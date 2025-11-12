# Privacy Policy for Markdown Text Chunker Plugin

## Data Collection and Usage

This plugin does **NOT** collect, store, or transmit any user data to external servers by default.

### What Data is Processed

1. **Input Text**: The markdown text you provide is processed locally within your Dify instance
2. **Configuration Parameters**: Plugin settings (heading level, metadata options, etc.) are stored locally
3. **Output Chunks**: Generated text chunks remain within your Dify instance

### Optional LLM Enhancement Feature

If you enable the **LLM-based heading enhancement** feature:

- Your markdown text will be sent to the LLM API endpoint you configure
- This feature is **opt-in** and disabled by default
- You have full control over which LLM service to use by configuring:
  - `llm_api_base`: Your chosen API endpoint
  - `llm_api_key`: Your API credentials
  - `llm_model`: The model to use

**Important**: When using LLM enhancement, your data is subject to the privacy policy of the LLM service provider you choose. Please review their privacy policy before enabling this feature.

### Data Storage

- No data is permanently stored by this plugin
- All processing is done in-memory during execution
- No logs or caches are maintained

### Third-Party Services

This plugin does not use any third-party services unless you explicitly enable LLM enhancement and configure an external API endpoint.

### Recommendations

1. **For sensitive documents**: Keep LLM enhancement disabled to ensure data stays within your infrastructure
2. **For public documents**: You may safely use LLM enhancement if needed
3. **Enterprise users**: Configure your own self-hosted LLM endpoints for full data control

## Updates to This Policy

This privacy policy may be updated to reflect changes in the plugin. Any significant changes will be documented in the plugin's changelog.

## Contact

For privacy-related questions or concerns, please open an issue in the plugin repository.

---

**Last Updated**: 2025-01-12
