![Screenshot](assets/coffee_agntcy.png)

[![Release](https://img.shields.io/github/v/release/agntcy/repo-template?display_name=tag)](CHANGELOG.md)
[![Contributor-Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-fbab2c.svg)](CODE_OF_CONDUCT.md)

## About the Project

**CoffeeAgntcy** is a reference implementation based on a fictitious coffee company to help developers understand how components in the **AGNTCY Internet of Agents** ecosystem can work together. It gives examples of the components of AGNTCY working together as a **Multi-agent System (MAS)**. 

This reference agentic application demonstrates how to:

- How **SLIM** enables **request-reply** , **unicast (fire & forget)** and **group communication** patterns.
- How tools and transports can be reused across agent implementations (e.g., **SLIM**, **NATS**, **MCP**)
- How protocol-agnostic bridges and clients interconnect modular agents
- How to orchestrate agents using **LangGraph** for structured and stateful workflows
- How to write **A2A** client and server agents
- How to integrate data sources (e.g., weather services via **MCP**)
- How to extend or swap agents modularly using AGNTCY tooling
- How to enable observability using **AGNTCY Observe SDK**
- How to enable identity using **AGNTCY Identity SDK**

---

### Setups Included

We currently provide two setups you can run to see how components from AGNTCY work together — one simple two-agent use case and the other a more complex MAS:

- **Corto**:  
  A two-agent, ready-to-run setup that highlights core agent interactions using agent-to-agent (A2A) messaging via configurable transports(default: AGNTCY's SLIM). Agents are orchestrated within a LangGraph. It also shows how to enable observability using Observe SDK.

  👉 [View the Corto README](coffeeAGNTCY/coffee_agents/corto)

- **Lungo**:  
  A more advanced setup that will evolve over time as we mature components. There are two setups: 1) pub/sub A2A over NATS as default transport, and 2) group communication over SLIM as default. Agents are structured as directed LangGraphs with A2A communication using configurable transports. It includes an MCP weather-aware farm that fetches live data, observability via the Observe SDK, identity, and a group communication pattern with specialized agents (farms, shipper, accountant) that collaborate to fulfill coffee orders.

  👉 [View the Lungo README](coffeeAGNTCY/coffee_agents/lungo)

---

### Built With

- [AGNTCY App SDK](https://github.com/agntcy/app-sdk) = v0.2.8
- [SLIM](https://github.com/agntcy/slim) = v0.4.0
- [A2A](https://github.com/a2aproject/a2a-python) = v0.3.0
- [MCP](https://github.com/modelcontextprotocol/python-sdk) >= v1.10.0
- [LangGraph](https://github.com/langchain-ai/langgraph) >= v0.4.1 
- [Observe SDK](https://github.com/agntcy/observe) = 1.0.18
- [Identity SDK](https://github.com/agntcy/identity) = 0.0.3

---

## Contributing

This is a developer-facing reference repo. If you're building agentic systems—or interested in shaping the future of distributed agents—we'd love your feedback, contributions, or collaboration. Contributions are what make the open-source community such an amazing place to learn, inspire, and create. For detailed contributing guidelines, please see [CONTRIBUTING.md](CONTRIBUTING.md).

---

## License

Distributed under the Apache-2.0 License. See [LICENSE](LICENSE) for more information.

## Acknowledgements

- The [AGNTCY](https://github.com/agntcy) project.
