# 在 n8n 中使用 Valen

[English](README.md)

把客服工单分给合适的团队，为图片增加复核步骤，或按紧急程度处理告警。添加一个 Valen 节点，写下要判断的问题，再把输出口连接到后续步骤。是否题自带 `unsure` 出口，方便把中间结果交给人工。

原始字段、图片和项目关联随工单保留，答案与概率写入 `valen` 字段（覆盖已有同名字段）。

## 安装

在**自托管 n8n** 中打开 **Settings → Community nodes → Install**，填写：

```text
@valen-team/n8n-nodes-valen
```

安装后添加节点，搜索 **Valen**。需要 Node.js 22.16+，已在 n8n 2.45.6 上运行。此社区包尚未获得 n8n Cloud 认证。

也可以在运行 n8n 的机器上，以运行 n8n 的用户手动安装：

```sh
mkdir -p ~/.n8n/nodes
cd ~/.n8n/nodes
# 如果没有 package.json，先运行 npm init -y。
npm install @valen-team/n8n-nodes-valen@0.1.0 --omit=dev --legacy-peer-deps
```

手动安装后重启 n8n。Docker 用户在持久化目录 `/home/node/.n8n/nodes` 中以 `node` 用户安装。[npm 包](https://www.npmjs.com/package/@valen-team/n8n-nodes-valen)

## 跑通示例

1. 新建 **Valen API** 凭证。默认免费地址不需要密钥，测试凭证会检查模型列表。也支持带密钥的官方地址或自部署地址。
2. 从文件导入 [`examples/support-routing.json`](examples/support-routing.json)。
3. 在 **Route tickets** 节点选择刚创建的凭证，运行工作流。
4. 查看 Billing、Technical、Human review 三个输出中的 `valen` 字段。

示例只生成三条合成工单，不执行外部操作。结果随模型而变，不作为正确率保证。Choice 必须选择候选项之一，所以示例明确提供了范围外的人工复核选项。

## 配置

- **Evaluate**：输入 1–8 个 Decisions API 问题的 JSON 数组，每个问题有 `name`、`type`、`instructions`。Choice 加 `choices`，Score 加 `levels`。结果在 `valen.answers.<问题名>`。
- **Route / Yes/No**：默认概率 ≥ 0.7 进入 `yes`，≤ 0.3 进入 `no`，其余进入 `unsure`；阈值可调。
- **Route / Choice**：每行一个选项，格式为 `value` 或 `value: description`，自动生成同名输出口。
- **Route / Score**：同样逐行填写等级，从低到高。按概率最高的等级分流，平局选靠前等级，不对期望分数四舍五入。
- **Input Format**：文本、JSON 或整个输入项目。JSON 保留中文并使用两空格缩进。
- **Image Binary Field**：填写前序节点的二进制字段名，例如 `data`，支持一张 PNG、JPEG 或 WebP。远程图片先用 HTTP Request 节点下载。

模型列表来自当前连接。自部署模型名若不以 `valen` 开头，可把模型字段切到 Expression，填写 `{{ "my-model" }}`。Route 的选项和类型是固定配置，不能按项目改变输出端口。Choice、Score 无自动低置信度兜底，需要另加工作流条件。

## 失败处理

默认遇错停止。429/502/503/504 和支持的网络错误会重试两次，每次最多等待 120 秒。缺失、非法或不完整的回答也会报错，不会伪造为“否”或首个选项。

示例开启 **Continue (using error output)**，请求失败通过 n8n 独立错误输出进入 Request failure，不混入正常分支。失败项有 标准 `error` 字段和 `details.input` 中的原始输入，没有正常答案或 `branch`。Stop Workflow 会直接停止。旧的 Continue (using regular output) 会把失败送到 `unsure` 或首个端口，分流场景请使用独立错误输出。

输入、图片和问题发送到配置的 API；节点不额外存储，n8n 本身可能保留执行记录。[数据处理说明](https://valen-team.github.io/docs/valen/api/data-handling/)。

发布前检查见 [RELEASING.md](RELEASING.md)，完整字段和开发说明见 [英文说明](README.md)。
