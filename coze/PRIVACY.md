# Data handling / 数据处理

The tools send the input text, questions, candidate descriptions and optional image bytes
to the configured Valen service. This Coze integration uses
https://llm-proxy.openxxlab.com/v1 because coze.cn cannot reach the free endpoint. Its API
key stays in the plugin code on Coze's servers; it is not an input or output parameter.
An image URL is downloaded first, and its PNG, JPEG or WebP bytes are sent as a data URL.

The integration does not intentionally retain a separate copy or write application logs.
Coze retains workflow/plugin execution records according to its own settings and policies.
The API service has its own [data handling policy](https://valen-team.github.io/docs/valen/api/data-handling/).
Inputs can contain personal information, so the Coze publication statement must disclose
that inputs are transmitted to an external API.

工具会将输入文本、问题、候选描述和可选图片发送到配置的 Valen 服务。由于 coze.cn 无法
连接免费端点，此集成使用 https://llm-proxy.openxxlab.com/v1。API 密钥保存在扣子服务器的
插件代码内，不作为工具输入或输出。图片 URL 会先下载，PNG、JPEG、WebP 原始字节随后
作为 data URL 发送。

集成本身不另存数据，也不主动写应用日志；扣子按自身设置和政策保留工作流、插件运行记录。
API 服务的处理方式见上述数据政策。由于输入可能包含个人信息，发布时的个人信息声明
必须如实披露输入会传给外部 API。

The Coze declaration identifies names and contact details as information that users may
include in free-form support tickets. The tools do not request these as separate fields.
扣子的声明列出自由文本工单中可能包含的姓名和联系方式；工具不会单独要求填写这些字段。
