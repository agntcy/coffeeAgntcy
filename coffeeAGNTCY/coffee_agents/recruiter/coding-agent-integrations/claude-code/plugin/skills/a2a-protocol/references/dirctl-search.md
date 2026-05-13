# dirctl Search & Pull

## Search — find agents (returns CIDs)

```bash
# Search by skill
dirctl search --skill "natural_language_processing"

# Wildcard skill search (browse all)
dirctl search --skill "*"

# Search by domain
dirctl search --domain "*education*"

# Search by name
dirctl search --name "*coffee*"

# Combine filters
dirctl search --skill "AI" --domain "healthcare"
```

Output: a list of CIDs (Content Identifiers), e.g.:
```
Record CIDs found: [baeareicbymfgll4l3ngwbfkg7k5o2if5fajfu7beswvwe7r2yv3cmkvf5a ...]
```

## Pull — fetch a full OASF record by CID

```bash
dirctl pull <CID> --output json
```

Returns the full OASF record as JSON. Extract what you need with jq:

```bash
dirctl pull <CID> --output json | jq '{
  name: .name,
  description: .description,
  endpoint: (.modules[] | select(.name=="integration/a2a") | .data.card_data.url),
  skills: [(.modules[] | select(.name=="integration/a2a") | .data.card_data.skills[]? | .name)],
  protocolVersion: (.modules[] | select(.name=="integration/a2a") | .data.card_data.protocolVersion)
}'
```

## Verify — confirm a record's signature

```bash
# Local Sigstore verification (default, recommended)
dirctl verify <CID>

# Scripting-friendly output: empty stdout = trusted; error_message: ... = not trusted
dirctl verify <CID> --output raw

# Verify locally with an explicit public key
dirctl verify <CID> --key cosign.pub

# Verify with OIDC identity (Sigstore keyless)
dirctl verify <CID> \
  --oidc-issuer https://accounts.google.com \
  --oidc-subject publisher@example.com
```

**Two gotchas:**
- Exit code is **0 in both trusted and not-trusted cases** — it only signals that verification ran. Parse stdout to get the actual result.
- `--from-server` (cached verification) is often returned as `Unimplemented` by directory servers. Stick with local verification (default).

The `/recruit` flow uses `dirctl verify <CID> --output raw` and treats empty output as `signed ✓`, anything else as `unsigned ✗`.

You can also bias `search` toward trustworthy records up front:

```bash
# Only return records whose names are verified (DNS / namespace-owned)
dirctl search --skill "*" --verified

# Only return records with a trusted signature
dirctl search --skill "*" --trusted
```

## Configuration

```bash
# Directory server address (default 0.0.0.0:8888)
export DIRECTORY_CLIENT_SERVER_ADDRESS=your-host:9999
```
