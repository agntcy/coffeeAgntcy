// a2a-send: CLI tool for sending messages to A2A agents using the a2a-go SDK.
//
// Inspired by openclaw-a2a-gateway's skill/scripts/a2a-send.mjs but written in Go
// using the official a2a-go SDK (github.com/a2aproject/a2a-go/v2).
//
// Supports: blocking send, non-blocking+polling, SSE streaming, multi-turn
// conversations (task-id/context-id), and automatic agent card discovery.
//
// Usage:
//
//	a2a-send --peer-url <URL> --message "Hello!"
//	a2a-send --peer-url <URL> --message "Follow up" --task-id <ID> --context-id <CTX>
//	a2a-send --peer-url <URL> --stream --message "Stream this"
//	a2a-send --peer-url <URL> --non-blocking --wait --message "Long task"
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"time"

	"github.com/a2aproject/a2a-go/v2/a2a"
	"github.com/a2aproject/a2a-go/v2/a2aclient"
	"github.com/a2aproject/a2a-go/v2/a2aclient/agentcard"
	"github.com/a2aproject/a2a-go/v2/a2acompat/a2av0"
)

const usage = `a2a-send — Send messages to A2A agents using the a2a-go SDK.

Usage:
  a2a-send --peer-url <URL> --message <TEXT> [options]

Options:
  --peer-url <url>         Agent base URL (required)
  --message <text>         Message text to send (required)
  --task-id <id>           Continue an existing task (multi-turn)
  --context-id <id>        Continue an existing context (multi-turn)
  --non-blocking           Send with returnImmediately=true, get task handle back
  --wait                   When --non-blocking, poll tasks/get until terminal state
  --stream                 Use streaming (SSE) to receive events
  --timeout-ms <ms>        Max wait time for --wait mode (default: 600000)
  --poll-ms <ms>           Poll interval for --wait mode (default: 1000)
  --verbose                Print debug info (agent card, transport negotiation)
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

	flag.Usage = func() {
		fmt.Fprint(os.Stderr, usage)
	}

	flag.Parse()
	return c
}

func main() {
	cfg := parseFlags()

	if cfg.peerURL == "" || cfg.message == "" {
		flag.Usage()
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

	// Discover agent card
	card, err := discoverCard(ctx, cfg.peerURL)
	if err != nil {
		// If agent card discovery fails, fall back to direct endpoint
		debug("Agent card not found at %s, using direct endpoint", cfg.peerURL)
		return runWithEndpoints(ctx, cfg)
	}

	printAgentInfo(card)

	if len(card.SupportedInterfaces) == 0 {
		// The agent card had no usable interfaces (common when v0.3 cards
		// have "url": "" or the field is missing). Default to v0.3 JSON-RPC
		// at the peer URL so the compat transport is selected.
		card.SupportedInterfaces = []*a2a.AgentInterface{
			{
				URL:             cfg.peerURL,
				ProtocolBinding: a2a.TransportProtocolJSONRPC,
				ProtocolVersion: a2av0.Version,
			},
		}
		debug("No supported interfaces listed, defaulting to v0.3 JSON-RPC at %s", cfg.peerURL)
	}

	// Also patch any interfaces that have an empty URL to use the peer URL.
	for _, iface := range card.SupportedInterfaces {
		if iface.URL == "" {
			iface.URL = cfg.peerURL
		}
	}

	// Create client from discovered card.
	// Register both v1.0 and v0.3 transports so the SDK can negotiate
	// the right wire format based on the agent card's protocolVersion.
	httpClient := &http.Client{Timeout: 5 * time.Minute}
	client, err := a2aclient.NewFromCard(ctx, card,
		// v1.0 transports
		a2aclient.WithJSONRPCTransport(httpClient),
		a2aclient.WithRESTTransport(httpClient),
		// v0.3 compat transport: converts ROLE_USER→"user", SendMessage→"message/send", etc.
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
	// When there's no agent card, assume v0.3 (most common for older servers).
	// Create a v0.3 interface so the compat transport is selected.
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
	// Use the v0 compat card parser so that v0.3 agent cards (with "url",
	// "protocolVersion", "preferredTransport" fields) are parsed correctly
	// into the v1.0 AgentCard structure with proper SupportedInterfaces.
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
			// Print what we have and return
			if r.Status.Message != nil {
				printMessageParts(r.Status.Message)
			}
			return nil
		}

		// Poll until terminal state
		return pollTask(ctx, client, r.ID, cfg)
	default:
		// Fallback: print as JSON
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
			// Non-text part: print as JSON
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
