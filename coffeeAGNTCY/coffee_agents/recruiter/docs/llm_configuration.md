# LLM Configuration

Agent Recruiter uses [LiteLLM](https://docs.litellm.ai/) to manage LLM connections. With LiteLLM, you can seamlessly switch between different model providers using a unified configuration interface.

For a comprehensive list of supported providers, see the [official LiteLLM documentation](https://docs.litellm.ai/docs/providers).

> **Note:** The environment variable for specifying the model is always `LLM_MODEL`, regardless of the provider.

## Provider Examples

### OpenAI

```env
LLM_MODEL="openai/<model_of_choice>"
OPENAI_API_KEY=<your_openai_api_key>
```

### Azure OpenAI

```env
LLM_MODEL="azure/<your_deployment_name>"
AZURE_API_BASE=https://your-azure-resource.openai.azure.com/
AZURE_API_KEY=<your_azure_api_key>
AZURE_API_VERSION=<your_azure_api_version>
```

### GROQ

```env
LLM_MODEL="groq/<model_of_choice>"
GROQ_API_KEY=<your_groq_api_key>
```

### NVIDIA NIM

```env
LLM_MODEL="nvidia_nim/<model_of_choice>"
NVIDIA_NIM_API_KEY=<your_nvidia_api_key>
NVIDIA_NIM_API_BASE=<your_nvidia_nim_endpoint_url>
```

### LiteLLM Proxy

If you're using a LiteLLM proxy to route requests to various LLM providers:

```env
LLM_MODEL="azure/<your_deployment_name>"
LITELLM_PROXY_BASE_URL=<your_litellm_proxy_base_url>
LITELLM_PROXY_API_KEY=<your_litellm_proxy_api_key>
```

### Custom OAuth2 Application

If you're using an application secured with OAuth2 + refresh token that exposes an OpenAI endpoint:

```env
LLM_MODEL=oauth2/<your_llm_model_here>
OAUTH2_CLIENT_ID=<your_client_id>
OAUTH2_CLIENT_SECRET=<your_client_secret>
OAUTH_TOKEN_URL="https://your-auth-server.com/token"
OAUTH2_BASE_URL="https://your-openai-endpoint"
OAUTH2_APP_KEY=<your_app_key>  # optional
```
