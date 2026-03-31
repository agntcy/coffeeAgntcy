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

## Configuration

```bash
# Directory server address (default 0.0.0.0:8888)
export DIRECTORY_CLIENT_SERVER_ADDRESS=your-host:9999
```
