# Identity Integration Documentation

## Retrieving API Keys from Identity SaaS

Please refer to https://identity-docs.staging.outshift.ai/docs/intro for more information on Identity SaaS and its features.

To integrate with Identity SaaS, follow these steps to retrieve API keys and configure environment variables:

1. **Retrieve API Keys**:
    - Contact the AGNTCY Identity team for access to Identity SaaS.
    - Use the Identity SaaS UI to generate API keys for your agents (e.g., Vietnam and Colombia).

2. **Configure Environment Variables**:
    - Set the retrieved API keys and configuration values as environment variables:
        - `IDENTITY_VIETNAM_AGENT_SERVICE_API_KEY`: Vietnam agent API key.
        - `IDENTITY_COLOMBIA_AGENT_SERVICE_API_KEY`: Colombia agent API key.
        - `IDENTITY_API_KEY`: General Identity SaaS API key.
        - `IDENTITY_API_SERVER_URL`: Identity API endpoint.
        - `VIETNAM_FARM_AGENT_URL` and `COLOMBIA_FARM_AGENT_URL`: URLs for the farm agents' well-known agent cards.