# Dify Valen 插件

[English](README.md) · [统一协议](../SPEC.md)

把一条客服工单变成明确的下一步：退款复核、普通支持，或人工处理。Valen 读取文本或图片，返回答案与概率；你在工作流里决定阈值和动作。随包提供的示例已连接好正常分流与请求失败出口，便于先试用，再接入自己的业务。

## 安装

需要 **Dify 1.18.0+**。打开 **集成（Integrations）→ 安装（Install）→ GitHub**（旧版界面为「插件 → 安装插件」），输入：

```text
https://github.com/Valen-Team/valen-integrations
```

选择版本 **dify-v0.1.0** 和文件 **valen-0.1.0.difypkg**，完成安装。也可以在[发布页](https://github.com/Valen-Team/valen-integrations/releases/tag/dify-v0.1.0)下载插件与示例，再选择「本地插件文件」安装。

这是通过 GitHub 分发的社区插件，Dify 市场审核另行进行。安装包未签名，需要实例允许安装未签名社区插件；强制要求市场签名的实例请先联系管理员。[管理员配置与源码构建](RELEASING.md)。

授权时使用默认地址 `https://api.valen-team.workers.dev`，密钥留空；也可填写带密钥的服务或
自托管地址。保存时检查 `/v1/models`。密钥保存在 Dify 的供应商凭据中。模型可自由填写，
默认为 `valen-2b`。

## 使用

- **Yes/No**：输入文本和具体陈述，返回 `probability`、`branch`、`model`。默认概率 ≥0.7
  进入 `yes`，≤0.3 进入 `no`，其余进入 `unsure`。
- **Choice**：选项每行一个，写成 `value` 或 `value: description`；返回 `choice`、
  `confidence`、`probabilities`、`branch`、`model`。
- **Score**：等级从低到高，每行一个，格式同上；返回期望等级索引 `score`、最可能的
  `level`、`confidence`、`probabilities`、`branch`、`model`。
- **Evaluate**：输入 Decisions API 的 questions JSON 数组，在 JSON 输出中返回 `answers`
  和 `model`。动态问题名可由代码节点读取；单问题工具的声明变量可直接供条件节点选择。

先安装并授权插件，再在工作室导入 [示例工作流](https://github.com/Valen-Team/valen-integrations/releases/download/dify-v0.1.0/support-review.yml)。
示例将工单送入 Yes/No，根据结果输出到退款、普通支持、人工复核三个路径；请求失败走单独
的错误路径，保留原工单。各终点输出分别使用 refund_、support_、review_、failure_ 前缀，
满足 Dify 对所有输出节点变量名称唯一的要求。示例仅输出队列结果，不执行外部业务操作。可选图片输入接收一个
文件。自托管 Dify 还需配置插件容器能访问的 `FILES_URL` 和 `INTERNAL_FILES_URL`。
文件中不包含账号凭据 ID 或插件包哈希。

请求失败会产生工具错误，不会变成否定答案。请配置工具异常处理并连接失败分支。
临时故障重试两次，每次超时 120 秒。持续 429 时至少等待一分钟。输入、问题和图片会发送
到配置的服务，见 [PRIVACY.md](PRIVACY.md)。

## 升级

在同一发布页获取新版本，并在插件页安装。升级前导出工作流，保留旧安装包以便回退；升级后先运行一条示例工单，再连接实际业务操作。

[数据处理说明](PRIVACY.md) · [构建与发布](RELEASING.md)
