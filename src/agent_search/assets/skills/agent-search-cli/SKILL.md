---
name: agent-search-cli
description: CLI-first web research and source retrieval through the local agent-search command. Use when Codex needs current web search, source-backed fact checking, URL fetching, site mapping, official/API/documentation search, or reproducible search evidence via Skill + CLI instead of MCP tools.
---

# WolfHolo Agent Search CLI

Use the local `agent-search` command as the default execution layer for web research. The skill decides routing; the CLI performs the work; JSON or saved files provide evidence.

## Default workflow

1. Run `agent-search doctor --format json` when configuration or availability is uncertain.
2. If `doctor` reports missing configuration, use `agent-search setup` or `agent-search config set KEY VALUE` when the user provides keys. Do not ask users to edit global environment variables by default.
3. If OpenAI-compatible `search` hangs or times out after `doctor` succeeds, run `agent-search diagnose openai-compatible --format markdown` and use its summary/recommendation. This one command tests quick chat plus real search-shape `stream=false` and `stream=true`.
4. If `doctor` returns `ok: true`, use only `agent-search` CLI subcommands for web research. Do not call Codex native web search in the same task.
5. Use `agent-search skills status --targets codex --format json` when the global skill may be stale; use `agent-search skills update --targets codex --format json` to refresh this skill without rerunning setup.
6. Use `agent-search smoke --mock --format json` after CLI/provider architecture changes. Use `--live` only when real keys are available and the user expects live checks.
7. Use `agent-search search` as the first hop for realtime, broad exploration, community signals, multi-source summaries, and routing metadata.
8. Use `agent-search search --extra-sources N` for current, domain-filtered, and supplementary web-source discovery.
9. Use `agent-search context7-library` / `context7-docs` first for library, SDK, API, framework, or documentation intent.
10. Use `agent-search exa-search` for official domains, papers, product pages, trusted sites, and low-noise discovery. Do not treat Exa as the universal second hop for every high-risk or verification task.
11. Use `agent-search search --extra-sources N` for Tavily/Firecrawl horizontal candidates, and `agent-search fetch` for page text that can support final claims.
12. Use `agent-search anysearch-*` only for explicit experimental vertical search: call `anysearch-domains` first, then `anysearch-search` in a selected domain. Do not use AnySearch as default fallback.
13. Use `agent-search exa-similar` when the user gives a representative URL and wants related pages or neighboring sources.
14. Use `agent-search fetch` when the user gives a URL or a claim depends on page content.
15. Use `agent-search map` when a documentation site or domain structure matters.
16. Use `agent-search model current` only to inspect explicit provider models. To change models, use `agent-search config set XAI_MODEL ...` or `agent-search config set OPENAI_COMPATIBLE_MODEL ...`.
17. For current-news, policy, finance, health, or other high-risk facts, do not answer from broad `search.content` alone. Select the second source by intent: Context7 for docs/API, Exa for official/trusted domains or papers, `search --extra-sources` for supplementary web candidates, then `fetch` key pages and summarize only what fetched text supports.
18. Preserve command lines and source URLs in your answer. Prefer citing fetched pages or `primary_sources`; treat `extra_sources` as follow-up candidates, not verified evidence for generated claims.

## Deep Research Mode

Use Deep Research Mode when the user asks for `深度搜索`, `深度调研`, `深入搜索`, `deep search`, `deep research`, multi-source verification, cross-checking, serious review, or selection/comparison research. This is a capability-based orchestration workflow: the AI agent calls `agent-search deep "question" --format json` to get an offline plan, then composes existing `agent-search` CLI building blocks, the CLI executes those later commands, and JSON/Markdown files provide reproducible evidence. `agent-search deep` is a public planner entrypoint, not an executor; it does not call providers, run `doctor`, or fetch pages by default. It does not change default `agent-search search`, and it does not depend on an MCP session.

Do not select a fixed topic recipe. Market, product, technical docs, news, policy, claim-checking, and URL-first prompts are examples of user language, not schema modes. Decide from intent dimensions and capability needs.

Before running deep research commands, run `agent-search deep "question" --format json` and use the returned `research_plan` as your planning artifact. Use this shape:

```json
{
  "mode": "deep_research",
  "query_mode": "deep",
  "question": "user question",
  "trigger_source": "explicit_cli",
  "difficulty": "standard|high",
  "intent_signals": {
    "recency_requirement": "none|recent|current",
    "docs_api_intent": false,
    "locale_domain_scope": "global|china|known_domains|mixed",
    "known_url": false,
    "source_authority_need": "normal|high",
    "claim_risk": "low|medium|high",
    "cross_validation_need": "normal|high",
    "breadth_depth_budget": "quick|standard|deep"
  },
  "decomposition": [
    {
      "id": "sq1",
      "question": "subquestion",
      "reason": "why this subquestion is needed",
      "required_capabilities": ["broad_discovery"]
    }
  ],
  "capability_plan": [
    {
      "capability": "broad_discovery",
      "tools": ["search"],
      "reason": "Find the initial answer shape and candidate sources."
    }
  ],
  "preflight": {
    "tool": "doctor",
    "command": "agent-search doctor --format json",
    "when": "configuration or availability is uncertain"
  },
  "evidence_policy": "fetch_before_claim",
  "steps": [
    {
      "id": "s1",
      "subquestion_id": "sq1",
      "tool": "search",
      "purpose": "broad discovery",
      "command": "agent-search search \"query\" --validation balanced --extra-sources 1 --format json --output C:\\tmp\\agent-search-evidence\\YYYYMMDD-HHMM-topic\\01-search.json",
      "output_path": "C:\\tmp\\agent-search-evidence\\YYYYMMDD-HHMM-topic\\01-search.json"
    }
  ],
  "gap_check": {
    "required": true,
    "rule": "fetch missing evidence for key claims or downgrade them to unverified candidates"
  },
  "final_answer_policy": "cite fetched evidence, list unverified candidates, and include key commands",
  "usage_boundary": {
    "search": "agent-search search runs live fast/broad search immediately.",
    "deep": "agent-search deep is an offline planner; it does not execute provider calls or fetch pages.",
    "execution": "An AI agent or user executes the listed steps with existing CLI commands, then performs gap_check."
  }
}
```

Allowed `steps[].tool` values are `search`, `exa-search`, `exa-similar`, `context7-library`, `context7-docs`, `fetch`, and `map`. Each step must include `id`, `subquestion_id`, `purpose`, `command`, and `output_path`. `doctor` is preflight and must not appear in `steps[]`. Simple plans may have one subquestion; complex plans should use 2-6 subquestions unless the user explicitly asks for exhaustive coverage.

Capability boundaries:

- `search`: broad discovery and synthesis through `main_search`; inspect `routing_decision`, `provider_attempts`, `fallback_used`, and `source_warning`. Do not treat broad answers as proof for high-risk claims.
- `context7-library` / `context7-docs`: library, SDK, API, framework, and documentation intent. Prefer Context7 before Exa for docs/API questions.
- `exa-search`: low-noise discovery for official domains, papers, product pages, known domains, and trusted pages. Use it when that boundary fits; it is not the default second hop for every verification task.
- `exa-similar`: adjacent-source discovery when a known reliable URL is available.
- `search --extra-sources N`: Tavily/Firecrawl horizontal candidate collection for current, domain-filtered, and supplementary web discovery. Treat those candidates as discovery until fetched.
- `anysearch-domains` / `anysearch-search`: experimental vertical search. Inspect domains first, then search a selected domain; do not insert it into the default fallback chain.
- `fetch`: page-content evidence. Use it before claim-level conclusions.
- `map`: site structure exploration before many fetches from one site; not claim evidence by itself.

Default Deep Research orchestration:

1. Run `agent-search doctor --format json` as preflight when configuration is uncertain.
2. Call `agent-search deep "question" --format json` to create an offline `research_plan`.
3. Inspect `intent_signals`, `decomposition`, and `capability_plan`; do not choose fixed topic recipe ids.
4. Execute planned `search --validation balanced --extra-sources 1..3` steps for broad discovery and read routing metadata.
5. Execute planned `exa-search`, `exa-similar`, `context7-library`, `context7-docs`, or `map` only when their capability boundary matches the intent.
6. Use `fetch` on key URLs before making claim-level statements.
7. Run `gap_check`: if an important claim lacks fetched evidence, fetch another source or mark the claim/source as unverified.

Default evidence policy is `fetch_before_claim`: key claims in the final answer must be supported by fetched page text. Treat `primary_sources` and `extra_sources` as discovery candidates until the relevant URL has been fetched. The final answer should include fetched evidence, unverified candidate sources, and key commands used.

Deep Research smoke matrix for workflow maintenance is mock-full plus live-limited. Mock-full coverage should include trigger phrases, normal search requests that should not trigger Deep Research, required `research_plan` fields, allowed tool whitelist, `fetch_before_claim`, evidence output paths, capability boundaries, `intent_signals`, `capability_plan`, `gap_check`, simple current prompts such as `深度搜索一下最近的比特币行情`, docs/API prompts, claim-verification prompts, user-provided URL fetch-first flows, missing-provider failure guidance, and the rule that fixed topic recipe ids are not required schema. Live-limited coverage should run `doctor`, one broad `search`, one `exa-search`, and one `fetch` only when real keys are available and the user expects live checks.

Standard user-facing Deep Research tests:

```powershell
agent-search deep "深度搜索一下最近的比特币行情" --format json
agent-search deep "OpenAI Responses API web_search 和 Chat Completions 联网搜索怎么选" --budget deep --format json
agent-search deep "帮我核验这个说法是真是假：某某工具已经完全替代 Tavily 做 AI 搜索了" --format json
agent-search deep "https://example.com/source" --format json
```

## Provider Routing

- `search` builds `main_search` from configured peer providers: `XAI_API_KEY` for the xAI multi-protocol channel and `OPENAI_COMPATIBLE_API_URL` + `OPENAI_COMPATIBLE_API_KEY` for OpenAI-compatible Chat Completions.
- `search` is the default first hop for broad exploration, current synthesis, and routing metadata.
- `XAI_API_FORMAT` selects the xAI channel wire format and defaults to `responses` when missing or blank. Its canonical values are `responses`, `chat-completions`, `messages`, and `google`; common aliases are normalized by config.
- `search --api-format FORMAT` overrides `XAI_API_FORMAT` for one request. `search --reasoning-effort EFFORT` overrides optional `XAI_REASONING_EFFORT`; when neither provides a nonblank value, the request body must omit every reasoning/thinking field.
- Native xAI-channel request mappings are:
  - `responses`: `/responses`, Bearer auth, optional `reasoning.effort`; sends configured `web_search` and `x_search`.
  - `chat-completions`: `/chat/completions`, Bearer auth, optional top-level `reasoning_effort`; does not send `XAI_TOOLS`.
  - `messages`: `/messages`, `x-api-key` plus `anthropic-version`, optional `output_config.effort` without forcing a thinking mode; maps only `web_search` to `web_search_20250305` and omits `x_search`.
  - `google`: `/models/{model}:generateContent`, `x-goog-api-key`, optional `generationConfig.thinkingConfig.thinkingLevel`; maps only `web_search` to `googleSearch` and omits `x_search`.
- The separate `OPENAI_COMPATIBLE_*` peer provider continues to use Chat Completions `/chat/completions`.
- `OPENAI_COMPATIBLE_STREAM=true` or `search --stream` sets `stream=true` only for OpenAI-compatible `search` and provider-side `fetch`; it is a relay compatibility switch and does not affect the xAI channel, URL description, or source ranking.
- Legacy `AGENT_SEARCH_API_URL`, `AGENT_SEARCH_API_KEY`, `AGENT_SEARCH_API_MODE`, `AGENT_SEARCH_MODEL`, and `AGENT_SEARCH_XAI_TOOLS` are unsupported config keys.
- `XAI_TOOLS` accepts only `web_search` and `x_search`. Do not send `x_search` through Messages or Google, where no equivalent is mapped.
- The standard minimum profile requires one configured provider in each of `main_search`, `docs_search`, and fetch capability. Missing required capabilities should be treated as a hard configuration failure.
- AnySearch is reported only as optional experimental `vertical_search`; it is not part of the `web_search` fallback and is not required by the `standard` minimum profile.
- `search` exposes `--validation fast|balanced|strict`, `--fallback auto|off`, and `--providers auto|CSV`. Default validation is `balanced`; fallback only happens within the same capability.
- The xAI channel, using Responses by default, is the first main answer route for Grok/xAI. In `fallback=auto`, a failed xAI-channel request can fall back to OpenAI-compatible only when the OpenAI-compatible provider is separately configured.
- Docs/API/library routing should prefer Context7 first. Exa is for official-domain or low-noise supplemental discovery, not the default docs answer route.
- `web_search` reinforcement is a same-capability Tavily -> Firecrawl chain for current, domain-filtered, and supplementary web-source discovery.
- `search` calls Tavily and/or Firecrawl only when `--extra-sources N` is greater than 0.
- With both Tavily and Firecrawl configured, `search --extra-sources N` splits extra sources between them, with Tavily receiving about 60% and Firecrawl the rest.
- Search JSON separates `primary_sources`, `extra_sources`, and backward-compatible merged `sources`.
- `primary_sources` are extracted from the primary model answer. `extra_sources` are parallel Tavily / Firecrawl candidates and are not automatically used to verify `content`.
- `fetch` tries Tavily first and uses Firecrawl only as a fallback when Tavily returns no content.
- `map` currently uses Tavily only.
- `exa-search` and `exa-similar` use Exa only.
- `context7-library` and `context7-docs` use Context7 only.
- `anysearch-domains`, `anysearch-search`, `anysearch-extract`, and `anysearch-batch` use AnySearch only. Treat results as acceptance evidence until the target vertical domain is reviewed.
- `TAVILY_API_URL` only affects Tavily REST calls. `FIRECRAWL_API_URL` only affects Firecrawl REST calls.
- `doctor` tests configured main-search providers, Exa, Tavily, and Context7 connectivity. Firecrawl status currently means the key is configured, not that a live Firecrawl request succeeded.

## Evidence Files

For multi-source research, use `--output` to save evidence under `C:\tmp\agent-search-evidence\` with a descriptive timestamped filename. Stdout should still contain the full JSON result unless markdown or content output was explicitly chosen for human reading.

For claim-level evidence, prefer this order:

1. Discover candidate URLs with source-focused `search --extra-sources`, Context7 for docs/API/library topics, or `exa-search` for official/trusted domains and papers.
2. Fetch the exact pages that matter.
3. Use broad `search` only as synthesis or discovery, and mark claims as unverified when only `extra_sources` are available.

Prefer shorter, source-directed commands:

```powershell
agent-search exa-search "Reuters Iran Hormuz latest" --num-results 5 --include-highlights --format json --output C:\tmp\agent-search-evidence\iran-hormuz-exa.json
agent-search exa-search "OpenAI Responses API documentation" --include-domains platform.openai.com developers.openai.com --num-results 5 --include-text --format json
agent-search exa-similar "https://example.com/source" --num-results 5 --format json
agent-search fetch "https://example.com/source" --format json --output C:\tmp\agent-search-evidence\source-fetch.json
agent-search search "Iran Hormuz latest military talks" --extra-sources 3 --timeout 180 --format json --output C:\tmp\agent-search-evidence\iran-hormuz-search.json
```

## Local wrapper contract

- Expect `agent-search` to resolve from the user's PATH.
- This bundled skill is maintained with the `TheWiseWolfHolo/agent-search` repository.
- Prefer the CLI's local config file managed by `agent-search setup` / `agent-search config`.
- Environment variables remain supported for CI and advanced users, and override the local config file.
- Do not ask users to set Windows global API-key environment variables by default.
- If keys are changed with `agent-search config set`, rerun the CLI; no Codex restart is needed.
- If PATH is changed, a new terminal or Codex restart may be needed.
- On Windows, the default local config file is `%LOCALAPPDATA%\agent-search\config.json`. Linux/macOS default to `~/.config/agent-search/config.json`.
- In sandboxed runtimes (Codex CLI, containers, CI) where the default config directory is not writable or must be pinned, set `AGENT_SEARCH_CONFIG_DIR` to an absolute writable path. The CLI uses it for both config and relative logs and skips default-directory selection.
- Earlier Windows source defaults used `~\.config\agent-search\config.json`, while some installs were already pinned to `%LOCALAPPDATA%\agent-search` through `AGENT_SEARCH_CONFIG_DIR`. If the new default file is missing but the old file exists, `doctor` reports `legacy_windows_home` as the active source so upgrades do not silently lose configuration. It also reports the override value and whether it matches the current default.
- Use `agent-search doctor --format json` for agent/script parsing and `agent-search doctor --format markdown` when a human wants a detailed diagnostic report.
- If `agent-search doctor --format json` returns `ok: false`, follow the `error` field's guidance (`agent-search setup` or `agent-search config set KEY VALUE`); do not silently fall back to native web search.
- `agent-search search` has a 180-second default hard timeout. Use `--timeout SECONDS` only when the current provider or task needs a different bound.
- Use `agent-search diagnose openai-compatible --format markdown` when `doctor` succeeds but OpenAI-compatible `search` appears to hang, returns a timeout, or differs between `--stream` and `--no-stream`. It is the beginner-facing one-command report for upstream/relay compatibility.
- Interactive `agent-search setup` is a language-selecting grouped wizard with arrow-key / Space / Enter provider selection. It guides users through required `main_search`, `docs_search`, and fetch capability, then optional `web_search` reinforcement.
- The setup wizard prints beginner filling examples for official-service and relay/pooled-endpoint minimum profiles. Keep that guidance on stderr so stdout remains parseable JSON/Markdown/content output.
- Use `agent-search setup --lang en` for an English wizard and `agent-search setup --advanced` only when low-level config keys must be shown one by one.
- Use `agent-search setup --non-interactive --xai-api-format FORMAT --xai-reasoning-effort EFFORT` to persist the xAI channel wire format and optional reasoning effort. Leave effort unconfigured when requests must contain no reasoning/thinking field; if it was configured earlier, run `agent-search config unset XAI_REASONING_EFFORT`.
- Use `agent-search setup --non-interactive --openai-compatible-stream true` only when an OpenAI-compatible relay benefits from SSE streaming for long requests. Default remains false.
- Use `agent-search setup --non-interactive --anysearch-api-url "https://api.anysearch.com/mcp" --anysearch-key "key"` only for experimental AnySearch acceptance; do not add it to the normal minimum-profile setup.
- Interactive setup keeps `web_search` reinforcement focused on Tavily and Firecrawl, while AnySearch remains an optional `vertical_search` experiment.
- Use `TAVILY_API_URL=https://<host>/api/tavily` for Tavily Hikari / pooled endpoints. Root host and `/mcp` inputs are normalized by setup; `/mcp` itself is not the REST base WolfHolo Agent Search should call.
- `TAVILY_TIMEOUT_SECONDS` controls the Tavily `doctor` connectivity timeout and defaults to `30`. Raise it for slower pooled/community Tavily endpoints before judging the provider unhealthy.
- Use `FIRECRAWL_API_URL` only for a Firecrawl-compatible REST base. Official default is `https://api.firecrawl.dev/v2`.

## Command Patterns

```powershell
agent-search search "query" --extra-sources 5 --timeout 180 --format json --output result.json
agent-search search "query" --api-format responses --reasoning-effort high --format json
agent-search search "query" --stream --format json
agent-search diagnose openai-compatible --format markdown
agent-search search "query" --platform "Reuters" --model "model-id" --extra-sources 3 --timeout 180 --format json
agent-search search "nba战报" --format content
agent-search search "query" --validation strict --fallback auto --providers auto --format json
agent-search exa-search "query" --num-results 5 --search-type neural --include-text --include-highlights --include-domains docs.example.com developer.mozilla.org --format json
agent-search exa-similar "https://example.com/article" --num-results 5 --format json
agent-search context7-library "react" "hooks" --format json
agent-search context7-docs "/facebook/react" "useEffect cleanup" --format json
agent-search anysearch-domains security --format json
agent-search anysearch-search "CVE-2024-3094" --domain security.cve --max-results 3 --format json
agent-search anysearch-extract "https://example.com/source" --format json
agent-search anysearch-batch "AAPL" "RAG papers" --max-results 2 --format json
agent-search fetch "https://example.com" --format markdown --output page.md
agent-search map "https://docs.example.com" --instructions "Find API reference pages" --max-depth 1 --max-breadth 20 --limit 50 --format json
agent-search setup
agent-search setup --lang en
agent-search setup --advanced
agent-search setup --non-interactive --install-skills hermes
agent-search setup --non-interactive --xai-api-format messages --xai-reasoning-effort high
agent-search skills status --targets codex --format json
agent-search skills update --targets codex --format json
agent-search skills update --all --format json
agent-search setup --non-interactive --openai-compatible-stream true
agent-search setup --non-interactive --anysearch-api-url "https://api.anysearch.com/mcp" --anysearch-key "key"
agent-search setup --non-interactive --tavily-api-url "https://api.tavily.com" --tavily-key "key"
agent-search --version
agent-search config path --format json
agent-search config list --format json
agent-search config list --format markdown
agent-search config set XAI_API_KEY "key" --format json
agent-search config set XAI_MODEL "grok-4-fast" --format json
agent-search config set XAI_TOOLS "web_search,x_search" --format json
agent-search config set XAI_API_FORMAT "responses" --format json
agent-search config set XAI_REASONING_EFFORT "high" --format json
agent-search config unset XAI_REASONING_EFFORT --format json
agent-search config set OPENAI_COMPATIBLE_API_URL "https://api.openai.com/v1" --format json
agent-search config set OPENAI_COMPATIBLE_API_KEY "key" --format json
agent-search config set OPENAI_COMPATIBLE_MODEL "model-id" --format json
agent-search config set OPENAI_COMPATIBLE_STREAM "true" --format json
agent-search config set ANYSEARCH_API_URL "https://api.anysearch.com/mcp" --format json
agent-search config set ANYSEARCH_API_KEY "key" --format json
agent-search config set ANYSEARCH_TIMEOUT_SECONDS "30" --format json
agent-search config set EXA_API_KEY "key" --format json
agent-search config set CONTEXT7_API_KEY "key" --format json
agent-search config set TAVILY_API_URL "https://api.tavily.com" --format json
agent-search config set TAVILY_TIMEOUT_SECONDS "45" --format json
agent-search config set FIRECRAWL_API_URL "https://api.firecrawl.dev/v2" --format json
agent-search model current --format json
agent-search doctor --format json
agent-search doctor --format markdown
agent-search diagnose openai-compatible --format markdown
agent-search regression
agent-search smoke --mock --format json
agent-search smoke --mock --format markdown
```

Short aliases are supported for interactive use:

```powershell
agent-search --v
agent-search s "query" --format json
agent-search s "nba战报" --format content
agent-search f "https://example.com" --format markdown
agent-search exa "OpenAI Responses API documentation" --format json
agent-search z "today China AI news" --format json
agent-search c7 "react" "hooks" --format json
agent-search c7docs "/facebook/react" "useEffect cleanup" --format json
agent-search cfg ls --format json
agent-search d --format markdown
agent-search mdl cur --format json
agent-search sm --format json
agent-search reg
```

## Timeout Retry Policy

When `agent-search search` returns `ok: false` with `error_type: "network_error"` and an error message containing `timed out`, treat it as a retryable CLI-level timeout, not as a terminal research failure.

1. Retry up to 3 total attempts with `--timeout 180`, waiting about 5 seconds between attempts.
2. Use `--format json` and `--output PATH` for each attempt; after each attempt, inspect the saved JSON and stop on the first `"ok": true`.
3. Use `--extra-sources 1` during retry attempts to keep Tavily/Firecrawl overhead small.
4. Always use the CLI's `--timeout` option. Do not wrap `agent-search` in a shell-level `timeout` command because shell termination can prevent the CLI from writing structured failure JSON.
5. Do not rely on `AGENT_SEARCH_RETRY_*` settings for this path; search command timeouts are surfaced by the CLI result contract and should be handled by the agent workflow.
6. If all attempts time out, fall back to source-first evidence:
   - Run `exa-search` with the original query for broad source discovery.
   - Run `exa-search --include-domains` when likely official domains are known.
   - `fetch` the top 1-2 relevant URLs before making claim-level statements.
   - Mark the final answer as `source_mode: "fallback"` or clearly state that the answer was assembled from fetched sources rather than generated by `search`.

Example retry flow:

```powershell
agent-search search "query" --validation balanced --extra-sources 1 --timeout 180 --format json --output result-attempt-1.json
agent-search search "query" --validation balanced --extra-sources 1 --timeout 180 --format json --output result-attempt-2.json
agent-search search "query" --validation balanced --extra-sources 1 --timeout 180 --format json --output result-attempt-3.json
agent-search exa-search "query" --num-results 5 --include-text --format json --output exa.json
agent-search exa-search "query" --include-domains platform.openai.com developers.openai.com --num-results 3 --include-text --format json --output exa-official.json
agent-search fetch "https://example.com/source" --format markdown --output fetch.md
```

## Guardrails

- Prefer JSON for agent parsing and markdown for fetched page text intended for reading.
- Use `--output` for multi-source work, long pages, or anything the answer may need to cite later.
- Keep `--extra-sources` small (`1` to `3`) unless the user asks for broad coverage. Large values are slower and can add noise.
- Do not cite `extra_sources` as proof for a sentence in `content`; fetch the URL first or cite it only as a candidate source.
- Prefer `exa-search --include-domains` for official documentation when likely domains are known.
- Do not expose API keys. Treat `doctor` output as safe only because it is expected to mask secrets.
- In this CLI-first workflow, native `web_search` is disabled unless the user explicitly configures another approved route.
- If `doctor` or a command fails, report the failure and recovery steps; do not silently fall back to another web-search route.
- If the user explicitly asks to bypass agent-search, state that another approved web-search route must be configured first.
- Do not use legacy MCP tool names in prompts, notes, or generated instructions for this workflow.
- Treat key rotation as a hard safety gate when previous key values were pasted into chat or logs.
- For provider architecture maintenance, verify the distributable contract rather than the current developer machine's wrappers or local config. Keep fallback same-capability only.
- Treat the xAI multi-protocol channel and OpenAI-compatible as peer `main_search` providers. Do not reuse one provider's URL/key to fabricate the other provider as a fallback.

## Supporting Reference

Read `references/cli-contract.md` when you need command details, output fields, exit codes, or regression expectations.
