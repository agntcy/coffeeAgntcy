# Gateway Pattern Agents

The Gateway Pattern enables autonomous agents to compose multi-platform
workflows through a single MCP gateway. The following agents demonstrate how
upstream consumers leverage the gateway to accomplish tasks spanning multiple
platform servers.

## NOC Copilot Agent

**Role**: Autonomous triage and incident management for network operations.

**Workflow**: Monitors correlation engine alerts continuously. When triggered,
auto-pulls CMDB context to identify affected devices and services, checks the
ITSM platform for open changes or related incidents, runs diagnostics through
the monitoring platform, drafts an incident with full root cause analysis, and
escalates only when human approval is needed for remediation. Transforms L1 NOC
from reactive to supervisory.

**Gateway interactions**:

- Correlation Engine: subscribe to alerts, query correlated events
- CMDB Server: resolve device context, map dependencies
- ITSM Server: check open changes, create incidents, update resolution
- Monitoring Server: pull device health, interface diagnostics
- Configuration Server: apply remediation (requires HITL approval)
- Chat Server: post status updates to operations channel

## Security Orchestration Agent

**Role**: Automated threat detection, correlation, and containment across
security and network platforms.

**Workflow**: Subscribes to security platform events, correlates lateral movement
indicators across security and network monitoring tools, calculates blast radius
via the CMDB, quarantines compromised endpoints through access control, blocks
command-and-control domains on the firewall, creates a P1 incident, and posts a
summary to the security operations channel. Human approval gates protect
destructive containment actions.

**Gateway interactions**:

- Security Server: detect threats, retrieve indicators of compromise
- Monitoring Server: correlate network anomalies with security events
- CMDB Server: map blast radius, identify affected assets
- Access Control Server: quarantine endpoints (requires HITL approval)
- Firewall Server: block domains (requires HITL approval)
- ITSM Server: create P1 incident
- Chat Server: post summary to SecOps channel

## Change Validation Agent

**Role**: Automated pre/post change verification across all platforms.

**Workflow**: Before a maintenance window, captures baseline snapshots of health
scores, telemetry, and configuration state across every platform via the
gateway. After the change, re-runs the same queries, diffs the results, and
flags regressions. Writes before/after evidence to the ITSM change record.

**Gateway interactions**:

- All platform servers: snapshot health, telemetry, configuration state
- Correlation Engine: capture risk score baseline, compare post-change
- ITSM Server: attach before/after evidence to change record
- Chat Server: notify operations of validation results

## Capacity Planning Agent

**Role**: Proactive infrastructure capacity analysis and forecasting.

**Workflow**: Periodically queries monitoring platforms for device utilization,
wireless density, path capacity, and rack space. Feeds historical telemetry
through the correlation engine's prediction capabilities. Generates quarterly
reports and creates proactive change requests before capacity thresholds are
breached.

**Gateway interactions**:

- Monitoring Server: device utilization, interface capacity
- Observability Server: wireless density, path metrics
- CMDB Server: rack space, power budgets
- Correlation Engine: trend analysis, threshold prediction
- ITSM Server: create proactive change requests

## Compliance Auditor Agent

**Role**: Scheduled compliance evidence collection and violation detection.

**Workflow**: Runs on a defined schedule, systematically queries every platform
for compliance evidence (certificate expiry, endpoint posture, configuration
drift, access policy consistency, vulnerability exposure). Compiles findings,
flags violations, and compares against the last audit run. This agent has
read-only TBAC permissions across all servers.

**Gateway interactions**:

- All platform servers: read-only queries for compliance evidence
- Security Server: certificate expiry, vulnerability exposure
- Access Control Server: endpoint posture, policy consistency
- Configuration Server: configuration drift detection
- ITSM Server: file compliance reports, flag violations

## Multi-Vendor Orchestration Agent

**Role**: Cross-vendor agent coordination using AGNTCY discovery.

**Workflow**: Discovers the gateway's MCP servers via the AGNTCY Agent Directory
alongside MCP servers from other vendors (cloud providers, third-party security,
SaaS platforms). Queries the gateway for campus and WAN telemetry while
simultaneously querying external MCP servers for cloud-side metrics. Correlates
across all sources. The gateway becomes one piece of a larger agent ecosystem,
demonstrating AGNTCY's Internet of Agents vision.

**Gateway interactions**:

- Agent Directory: discover gateway and external vendor MCP servers
- All gateway platform servers: campus/WAN queries
- External MCP servers: cloud/SaaS queries (outside gateway)
- Correlation Engine: cross-vendor event fusion

## Executive Briefing Agent

**Role**: Automated daily operational summary for leadership.

**Workflow**: Generates a daily digest by querying the correlation engine for
overnight risk scores, pulling top incidents from the ITSM platform, grabbing
network health from monitoring, and security posture from the security platform.
Synthesizes into a concise summary with key metrics and posts to a leadership
communication channel.

**Gateway interactions**:

- Correlation Engine: overnight risk scores, active correlations
- ITSM Server: top incidents, open changes
- Monitoring Server: network health summary
- Security Server: security posture overview
- Chat Server: post daily briefing to leadership channel
