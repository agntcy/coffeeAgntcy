# Discovery, Routing & Composition

How the system finds, selects, and composes the right agent or capability *before or at the edge of execution*. Patterns
here turn a vague ask into directory lookup, ranked shortlists, or versioned services-not the day-to-day saga itself.

**Routing** (Directory-Based Dispatch, Recruiter) picks callees from intent and catalog metadata with an explainable
rationale. **Composition** (Composable Agent Service) packages agents as discoverable, versioned products other
workflows reuse instead of forking.

**Patterns:** Recruiter, Directory-Based Dispatch, Composable Agent Service

**Not to be confused with Orchestration & Control Flow** - failover, retries, and saga recovery after a step fails belong
there. Discovery focuses on *initial selection and capability assembly*, often using a directory or registry as the map
of who can do what.
