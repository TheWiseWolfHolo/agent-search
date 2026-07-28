# WolfHolo Agent Search

[![CI](https://github.com/TheWiseWolfHolo/agent-search/actions/workflows/ci.yml/badge.svg)](https://github.com/TheWiseWolfHolo/agent-search/actions/workflows/ci.yml)

简体中文 | [English](README.md)

WolfHolo Agent Search 是一个给 AI 助手和命令行用户使用的 CLI-first 研究工具。它把联网搜索、来源发现、网页正文抓取、站点 map、provider 诊断和离线深度研究规划收束到一个可复现的命令层。

```powershell
agent-search search "今天 OpenAI Responses API 有什么新变化" --format json
agent-search fetch "https://example.com/article" --format markdown
agent-search deep "OpenAI Responses API web_search 和 Chat Completions 联网搜索怎么选" --format json
```

## 为什么做它

AI agent 很擅长推理，但搜索执行层如果散落在不同工具里，证据和复现就会变乱。Agent Search 的目标是让执行层稳定、透明、可诊断：

| 层 | 负责什么 |
| --- | --- |
| CLI 执行层 | provider 调用、同能力兜底、JSON/Markdown 输出、本机配置、smoke/regression、证据落盘 |
| Agent skill | 判断用户意图，选择命令，执行计划步骤，最后写出有来源支撑的回答 |

`agent-search search` 是快速联网路径。`agent-search deep` 是离线 planner：它本身不调用 provider，只输出结构化 `research_plan`，后续由 agent 或用户逐步执行。

## 安装

```powershell
npm install -g @thewisewolfholo/agent-search@latest
agent-search --version
agent-search setup
agent-search doctor --format markdown
```

前置条件：

- Node.js 18 或更新版本。
- Python 3.10 或更新版本，并且终端里能运行 `python`、`python3` 或 Windows 的 `py -3`。

npm 包安装时会创建隔离的 `.agent-search-python` 运行环境。日常只需要使用 `agent-search` 命令。

## 快速开始

配置 provider：

```powershell
agent-search setup
agent-search doctor --format json
```

普通搜索：

```powershell
agent-search search "今天有什么值得关注的 AI 新闻？" --validation balanced --extra-sources 2 --format json
```

抓取指定网页正文：

```powershell
agent-search fetch "https://example.com/source" --format markdown --output evidence.md
```

生成深度研究计划：

```powershell
agent-search deep "深度搜索一下最近的比特币行情" --budget standard --format json
```

安装或刷新 agent skill：

```powershell
agent-search setup --non-interactive --install-skills codex,claude,cursor,hermes
agent-search skills status --targets codex --format json
agent-search skills update --targets codex --format json
```

## 能力结构

| 能力 | 命令 | Provider | 用途 |
| --- | --- | --- | --- |
| `main_search` | `search` | xAI Responses、OpenAI-compatible Chat Completions | 综合回答、快速联网搜索 |
| `docs_search` | `context7-library`、`context7-docs`、`exa-search` | Context7、Exa | SDK、API、框架、官方域名、论文、产品页 |
| `web_search` | `search --extra-sources` | Tavily、Firecrawl | 时效、域名过滤和补充网页来源 |
| `web_fetch` | `fetch` | Tavily、Firecrawl | 已知 URL 正文抓取 |
| `vertical_search` | `anysearch-*` | AnySearch | 实验性垂直搜索验收 |
| `site_map` | `map` | Tavily | 文档站或产品站结构发现 |
| `deep_planner` | `deep`、`dr` | 本地 planner | 离线生成多步研究计划 |

兜底只在同一类能力里发生。网页抓取不会伪装成文档语义搜索，Context7 也不会拿来查普通新闻。

## 配置

普通用户优先运行 `agent-search setup`。CI 和高级用户可以使用环境变量或本地配置文件。

| Provider | 主要配置 | 文档 | Key |
| --- | --- | --- | --- |
| xAI Responses | `XAI_API_KEY`、`XAI_API_URL`、`XAI_MODEL`、`XAI_TOOLS` | https://docs.x.ai/docs | https://console.x.ai/team/default/api-keys |
| OpenAI-compatible Chat Completions | `OPENAI_COMPATIBLE_API_URL`、`OPENAI_COMPATIBLE_API_KEY`、`OPENAI_COMPATIBLE_MODEL`、`OPENAI_COMPATIBLE_STREAM` | https://platform.openai.com/docs | https://platform.openai.com/api-keys |
| Exa | `EXA_API_KEY`、`EXA_BASE_URL` | https://docs.exa.ai/ | https://dashboard.exa.ai/api-keys |
| Context7 | `CONTEXT7_API_KEY`、`CONTEXT7_BASE_URL` | https://context7.com/docs | https://context7.com/ |
| Tavily | `TAVILY_API_KEY`、`TAVILY_API_URL`、`TAVILY_TIMEOUT_SECONDS` | https://docs.tavily.com/ | https://app.tavily.com/home |
| Firecrawl | `FIRECRAWL_API_KEY`、`FIRECRAWL_API_URL` | https://docs.firecrawl.dev/ | https://www.firecrawl.dev/app/api-keys |
| AnySearch | `ANYSEARCH_API_KEY`、`ANYSEARCH_API_URL`、`ANYSEARCH_TIMEOUT_SECONDS` | 服务商文档 | 服务商控制台 |

Agent Search 自身使用 `AGENT_SEARCH_*`：

| Key | 用途 |
| --- | --- |
| `AGENT_SEARCH_CONFIG_DIR` | 覆盖配置目录 |
| `AGENT_SEARCH_VALIDATION_LEVEL` | 默认验证强度：`fast`、`balanced`、`strict` |
| `AGENT_SEARCH_FALLBACK_MODE` | `auto` 或 `off` |
| `AGENT_SEARCH_MINIMUM_PROFILE` | `standard` 或 `off` |
| `AGENT_SEARCH_LOG_DIR` | 日志目录 |
| `AGENT_SEARCH_LOG_TO_FILE` | 是否写文件日志 |

配置文件位置：

- Windows 默认：`%LOCALAPPDATA%\agent-search\config.json`。
- Linux/macOS 默认：`~/.config/agent-search/config.json`。

迁移时，如果新配置不存在，CLI 可以读取旧 `SMART_SEARCH_CONFIG_DIR` 或 Windows `~/.config/smart-search/config.json`。新的写入使用 Agent Search 配置键。

命令输出会遮蔽 secrets。不要把 provider key 提交到仓库。

Provider 边界：

- xAI 官方联网搜索走 Responses API，通过 `XAI_*` 配置。
- OpenAI-compatible 中转走 Chat Completions，通过 `OPENAI_COMPATIBLE_*` 配置。
- `OPENAI_COMPATIBLE_STREAM=true`、`agent-search search --stream`、`agent-search search --no-stream` 只影响 OpenAI-compatible 的 search/fetch 传输。
- `web_search` 补充来源优先使用 Tavily，两者都配置时再用 Firecrawl 作为同能力兜底。
- `TAVILY_API_URL` 只影响 Tavily REST 调用。`FIRECRAWL_API_URL` 只影响 Firecrawl REST 调用。
- AnySearch 命令是显式实验入口：`anysearch-domains`、`anysearch-search`、`anysearch-extract`、`anysearch-batch`。AnySearch 暴露为 `vertical_search`，不进入 `web_search` 兜底链，也不是 `standard` 最低配置要求。

## Deep Research

Deep Research 不是固定题材配方。`agent-search deep` 会生成本地计划，包含 `intent_signals`、`decomposition`、`capability_plan`、`gap_check`、`usage_boundary`，让 agent 根据问题选择合适的 CLI 积木。

常见计划步骤会使用 `agent-search search --extra-sources`、`exa-similar`、`context7-library`、`context7-docs`、`fetch`、`map`。`doctor` 只是配置预检，不是 research step。没有 fetch 的来源标为未验证候选。

## 命令速查

| 命令 | 别名 | 用途 |
| --- | --- | --- |
| `search` | `s` | 联网搜索和综合 |
| `fetch` | `f` | 抓取指定 URL |
| `deep` | `dr` | 生成离线研究计划 |
| `map` | `m` | 探索站点结构 |
| `exa-search` | `exa`、`x` | Exa 来源发现 |
| `exa-similar` | `xs` | 查找相似页面 |
| `context7-library` | `c7`、`ctx7` | 解析 Context7 库 |
| `context7-docs` | `c7d`、`c7docs` | 抓取 Context7 文档 |
| `anysearch-domains` | `as-domains` | 列出 AnySearch 域 |
| `anysearch-search` | `as-search`、`as` | AnySearch 搜索 |
| `doctor` | `d` | 配置和 provider 诊断 |
| `diagnose openai-compatible` | `diag openai-compatible` | 中转超时/stream 诊断 |
| `smoke` | `sm` | mock/live 健康检查 |
| `regression` | `reg` | 源码或打包回归 |
| `config` | `cfg` | 配置 path/list/set/unset |
| `skills` | `skill` | skill 状态和更新 |

## 开发

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m agent_search.cli smoke --mock --format json
npm install
npm test
npm pack --dry-run
```

Windows wrapper 的中文 JSON 管道检查：

```powershell
agent-search deep "深度搜索一下最近的比特币行情" --format json | ConvertFrom-Json
```

## 项目沿革

Agent Search 是基于
[konbakuyomu/smartsearch](https://github.com/konbakuyomu/smartsearch)
演进的独立发行版。它拥有自己的命令名、包命名空间、配置前缀、发布节奏和产品决策，同时会继续借鉴上游项目的优秀实践。原项目的 MIT 版权声明已保留在
[LICENSE](LICENSE) 中。

## 发布通道

稳定版使用 Git tag 和 npm `latest`：

```powershell
npm version patch
git push origin main
git push origin vX.Y.Z
```

测试版通过 GitHub Actions 手动 dispatch，使用 `<package.json version>-beta.N` 和 npm `next`。发布 workflow 会拒绝把 prerelease 发到 `latest`。

发布需要仓库 secret `NPM_TOKEN`，并且这个 token 必须有 npm scope `@thewisewolfholo` 的发布权限。普通 `main` push 不会发布 npm。

发布前运行：

```powershell
npm test
npm pack --dry-run
```

发布后安装验证：

```powershell
npm install -g @thewisewolfholo/agent-search@latest
agent-search --version
agent-search regression
agent-search smoke --mock --format json
```

## License

MIT
