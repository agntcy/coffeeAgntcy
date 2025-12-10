# Route Evaluation System - Steps

## Phase 1 - Setup

 **Define ideal route patterns and store in Redis VL** - Manually create templates for default prompt flows with expected steps, tools, and latency ranges. Index these patterns with embeddings to find similar routes via vector search

**Extract traces from Clickhouse and convert traces to route objects** - Pull OTEL spans for completed requests and parse spans into normalized format: nodes visited, tools called, timing, decisions made

## Phase 2 - Eval
**Find matching expected route** - For each trace's query, search RedisVL to find most similar ideal pattern

**Compare actual vs expected** - Check if nodes match, tools match, if there are extra/missing steps, latency differences

**Calculate scores** - Generate accuracy score (did it follow the right path?), efficiency score (extra steps?), identify specific deviations

## Phase 3 - Visualization
**Write results to ClickHouse** - Store evaluation metrics in the results table

**Visualize in Grafana** - Create dashboards that query ClickHouse for trends (accuracy over time, common deviations, latency overhead by pattern)


### Why RedisVL for Route Evaluation

RedisVL enables semantic matching of actual traces to ideal route patterns through vector similarity search, meaning queries like "Count of beans in Colombia" and "Tell me how many beans in Colombia" automatically map to the same "brazil_inventory" pattern without brittle keyword matching. This allows the system to evaluate traces against the most similar ideal pattern even when query wording varies, and enables automatic discovery of new patterns by clustering similar historical traces. Alternative approaches using SQL keyword matching would require maintaining massive synonym lists, break with natural language variations, and can't handle the semantic similarity needed to generalize across diverse user queries.

