// a2a-send: CLI tool for sending messages to A2A agents using the a2a-go SDK.
//
// Inspired by openclaw-a2a-gateway's skill/scripts/a2a-send.mjs but written in Go
// using the official a2a-go SDK (github.com/a2aproject/a2a-go/v2). The HTTP
// path supports blocking send, non-blocking+polling, SSE streaming, multi-turn
// conversations (task-id/context-id), and automatic agent card discovery. The
// SLIM path uses github.com/agntcy/slim-a2a-go for unary send over a running
// SLIM node. --transport auto picks SLIM when the agent card advertises a
// slim/slimrpc interface, otherwise HTTP.
//
// Usage:
//
//	a2a-send --peer-url <URL> --message "Hello!"
//	a2a-send --peer-url <URL> --message "Follow up" --task-id <ID> --context-id <CTX>
//	a2a-send --peer-url <URL> --stream --message "Stream this"
//	a2a-send --peer-url <URL> --non-blocking --wait --message "Long task"
//	a2a-send --peer-url <URL> --transport slim --message "Over SLIM"
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2acompat/a2av0"
	a2aslimrpcv0 "github.com/agntcy/slim-a2a-go/a2aslimrpc/v0"
	a2aslimrpcv1 "github.com/agntcy/slim-a2a-go/a2aslimrpc/v1"
	slim_bindings "github.com/agntcy/slim-bindings-go"
)

const usage = `a2a-send — Send messages to A2A agents using the a2a-go SDK.

Usage:
  a2a-send --peer-url <URL> --message <TEXT> [options]

Options:
  --peer-url <url>         Agent base URL (required for http transport;
                           optional for slim transport — used to discover the
                           remote SLIM name from the agent card)
  --message <text>         Message text to send (required)
  --task-id <id>           Continue an existing task (multi-turn)
  --context-id <id>        Continue an existing context (multi-turn)
  --non-blocking           Send with returnImmediately=true, get task handle back
  --wait                   When --non-blocking, poll tasks/get until terminal state
  --stream                 Use streaming (SSE) to receive events
  --timeout-ms <ms>        Max wait time for --wait mode (default: 600000)
  --poll-ms <ms>           Poll interval for --wait mode (default: 1000)
  --verbose                Print debug info (agent card, transport negotiation)

SLIM transport:
  --transport <auto|http|slim> Transport to use (default: auto). "auto" fetches
                              the agent card at --peer-url and picks SLIM if
                              it advertises a slim/slimrpc interface, else HTTP.
  --slim-endpoint <url>       SLIM node endpoint (default: http://127.0.0.1:46357)
  --slim-remote-name <name>   Three-segment SLIM name org/ns/name. If empty,
                              derived from --peer-url agent card's slimrpc/slim
                              interface (e.g. lungo/agents/brazil_coffee_farm).
  --slim-local-name <name>    Local SLIM identity (default: lungo/agents/a2a-send-cli)
  --slim-secret <secret>      Shared secret for SLIM identity (default: from
                              $SLIM_SHARED_SECRET; required — must match the
                              value the target agent was started with).
                              Uses insecure transport — not for prod.
  --a2a-version <auto|v0|v1>  A2A protocol version over SLIM (default: auto).
                              "auto" reads protocolVersion from the agent card
                              (cards with 0.x → v0; 1.x or unknown → v1).

  --help                   Show this help text

Examples:
  # Simple blocking send
  a2a-send --peer-url http://localhost:9999 --message "What is your name?"

  # Streaming mode
  a2a-send --peer-url http://localhost:9999 --stream --message "Tell me a story"

  # Non-blocking with polling
  a2a-send --peer-url http://localhost:9999 --non-blocking --wait --message "Analyze this data"

  # Multi-turn conversation
  a2a-send --peer-url http://localhost:9999 --message "Follow up" --task-id abc --context-id xyz
`

type config struct {
	peerURL     string
	message     string
	taskID      string
	contextID   string
	nonBlocking bool
	wait        bool
	stream      bool
	verbose     bool
	timeoutMs   int
	pollMs      int

	// SLIM transport options
	transport      string
	slimEndpoint   string
	slimRemoteName string
	slimLocalName  string
	slimSecret     string
	a2aVersion     string
}

func parseFlags() config {
	var c config
	flag.StringVar(&c.peerURL, "peer-url", "", "Agent base URL")
	flag.StringVar(&c.message, "message", "", "Message text to send")
	flag.StringVar(&c.taskID, "task-id", "", "Existing task ID for multi-turn")
	flag.StringVar(&c.contextID, "context-id", "", "Existing context ID for multi-turn")
	flag.BoolVar(&c.nonBlocking, "non-blocking", false, "Send with returnImmediately=true")
	flag.BoolVar(&c.wait, "wait", false, "Poll tasks/get until terminal state (requires --non-blocking)")
	flag.BoolVar(&c.stream, "stream", false, "Use streaming (SSE)")
	flag.BoolVar(&c.verbose, "verbose", false, "Print debug info (agent card, interfaces, etc.)")
	flag.IntVar(&c.timeoutMs, "timeout-ms", 600000, "Max wait time in ms for --wait mode")
	flag.IntVar(&c.pollMs, "poll-ms", 1000, "Poll interval in ms for --wait mode")

	flag.StringVar(&c.transport, "transport", "auto", "Transport to use: auto, http, or slim. \"auto\" inspects the agent card — if it advertises a slim/slimrpc interface, SLIM is used; otherwise HTTP.")
	flag.StringVar(&c.slimEndpoint, "slim-endpoint", "http://127.0.0.1:46357", "SLIM node endpoint")
	flag.StringVar(&c.slimRemoteName, "slim-remote-name", "", "Remote SLIM name (org/ns/name); auto-derived from agent card if empty")
	flag.StringVar(&c.slimLocalName, "slim-local-name", "lungo/agents/a2a-send-cli", "Local SLIM identity (org/ns/name)")
	flag.StringVar(&c.slimSecret, "slim-secret", os.Getenv("SLIM_SHARED_SECRET"), "Shared secret for SLIM identity (default: $SLIM_SHARED_SECRET)")
	flag.StringVar(&c.a2aVersion, "a2a-version", "auto", "A2A protocol version over SLIM: auto, v0, or v1 (auto = derive from agent card protocolVersion, defaults to v0 if unknown)")

	flag.Usage = func() {
		fmt.Fprint(os.Stderr, usage)
	}

	flag.Parse()
	return c
}

func main() {
	cfg := parseFlags()

	if cfg.message == "" {
		flag.Usage()
		os.Exit(1)
	}
	switch cfg.transport {
	case "http":
		if cfg.peerURL == "" {
			fmt.Fprintln(os.Stderr, "error: --peer-url is required for http transport")
			flag.Usage()
			os.Exit(1)
		}
	case "slim":
		if cfg.slimRemoteName == "" && cfg.peerURL == "" {
			fmt.Fprintln(os.Stderr, "error: slim transport needs --slim-remote-name or --peer-url (to derive name from agent card)")
			flag.Usage()
			os.Exit(1)
		}
		if cfg.a2aVersion != "auto" && cfg.a2aVersion != "v0" && cfg.a2aVersion != "v1" {
			fmt.Fprintf(os.Stderr, "error: --a2a-version must be auto, v0, or v1 (got %q)\n", cfg.a2aVersion)
			os.Exit(1)
		}
	case "auto":
		if cfg.peerURL == "" {
			fmt.Fprintln(os.Stderr, "error: --peer-url is required for --transport auto (used to fetch the agent card)")
			flag.Usage()
			os.Exit(1)
		}
	default:
		fmt.Fprintf(os.Stderr, "error: unknown --transport %q (expected auto, http, or slim)\n", cfg.transport)
		os.Exit(1)
	}

	verbose = cfg.verbose

	if err := run(cfg); err != nil {
		printError(err)
		os.Exit(1)
	}
}

func run(cfg config) error {
	ctx := context.Background()

	if cfg.transport == "auto" {
		picked, reason := pickTransportFromCard(ctx, cfg.peerURL)
		debug("Transport auto-detect: chose %s (%s)", picked, reason)
		cfg.transport = picked
	}

	if cfg.transport == "slim" {
		if cfg.stream {
			return fmt.Errorf("--stream is not supported over SLIM; use --transport http")
		}
		if cfg.nonBlocking && cfg.wait {
			return fmt.Errorf("--non-blocking --wait polling is not supported over SLIM")
		}
		return runSlim(ctx, cfg)
	}

	return runHTTP(ctx, cfg)
}

// pickTransportFromCard returns "slim" if the agent card advertises any
// slim/slimrpc interface, else "http". Discovery failures fall back to HTTP.
func pickTransportFromCard(ctx context.Context, peerURL string) (transport string, reason string) {
	if peerURL == "" {
		return "http", "no --peer-url provided"
	}
	card, err := discoverCard(ctx, peerURL)
	if err != nil {
		return "http", fmt.Sprintf("agent card discovery failed: %v", err)
	}
	for _, iface := range card.SupportedInterfaces {
		binding := strings.ToLower(string(iface.ProtocolBinding))
		if binding == "slim" || binding == "slimrpc" {
			return "slim", fmt.Sprintf("agent card advertises %s interface", binding)
		}
	}
	return "http", "no slim/slimrpc interface in agent card"
}

func runHTTP(ctx context.Context, cfg config) error {
	card, err := discoverCard(ctx, cfg.peerURL)
	if err != nil {
		debug("Agent card not found at %s, using direct endpoint", cfg.peerURL)
		return runWithEndpoints(ctx, cfg)
	}

	printAgentInfo(card)

	if len(card.SupportedInterfaces) == 0 {
		// v0.3 cards sometimes omit interfaces; default to JSON-RPC at the peer URL.
		card.SupportedInterfaces = []*a2a.AgentInterface{
			{
				URL:             cfg.peerURL,
				ProtocolBinding: a2a.TransportProtocolJSONRPC,
				ProtocolVersion: a2av0.Version,
			},
		}
		debug("No supported interfaces listed, defaulting to v0.3 JSON-RPC at %s", cfg.peerURL)
	}

	// Patch empty URLs and normalize non-canonical binding names (e.g. "jsonrpc"
	// → TransportProtocolJSONRPC) so the SDK's case-sensitive matcher accepts them.
	// Unknown bindings (slim, slimrpc, nats) are left untouched — the SDK skips them.
	for _, iface := range card.SupportedInterfaces {
		if iface.URL == "" {
			iface.URL = cfg.peerURL
		}
		switch strings.ToLower(string(iface.ProtocolBinding)) {
		case "jsonrpc":
			iface.ProtocolBinding = a2a.TransportProtocolJSONRPC
		case "grpc":
			iface.ProtocolBinding = a2a.TransportProtocolGRPC
		case "http+json", "rest", "httpjson":
			iface.ProtocolBinding = a2a.TransportProtocolHTTPJSON
		}
	}

	// Register both v1.0 and v0.3 transports so the SDK can negotiate the wire
	// format based on the card's protocolVersion.
	httpClient := &http.Client{Timeout: 5 * time.Minute}
	client, err := a2aclient.NewFromCard(ctx, card,
		a2aclient.WithJSONRPCTransport(httpClient),
		a2aclient.WithRESTTransport(httpClient),
		a2aclient.WithCompatTransport(
			a2av0.Version,
			a2a.TransportProtocolJSONRPC,
			a2av0.NewJSONRPCTransportFactory(a2av0.JSONRPCTransportConfig{Client: httpClient}),
		),
	)
	if err != nil {
		return fmt.Errorf("failed to create A2A client: %w", err)
	}
	defer client.Destroy()

	return executeRequest(ctx, client, cfg)
}

func runWithEndpoints(ctx context.Context, cfg config) error {
	httpClient := &http.Client{Timeout: 5 * time.Minute}
	// No agent card available — assume v0.3 JSON-RPC (most common for older servers).
	endpoints := []*a2a.AgentInterface{
		{
			URL:             cfg.peerURL,
			ProtocolBinding: a2a.TransportProtocolJSONRPC,
			ProtocolVersion: a2av0.Version,
		},
	}
	client, err := a2aclient.NewFromEndpoints(ctx, endpoints,
		a2aclient.WithCompatTransport(
			a2av0.Version,
			a2a.TransportProtocolJSONRPC,
			a2av0.NewJSONRPCTransportFactory(a2av0.JSONRPCTransportConfig{Client: httpClient}),
		),
	)
	if err != nil {
		return fmt.Errorf("failed to create A2A client from endpoint: %w", err)
	}
	defer client.Destroy()

	return executeRequest(ctx, client, cfg)
}

func discoverCard(ctx context.Context, peerURL string) (*a2a.AgentCard, error) {
	// Use the v0 compat parser so v0.3 cards (with "url", "protocolVersion",
	// "preferredTransport" fields) are normalized into v2 AgentCard structure.
	resolver := &agentcard.Resolver{
		Client:     &http.Client{Timeout: 10 * time.Second},
		CardParser: a2av0.NewAgentCardParser(),
	}
	return resolver.Resolve(ctx, peerURL)
}

func printAgentInfo(card *a2a.AgentCard) {
	if card.Name != "" {
		debug("Agent: %s", card.Name)
	}
	if card.Version != "" {
		debug("Version: %s", card.Version)
	}
	if card.Description != "" {
		debug("Description: %s", card.Description)
	}
	for _, iface := range card.SupportedInterfaces {
		debug("Interface: %s @ %s (v%s)", iface.ProtocolBinding, iface.URL, iface.ProtocolVersion)
	}
}

func executeRequest(ctx context.Context, client *a2aclient.Client, cfg config) error {
	if cfg.stream {
		return doStream(ctx, client, cfg)
	}
	return doSend(ctx, client, cfg)
}

// doSend handles blocking and non-blocking (with optional polling) sends.
func doSend(ctx context.Context, client *a2aclient.Client, cfg config) error {
	msg := buildMessage(cfg)
	req := &a2a.SendMessageRequest{
		Message: msg,
	}

	if cfg.nonBlocking {
		req.Config = &a2a.SendMessageConfig{
			ReturnImmediately: true,
		}
	}

	result, err := client.SendMessage(ctx, req)
	if err != nil {
		return fmt.Errorf("SendMessage failed: %w", err)
	}

	switch r := result.(type) {
	case *a2a.Message:
		printMessageParts(r)
	case *a2a.Task:
		printTaskHandle(r)

		if !cfg.nonBlocking || !cfg.wait {
			if r.Status.Message != nil {
				printMessageParts(r.Status.Message)
			}
			return nil
		}

		return pollTask(ctx, client, r.ID, cfg)
	default:
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		enc.Encode(result)
	}

	return nil
}

// doStream handles SSE streaming sends.
func doStream(ctx context.Context, client *a2aclient.Client, cfg config) error {
	msg := buildMessage(cfg)
	req := &a2a.SendMessageRequest{
		Message: msg,
	}

	fmt.Fprintln(os.Stderr, "[stream] connecting...")

	for event, err := range client.SendStreamingMessage(ctx, req) {
		if err != nil {
			return fmt.Errorf("streaming error: %w", err)
		}

		switch e := event.(type) {
		case *a2a.Task:
			state := e.Status.State
			text := extractTextFromMessage(e.Status.Message)
			if state == a2a.TaskStateWorking {
				ts := ""
				if e.Status.Timestamp != nil {
					ts = e.Status.Timestamp.Format(time.RFC3339)
				}
				fmt.Fprintf(os.Stderr, "[stream] working... (%s)\n", ts)
			} else if text != "" {
				fmt.Fprintf(os.Stderr, "[stream] %s: ", state)
				fmt.Println(text)
			} else {
				b, _ := json.Marshal(e.Status)
				fmt.Fprintf(os.Stderr, "[stream] %s: %s\n", state, string(b))
			}

		case *a2a.TaskStatusUpdateEvent:
			state := e.Status.State
			text := extractTextFromMessage(e.Status.Message)
			if text != "" {
				fmt.Fprintf(os.Stderr, "[stream] status-update: %s - %s\n", state, text)
			} else {
				fmt.Fprintf(os.Stderr, "[stream] status-update: %s\n", state)
			}

		case *a2a.Message:
			printMessageParts(e)

		case *a2a.TaskArtifactUpdateEvent:
			fmt.Fprintf(os.Stderr, "[stream] artifact-update: task=%s\n", e.TaskID)
			for _, part := range e.Artifact.Parts {
				text := part.Text()
				if text != "" {
					fmt.Println(text)
				}
			}

		default:
			b, _ := json.Marshal(event)
			fmt.Fprintf(os.Stderr, "[stream] unknown event: %s\n", string(b))
		}
	}

	fmt.Fprintln(os.Stderr, "[stream] done")
	return nil
}

// pollTask polls for task completion in non-blocking+wait mode.
func pollTask(ctx context.Context, client *a2aclient.Client, taskID a2a.TaskID, cfg config) error {
	timeout := time.Duration(cfg.timeoutMs) * time.Millisecond
	pollInterval := time.Duration(cfg.pollMs) * time.Millisecond
	deadline := time.Now().Add(timeout)

	historyLen := 20

	for {
		task, err := client.GetTask(ctx, &a2a.GetTaskRequest{
			ID:            taskID,
			HistoryLength: &historyLen,
		})
		if err != nil {
			return fmt.Errorf("GetTask failed: %w", err)
		}

		state := task.Status.State
		if state.Terminal() {
			text := extractTextFromMessage(task.Status.Message)
			if text != "" {
				fmt.Println(text)
			} else {
				enc := json.NewEncoder(os.Stdout)
				enc.SetIndent("", "  ")
				enc.Encode(task)
			}
			return nil
		}

		if time.Now().After(deadline) {
			return fmt.Errorf("timeout waiting for task %s after %dms", taskID, cfg.timeoutMs)
		}

		time.Sleep(pollInterval)
	}
}

func buildMessage(cfg config) *a2a.Message {
	msg := a2a.NewMessage(a2a.MessageRoleUser, a2a.NewTextPart(cfg.message))

	if cfg.taskID != "" {
		msg.TaskID = a2a.TaskID(cfg.taskID)
	}
	if cfg.contextID != "" {
		msg.ContextID = cfg.contextID
	}

	return msg
}

func printMessageParts(msg *a2a.Message) {
	if msg == nil {
		return
	}
	for _, part := range msg.Parts {
		text := part.Text()
		if text != "" {
			fmt.Println(text)
		} else {
			b, _ := json.Marshal(part)
			fmt.Println(string(b))
		}
	}
}

func printTaskHandle(task *a2a.Task) {
	contextID := task.ContextID
	if contextID == "" {
		contextID = "-"
	}
	fmt.Fprintf(os.Stderr, "[task] id=%s contextId=%s\n", task.ID, contextID)
}

func extractTextFromMessage(msg *a2a.Message) string {
	if msg == nil {
		return ""
	}
	for _, part := range msg.Parts {
		text := part.Text()
		if text != "" {
			return text
		}
	}
	return ""
}

func printError(err error) {
	errObj := map[string]string{
		"error": err.Error(),
	}
	b, _ := json.Marshal(errObj)
	fmt.Fprintln(os.Stderr, string(b))
}

// verbose is set from cfg.verbose at startup; used by debug().
var verbose bool

func debug(format string, args ...any) {
	if verbose {
		fmt.Fprintf(os.Stderr, "[debug] "+format+"\n", args...)
	}
}

// ---------------------------------------------------------------------------
// SLIM transport
// ---------------------------------------------------------------------------

// runSlim sends a single A2A message over SLIM RPC using slim-a2a-go.
func runSlim(ctx context.Context, cfg config) error {
	if cfg.slimSecret == "" {
		return fmt.Errorf("SLIM transport requires a shared secret: export SLIM_SHARED_SECRET in your shell (it must match the value the target agent was started with) or pass --slim-secret")
	}
	remoteSpec := cfg.slimRemoteName
	detectedVersion := "" // protocolVersion from the agent card (e.g. "0.3.0", "1.0")
	// Fetch the card if we need it for name derivation or version auto-detect.
	if remoteSpec == "" || cfg.a2aVersion == "auto" {
		if cfg.peerURL == "" {
			if remoteSpec == "" {
				return fmt.Errorf("--slim-remote-name is required when --peer-url is not provided")
			}
			// Explicit name but no peer URL — proceed with default version.
		} else {
			derivedName, derivedVersion, err := resolveSlimRemoteFromCard(ctx, cfg.peerURL)
			if err != nil {
				if remoteSpec == "" {
					return fmt.Errorf("could not derive --slim-remote-name from agent card at %s: %w", cfg.peerURL, err)
				}
				debug("Agent-card lookup for version detection failed (%v); using --a2a-version default", err)
			} else {
				if remoteSpec == "" {
					debug("Derived SLIM remote name from agent card: %s", derivedName)
					remoteSpec = derivedName
				}
				detectedVersion = derivedVersion
				debug("Agent card protocolVersion: %q", derivedVersion)
			}
		}
	}

	resolvedVersion := cfg.a2aVersion
	if resolvedVersion == "auto" {
		resolvedVersion = pickA2AVersion(detectedVersion)
		debug("Auto-selected A2A version: %s (from card protocolVersion %q)", resolvedVersion, detectedVersion)
	}

	remoteName, err := parseSlimName(remoteSpec)
	if err != nil {
		return fmt.Errorf("invalid --slim-remote-name %q: %w", remoteSpec, err)
	}
	localName, err := parseSlimName(cfg.slimLocalName)
	if err != nil {
		return fmt.Errorf("invalid --slim-local-name %q: %w", cfg.slimLocalName, err)
	}

	debug("SLIM endpoint:    %s", cfg.slimEndpoint)
	debug("SLIM local name:  %s", cfg.slimLocalName)
	debug("SLIM remote name: %s", remoteSpec)
	debug("A2A version:      %s", resolvedVersion)

	slim_bindings.InitializeWithDefaults()
	svc := slim_bindings.GetGlobalService()

	app, err := svc.CreateAppWithSecret(localName, cfg.slimSecret)
	if err != nil {
		return fmt.Errorf("create app: %w", err)
	}

	connID, err := svc.Connect(slim_bindings.NewInsecureClientConfig(cfg.slimEndpoint))
	if err != nil {
		return fmt.Errorf("connect to SLIM endpoint %s: %w", cfg.slimEndpoint, err)
	}

	if err := app.Subscribe(localName, &connID); err != nil {
		return fmt.Errorf("subscribe: %w", err)
	}

	channel := slim_bindings.ChannelNewWithConnection(app, remoteName, &connID)
	defer channel.Destroy()

	req := &a2a.SendMessageRequest{Message: buildMessage(cfg)}

	var result a2a.SendMessageResult
	if resolvedVersion == "v0" {
		t := a2aslimrpcv0.NewTransport(channel)
		defer t.Destroy() //nolint:errcheck
		result, err = t.SendMessage(ctx, nil, req)
	} else {
		t := a2aslimrpcv1.NewTransport(channel)
		defer t.Destroy() //nolint:errcheck
		result, err = t.SendMessage(ctx, nil, req)
	}
	if err != nil {
		// Code=15 from SLIM is almost always a shared-secret mismatch.
		msg := err.Error()
		if strings.Contains(msg, "Session handshake failed") || strings.Contains(msg, "Code=15") {
			return fmt.Errorf("SendMessage over SLIM failed: %w\nhint: SLIM_SHARED_SECRET must match the value the target agent was started with", err)
		}
		return fmt.Errorf("SendMessage over SLIM failed: %w", err)
	}

	switch r := result.(type) {
	case *a2a.Message:
		printMessageParts(r)
	case *a2a.Task:
		printTaskHandle(r)
		if r.Status.Message != nil {
			printMessageParts(r.Status.Message)
		}
		for _, artifact := range r.Artifacts {
			for _, part := range artifact.Parts {
				if text := part.Text(); text != "" {
					fmt.Println(text)
				}
			}
		}
	default:
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		enc.Encode(result)
	}

	return nil
}

// resolveSlimRemoteFromCard returns (slimName, protocolVersion) for the first
// slim/slimrpc interface in the agent card at peerURL. slimName is the
// org/ns/name path from the slim:// URL.
func resolveSlimRemoteFromCard(ctx context.Context, peerURL string) (name string, protocolVersion string, err error) {
	if peerURL == "" {
		return "", "", fmt.Errorf("no --peer-url provided")
	}
	card, err := discoverCard(ctx, peerURL)
	if err != nil {
		return "", "", fmt.Errorf("agent card discovery failed: %w", err)
	}

	// Top-level "protocolVersion" on v0.3 cards is not surfaced by the v2
	// AgentCard struct, so fetch the raw JSON to read it directly.
	protocolVersion = fetchRawProtocolVersion(ctx, peerURL)

	for _, iface := range card.SupportedInterfaces {
		binding := strings.ToLower(string(iface.ProtocolBinding))
		if binding != "slim" && binding != "slimrpc" {
			continue
		}
		n, err := extractSlimNameFromURL(iface.URL)
		if err != nil {
			debug("skipping %s interface with unparseable URL %q: %v", binding, iface.URL, err)
			continue
		}
		v := string(iface.ProtocolVersion)
		if v == "" {
			v = protocolVersion
		}
		return n, v, nil
	}

	return "", protocolVersion, fmt.Errorf("no slim/slimrpc interface found in agent card; supported interfaces: %s",
		summarizeInterfaces(card.SupportedInterfaces))
}

// pickA2AVersion maps an agent-card protocolVersion to "v0" or "v1".
// "1.x" → v1; everything else (including empty) → v0. Default-to-v0 matches
// this repo's agents, which all run agntcy-app-sdk 0.3.x.
func pickA2AVersion(cardVersion string) string {
	if strings.HasPrefix(strings.TrimSpace(cardVersion), "1.") {
		return "v1"
	}
	return "v0"
}

// fetchRawProtocolVersion pulls the top-level "protocolVersion" field directly
// from the agent card JSON. The v2 AgentCard struct drops this field, but
// agntcy-app-sdk v0.3 cards still advertise it (e.g. "0.3.0").
func fetchRawProtocolVersion(ctx context.Context, peerURL string) string {
	cardURL := strings.TrimRight(peerURL, "/") + "/.well-known/agent-card.json"
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, cardURL, nil)
	if err != nil {
		return ""
	}
	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return ""
	}
	defer resp.Body.Close()
	var raw struct {
		ProtocolVersion string `json:"protocolVersion"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&raw); err != nil {
		return ""
	}
	return raw.ProtocolVersion
}

func extractSlimNameFromURL(rawURL string) (string, error) {
	if rawURL == "" {
		return "", fmt.Errorf("empty URL")
	}
	u, err := url.Parse(rawURL)
	if err != nil {
		return "", err
	}
	path := strings.Trim(u.Path, "/")
	if path == "" {
		return "", fmt.Errorf("URL %q has no path segments to use as SLIM name", rawURL)
	}
	parts := strings.Split(path, "/")
	if len(parts) != 3 {
		return "", fmt.Errorf("expected 3 path segments (org/ns/name), got %d in %q", len(parts), rawURL)
	}
	return path, nil
}

func summarizeInterfaces(ifaces []*a2a.AgentInterface) string {
	if len(ifaces) == 0 {
		return "(none)"
	}
	parts := make([]string, 0, len(ifaces))
	for _, i := range ifaces {
		parts = append(parts, fmt.Sprintf("%s@%s", i.ProtocolBinding, i.URL))
	}
	return strings.Join(parts, ", ")
}

// parseSlimName splits "org/ns/name" into a *slim_bindings.Name.
func parseSlimName(s string) (*slim_bindings.Name, error) {
	parts := strings.Split(strings.Trim(s, "/"), "/")
	if len(parts) != 3 || parts[0] == "" || parts[1] == "" || parts[2] == "" {
		return nil, fmt.Errorf("expected org/ns/name, got %q", s)
	}
	return slim_bindings.NewName(parts[0], parts[1], parts[2]), nil
}
