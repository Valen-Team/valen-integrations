# Privacy and data handling

## Data used by the plugin

Valen processes only the text, questions, candidate choices or score levels, selected model ID, and optional image supplied to a tool invocation. Free-form content may contain personal or sensitive data if a workflow supplies it. The plugin does not request access to other workspace documents, conversations, contacts or databases.

## External services

The plugin sends the supplied evidence and questions to the endpoint configured in Dify provider credentials. The default hosted API is `https://api.valen-team.workers.dev`; the optional keyed hosted API is `https://llm-proxy.openxxlab.com`. An administrator may configure a trusted self-hosted Valen-compatible endpoint instead. Hosted service handling is described in [Valen API data handling](https://valen-team.github.io/docs/valen/api/data-handling/). A custom endpoint's operator determines its own processing and retention policies.

When an image is supplied, Dify's plugin SDK downloads its file URL before the image bytes are sent to the configured API. Image URLs may point to Dify-managed storage or to a remote file permitted by the instance. File downloads do not receive the Valen API key. Supported formats are PNG, JPEG and WebP.

## Credentials, storage and logs

The optional API key is held in Dify provider credentials and sent as an authorization header only to the configured API endpoint. The plugin does not embed credentials, create persistent storage, or add content logging. Image bytes are held in memory for the request. Dify may retain workflow inputs, outputs and errors in execution history, and the API or file-hosting service may retain data under its own policies.

## Operator control

Use only endpoints and images you trust. Configure Dify's network and file-access policies for the instance, and supply content only when you have permission to send it to the selected service. Review the endpoint's policy before processing personal or sensitive information. Request failures raise tool errors rather than fabricated judgments.

## Support

Contact: liuziyu77@sjtu.edu.cn. Source and issues: https://github.com/Valen-Team/valen-integrations.
