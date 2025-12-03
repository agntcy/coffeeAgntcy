# Changelog

## 0.0.59 (2025-11-24)
## 🚨 Breaking Changes
### 🔧 Migration from `cnoe-agent-utils` to `litellm`
We have replaced the internal LLM provider dependency `cnoe-agent-utils` with `litellm` to enable support for a wider range of LLM providers.

**Impact**
- This is a **breaking change**.
- Environment variables for LLM credentials must be updated in your environment to match the litellm convention for your preferred LLM provider. For a comprehensive list of supported providers, see the [official litellm documentation](https://docs.litellm.ai/docs/providers).
- LLM provider and model must be specified by the LLM_MODEL env variable. Examples:

#### **OpenAI**

```env
LLM_MODEL="openai/<model_of_choice>"
OPENAI_API_KEY=<your_openai_api_key>
```

#### **Azure OpenAI**

```env
LLM_MODEL="azure/<your_deployment_name>"
AZURE_API_BASE=https://your-azure-resource.openai.azure.com/
AZURE_API_KEY=<your_azure_api_key>
AZURE_API_VERSION=<your_azure_api_version>
```

#### **GROQ**

```env
LLM_MODEL="groq/<model_of_choice>"
GROQ_API_KEY=<your_groq_api_key>
```

---

## 0.0.1 (2025-05-30)
### Feat
- **Corto Demo**: Completed the implementation of the Corto demo, including:
  - **Frontend**:
    - Developed a React-based frontend for the Corto Exchange
  - **Backend**:
    - Implemented the Corto Exchange backend with modules for:
      - SLIM transport integration
      - A2A client
      - Graph operations
      - Main entry point
    - Developed the Corto Farm backend with:
      - SLIM transport integration
      - A2A agent execution and card management
      - Farm server
  - **Configuration**:
    - Docker support
    - Example environment file
    - Logging and server configuration
  - **Documentation**:
