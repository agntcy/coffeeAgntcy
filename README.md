# Coffee Agntcy

[![Release](https://img.shields.io/github/v/release/agntcy/repo-template?display_name=tag)](CHANGELOG.md)
[![Contributor-Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-fbab2c.svg)](CODE_OF_CONDUCT.md)

## About the Project

**Coffee Agntcy** is a real-world demo designed to help developers understand how components from Cisco’s **AGNTCY Internet of Agents** ecosystem fit together. It showcases modular, interoperable agent architectures that use flexible transport protocols and stateful LangGraph workflows to coordinate multi-agent behavior.

This project is ideal for developers building modern agent-based systems and looking to explore:

- How **SLIM** enables **broadcast** and **unicast** messaging
- How tools and transport can be reused across agent implementations (e.g., **SLIM**, **NATS**, **MCP**)
- How protocol-agnostic bridges and clients interconnect modular agents
- How to orchestrate agents using **LangGraph** for structured and stateful workflows
- How to integrate real-world data sources (e.g., weather services via **MCP**)
- How to extend or swap agents modularly using AGNTCY tooling

---

### Demos Included

We currently provide two demos, each targeting a different level of complexity and modularity:

- **Corto**:  
  A lightweight, ready-to-run demo that highlights core agent interactions using agent-to-agent (A2A) messaging over AGNTCY’s SLIM transport. Agents are orchestrated within a LangGraph, enabling simple but structured workflows.  
  👉 [View the Corto README](coffeeAGNTCY/coffee_agents/corto)

- **Lungo**:  
  A more advanced demo showcasing modular, extensible agentic components. Agents leveraging the A2A protocol communicate via configurable transports (default: SLIM), are structured as directed LangGraphs, and include real-world extensions—like a weather-aware farm that uses MCP to fetch live data.  
  👉 [View the Lungo README](coffeeAGNTCY/coffee_agents/lungo)

---

### Built With

- [AGNTCY SDK](https://github.com/agntcy/app-sdk)
- [SLIM](https://github.com/agntcy/slim)
- [A2A](https://github.com/a2aproject/a2a-python)
- [MCP](https://github.com/modelcontextprotocol/python-sdk)
- [LangGraph](https://github.com/langchain-ai/langgraph)

---

## Contributing

This is a developer-facing reference repo. If you're building agentic systems—or interested in shaping the future of distributed agents—we'd love your feedback, contributions, or collaboration. Contributions are what make the open source community such an amazing place to
learn, inspire, and create. For detailed contributing guidelines, please see
[CONTRIBUTING.md](CONTRIBUTING.md)  

--------

## License

Distributed under the Apache-2.0 License. See [LICENSE](LICENSE) for more
information.

## Contact

[cisco-outshift-ai-agents@cisco.com](mailto:cisco-outshift-ai-agents@cisco.com)

Project Link:
[https://github.com/cisco-outshift-ai-agents/coffeeAgntcy](https://github.com/cisco-outshift-ai-agents/coffeeAgntcy)


## Acknowledgements
- The [AGNTCY](https://github.com/agntcy) project.
