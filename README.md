# WolfHolo Agent Search

[简体中文](README.zh-CN.md) | English

WolfHolo Agent Search is a CLI-first research tool for AI agents and terminal users. It gives assistants one reproducible command layer for live search, source discovery, page fetching, site mapping, provider diagnostics, and offline deep-research planning.

```powershell
agent-search search "latest OpenAI Responses API changes" --format json
agent-search fetch "https://example.com/article" --format markdown
agent-search deep "Compare Responses API web_search with Chat Completions search" --format json
```

## Why It Exists

AI agents are good at reasoning, but research workflows get messy when every tool invents its own search path. Agent Search keeps the execution layer boring and inspectable:

| Layer | Responsibility |
| --- | --- |
| CLI executor | Runs provider calls, same-capability fallback, JSON/Markdown output, config checks, smoke tests, and evidence saving |
| Agent skill | Decides which command to run, executes planned steps, and writes source-backed answers |

`agent-search search` is the fast live-search path. `agent-search deep` is an offline planner: it does not call providers by itself, and instead returns a structured `research_plan` that an agent or user can execute step by step.

## Install

```powershell
npm install -g @thewisewolfholo/agent-search@latest
agent-search --version
agent-search setup
agent-search doctor --format markdown
```

Requirements:

- Node.js 18 or newer.
- Python 3.10 or newer available as `python`, `python3`, or `py -3` on Windows.

The npm package creates an isolated `.agent-search-python` runtime during install. You still use the single `agent-search` command.

## Quick Start

Configure providers:

```powershell
agent-search setup
agent-search doctor --format json
```

Run a normal search:

```powershell
agent-search search "today's important AI news" --validation balanced --extra-sources 2 --format json
```

Fetch exact page evidence:

```powershell
agent-search fetch "https://example.com/source" --format markdown --output evidence.md
```

Plan a deeper investigation:

```powershell
agent-search deep "Deep research recent Bitcoin market movement" --budget standard --format json
```

Install or refresh the bundled skill for agent tools:

```powershell
agent-search setup --non-interactive --install-skills codex,claude,cursor,hermes
agent-search skills status --targets codex --format json
agent-search skills update --targets codex --format json
```

## Capabilities

| Capability | Commands | Providers | Role |
| --- | --- | --- | --- |
| `main_search` | `search` | xAI Responses, OpenAI-compatible Chat Completions | Broad answer synthesis and live search |
| `docs_search` | `context7-library`, `context7-docs`, `exa-search` | Context7, Exa | SDK, API, framework, official-domain, paper, and product-page discovery |
| `web_search` | `search --extra-sources` | Tavily, Firecrawl | Current, domain-filtered, and supplementary web-source discovery |
| `web_fetch` | `fetch` | Tavily, Firecrawl | Known URL extraction for evidence |
| `vertical_search` | `anysearch-*` | AnySearch | Experimental vertical search acceptance |
| `site_map` | `map` | Tavily | Documentation or product-site structure discovery |
| `deep_planner` | `deep`, `dr` | Local planner | Offline multi-step research planning |

Fallback only happens within the same capability. Page fetchers are not used as documentation search engines, and Context7 is not used for broad news.

## Configuration

Normal users should run `agent-search setup`. Advanced users and CI can set the same values through environment variables or the local config file.

| Provider | Main keys | Docs | Keys |
| --- | --- | --- | --- |
| xAI Responses | `XAI_API_KEY`, `XAI_API_URL`, `XAI_MODEL`, `XAI_TOOLS` | https://docs.x.ai/docs | https://console.x.ai/team/default/api-keys |
| OpenAI-compatible Chat Completions | `OPENAI_COMPATIBLE_API_URL`, `OPENAI_COMPATIBLE_API_KEY`, `OPENAI_COMPATIBLE_MODEL`, `OPENAI_COMPATIBLE_STREAM` | https://platform.openai.com/docs | https://platform.openai.com/api-keys |
| Exa | `EXA_API_KEY`, `EXA_BASE_URL` | https://docs.exa.ai/ | https://dashboard.exa.ai/api-keys |
| Context7 | `CONTEXT7_API_KEY`, `CONTEXT7_BASE_URL` | https://context7.com/docs | https://context7.com/ |
| Tavily | `TAVILY_API_KEY`, `TAVILY_API_URL`, `TAVILY_TIMEOUT_SECONDS` | https://docs.tavily.com/ | https://app.tavily.com/home |
| Firecrawl | `FIRECRAWL_API_KEY`, `FIRECRAWL_API_URL` | https://docs.firecrawl.dev/ | https://www.firecrawl.dev/app/api-keys |
| AnySearch | `ANYSEARCH_API_KEY`, `ANYSEARCH_API_URL`, `ANYSEARCH_TIMEOUT_SECONDS` | provider documentation | provider console |

Agent Search uses `AGENT_SEARCH_*` for its own runtime settings:

| Key | Purpose |
| --- | --- |
| `AGENT_SEARCH_CONFIG_DIR` | Override the config directory |
| `AGENT_SEARCH_VALIDATION_LEVEL` | Default validation level: `fast`, `balanced`, or `strict` |
| `AGENT_SEARCH_FALLBACK_MODE` | `auto` or `off` |
| `AGENT_SEARCH_MINIMUM_PROFILE` | `standard` or `off` |
| `AGENT_SEARCH_LOG_DIR` | Relative or absolute log directory |
| `AGENT_SEARCH_LOG_TO_FILE` | Enable file logging |

Config files:

- Windows default: `%LOCALAPPDATA%\agent-search\config.json`.
- Linux/macOS default: `~/.config/agent-search/config.json`.

For migration, if a new Agent Search config does not exist, the CLI can read a legacy `SMART_SEARCH_CONFIG_DIR` or Windows `~/.config/smart-search/config.json` file. New writes use the Agent Search config keys.

Secrets are masked in command output. Do not commit provider keys.

Provider boundaries:

- Official xAI live search uses the Responses API through `XAI_*`.
- OpenAI-compatible relays use Chat Completions through `OPENAI_COMPATIBLE_*`.
- `OPENAI_COMPATIBLE_STREAM=true`, `agent-search search --stream`, and `agent-search search --no-stream` only affect OpenAI-compatible search/fetch transport.
- `web_search` reinforcement uses Tavily first, then Firecrawl when both are configured.
- `TAVILY_API_URL` affects Tavily REST calls only. `FIRECRAWL_API_URL` affects Firecrawl REST calls only.
- AnySearch commands are explicit experiments: `anysearch-domains`, `anysearch-search`, `anysearch-extract`, and `anysearch-batch`. AnySearch is exposed as `vertical_search`; it is not part of the `web_search` fallback and is not required by the `standard` minimum profile.

## Deep Research

Deep Research is not a fixed topic recipe system. `agent-search deep` produces a local plan with `intent_signals`, `decomposition`, `capability_plan`, `gap_check`, and `usage_boundary` so an agent can choose the right CLI building blocks for the question.

Typical plan steps use commands such as `agent-search search --extra-sources`, `exa-similar`, `context7-library`, `context7-docs`, `fetch`, and `map`. `doctor` is preflight, not a research step. Unsupported key claims must be fetched or downgraded to unverified candidates.

## Command Reference

| Command | Alias | Purpose |
| --- | --- | --- |
| `search` | `s` | Live search and synthesis |
| `fetch` | `f` | Extract a known URL |
| `deep` | `dr` | Build an offline research plan |
| `map` | `m` | Explore site structure |
| `exa-search` | `exa`, `x` | Exa discovery |
| `exa-similar` | `xs` | Similar pages for a URL |
| `context7-library` | `c7`, `ctx7` | Resolve Context7 libraries |
| `context7-docs` | `c7d`, `c7docs` | Fetch Context7 docs |
| `anysearch-domains` | `as-domains` | List AnySearch domains |
| `anysearch-search` | `as-search`, `as` | AnySearch vertical/general search |
| `doctor` | `d` | Provider and config diagnostics |
| `diagnose openai-compatible` | `diag openai-compatible` | Focused relay timeout/streaming report |
| `smoke` | `sm` | Mock or live health check |
| `regression` | `reg` | Source checkout or packaged regression |
| `config` | `cfg` | Config path/list/set/unset |
| `skills` | `skill` | Skill status and update |

## Development

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m agent_search.cli smoke --mock --format json
npm install
npm test
npm pack --dry-run
```

Useful Windows wrapper check for non-ASCII JSON output:

```powershell
agent-search deep "深度搜索一下最近的比特币行情" --format json | ConvertFrom-Json
```

## Release Lanes

Stable releases use tags and npm `latest`:

```powershell
npm version patch
git push origin main
git push origin vX.Y.Z
```

Prereleases use an explicit manual GitHub Actions dispatch with `<package.json version>-beta.N` and npm dist-tag `next`. The publish workflow refuses to publish a prerelease as `latest`.

Publishing requires a repository secret named `NPM_TOKEN` with permission to publish under the npm scope `@thewisewolfholo`. A normal `main` push does not publish npm.

Before publishing, run:

```powershell
npm test
npm pack --dry-run
```

After publishing, install the package explicitly and verify:

```powershell
npm install -g @thewisewolfholo/agent-search@latest
agent-search --version
agent-search regression
agent-search smoke --mock --format json
```

## License

MIT
