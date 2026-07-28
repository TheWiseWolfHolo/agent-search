import json
import logging
import re
from typing import Any
from urllib.parse import quote, urlsplit, urlunsplit

import httpx
from tenacity import AsyncRetrying, retry_if_exception, stop_after_attempt

from .base import BaseSearchProvider
from .openai_compatible import _WaitWithRetryAfter, _is_retryable_exception, get_local_time_info
from ..branding import user_agent
from ..config import config
from ..logger import log_info
from ..utils import search_prompt


_logger = logging.getLogger(__name__)
_ssl_warning_emitted = False

class XAIResponsesSearchProvider(BaseSearchProvider):
    """Search provider supporting four wire formats while preserving the legacy class name."""

    def __init__(
        self,
        api_url: str,
        api_key: str,
        model: str = "grok-4-fast",
        tools: list[str] | None = None,
        api_format: str = "responses",
        reasoning_effort: str | None = None,
    ):
        super().__init__(api_url.rstrip("/"), api_key)
        self.model = model
        self.tools = tools or []
        self.api_format = config.normalize_xai_api_format(api_format)
        effort = str(reasoning_effort).strip() if reasoning_effort is not None else ""
        self.reasoning_effort = effort or None
        if self.api_format == "responses":
            self.ignored_tools: list[str] = []
        elif self.api_format == "chat-completions":
            self.ignored_tools = list(dict.fromkeys(self.tools))
        else:
            self.ignored_tools = list(dict.fromkeys(tool for tool in self.tools if tool != "web_search"))

    def get_provider_name(self) -> str:
        names = {
            "responses": "xAI Responses",
            "chat-completions": "xAI Chat Completions",
            "messages": "xAI Messages-compatible",
            "google": "xAI Google-compatible",
        }
        return names[self.api_format]

    def _build_api_headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": user_agent(),
        }
        if self.api_format == "messages":
            headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = "2023-06-01"
        elif self.api_format == "google":
            headers["x-goog-api-key"] = self.api_key
        else:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _get_ssl_verify(self) -> bool:
        global _ssl_warning_emitted
        verify = config.ssl_verify_enabled
        if not verify and not _ssl_warning_emitted:
            _ssl_warning_emitted = True
            _logger.warning("SSL_VERIFY=false: xAI 渠道请求已禁用 SSL 证书验证，存在安全风险")
        return verify

    def _request_url(self) -> str:
        parts = urlsplit(self.api_url)
        path = parts.path.rstrip("/")

        if self.api_format == "responses":
            if path.endswith("/responses"):
                endpoint_path = path
            else:
                base_path = self._without_known_endpoint(path)
                endpoint_path = f"{base_path}/responses"
        elif self.api_format == "chat-completions":
            if path.endswith("/chat/completions"):
                endpoint_path = path
            else:
                base_path = self._without_known_endpoint(path)
                endpoint_path = f"{base_path}/chat/completions"
        elif self.api_format == "messages":
            if path.endswith("/messages"):
                endpoint_path = path
            else:
                base_path = self._without_known_endpoint(path)
                endpoint_path = f"{base_path}/messages"
        elif re.search(r"/models/[^/]+:generateContent$", path, flags=re.IGNORECASE):
            endpoint_path = path
        else:
            base_path = self._without_known_endpoint(path)
            google_model = re.sub(r"^models/", "", self.model, flags=re.IGNORECASE)
            if base_path.endswith("/models"):
                endpoint_path = f"{base_path}/{quote(google_model, safe='')}:generateContent"
            else:
                endpoint_path = f"{base_path}/models/{quote(google_model, safe='')}:generateContent"

        return urlunsplit((parts.scheme, parts.netloc, endpoint_path, parts.query, parts.fragment))

    @staticmethod
    def _without_known_endpoint(path: str) -> str:
        return re.sub(
            r"/(?:responses|chat/completions|messages|models/[^/]+:generateContent)$",
            "",
            path,
            flags=re.IGNORECASE,
        )

    def _user_content(self, query: str, platform: str = "") -> str:
        platform_prompt = ""
        if platform:
            platform_prompt = (
                "\n\nYou should search the web for the information you need, "
                f"and focus on these platform: {platform}\n"
            )
        return get_local_time_info() + "\n" + query + platform_prompt

    def _xai_tools(self) -> list[dict[str, str]]:
        return [{"type": tool} for tool in self.tools]

    def _anthropic_tools(self) -> list[dict[str, str]]:
        if "web_search" not in self.tools:
            return []
        return [{"type": "web_search_20250305", "name": "web_search"}]

    def _google_tools(self) -> list[dict[str, dict]]:
        if "web_search" not in self.tools:
            return []
        return [{"googleSearch": {}}]

    def _build_search_payload(self, query: str, platform: str = "") -> dict[str, Any]:
        user_content = self._user_content(query, platform)

        if self.api_format == "responses":
            payload: dict[str, Any] = {
                "model": self.model,
                "instructions": search_prompt,
                "input": [{"role": "user", "content": user_content}],
                "stream": False,
            }
            tools = self._xai_tools()
            if tools:
                payload["tools"] = tools
            if self.reasoning_effort:
                payload["reasoning"] = {"effort": self.reasoning_effort}
            return payload

        if self.api_format == "chat-completions":
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": search_prompt},
                    {"role": "user", "content": user_content},
                ],
                "stream": False,
            }
            if self.reasoning_effort:
                payload["reasoning_effort"] = self.reasoning_effort
            return payload

        if self.api_format == "messages":
            payload = {
                "model": self.model,
                "max_tokens": 4096,
                "system": search_prompt,
                "messages": [{"role": "user", "content": user_content}],
            }
            tools = self._anthropic_tools()
            if tools:
                payload["tools"] = tools
            if self.reasoning_effort:
                payload["output_config"] = {"effort": self.reasoning_effort}
            return payload

        payload = {
            "systemInstruction": {"parts": [{"text": search_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        }
        tools = self._google_tools()
        if tools:
            payload["tools"] = tools
        if self.reasoning_effort:
            payload["generationConfig"] = {
                "thinkingConfig": {"thinkingLevel": self.reasoning_effort.upper()}
            }
        return payload

    async def search(self, query: str, platform: str = "", ctx=None) -> str:
        payload = self._build_search_payload(query, platform)
        await log_info(ctx, f"platform_prompt: {query}", config.debug_enabled)
        return await self._execute_response_with_retry(self._build_api_headers(), payload, ctx)

    async def _execute_response_with_retry(self, headers: dict, payload: dict, ctx=None) -> str:
        timeout = httpx.Timeout(connect=6.0, read=120.0, write=10.0, pool=None)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, verify=self._get_ssl_verify()) as client:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(config.retry_max_attempts + 1),
                wait=_WaitWithRetryAfter(config.retry_multiplier, config.retry_max_wait),
                retry=retry_if_exception(_is_retryable_exception),
                reraise=True,
            ):
                with attempt:
                    response = await client.post(
                        self._request_url(),
                        headers=headers,
                        json=payload,
                    )
                    response.raise_for_status()
                    return await self._parse_response(response, ctx)
        return ""

    @staticmethod
    def _append_source(
        sources: list[dict[str, str]],
        seen: set[str],
        url: Any,
        title: Any = None,
    ) -> None:
        if not isinstance(url, str) or not url.startswith(("http://", "https://")) or url in seen:
            return
        seen.add(url)
        source: dict[str, str] = {"url": url}
        if isinstance(title, str) and title.strip():
            source["title"] = title.strip()
        sources.append(source)

    @classmethod
    def _append_citations(
        cls,
        citations: Any,
        sources: list[dict[str, str]],
        seen: set[str],
    ) -> None:
        if not citations:
            return
        if not isinstance(citations, list):
            citations = [citations]
        for citation in citations:
            if isinstance(citation, str):
                cls._append_source(sources, seen, citation)
                continue
            if not isinstance(citation, dict):
                continue
            web = citation.get("web")
            if isinstance(web, dict):
                cls._append_source(
                    sources,
                    seen,
                    web.get("uri") or web.get("url"),
                    web.get("title"),
                )
                continue
            url_citation = citation.get("url_citation")
            if isinstance(url_citation, dict):
                cls._append_source(
                    sources,
                    seen,
                    url_citation.get("url") or url_citation.get("uri"),
                    url_citation.get("title"),
                )
                continue
            cls._append_source(
                sources,
                seen,
                citation.get("url") or citation.get("uri") or citation.get("href") or citation.get("link"),
                citation.get("title") or citation.get("name") or citation.get("label"),
            )

    @staticmethod
    def _finish_answer(text_parts: list[str], sources: list[dict[str, str]]) -> str:
        unique_parts: list[str] = []
        seen_parts: set[str] = set()
        for part in text_parts:
            cleaned = part.strip()
            if not cleaned or cleaned in seen_parts:
                continue
            seen_parts.add(cleaned)
            unique_parts.append(cleaned)
        answer = "\n\n".join(unique_parts).strip()
        if sources:
            answer = f"{answer}\n\nsources({json.dumps(sources, ensure_ascii=False)})".strip()
        return answer

    def _parse_responses_data(self, data: dict[str, Any]) -> str:
        text_parts: list[str] = []
        sources: list[dict[str, str]] = []
        seen: set[str] = set()

        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text:
            text_parts.append(output_text)

        for item in data.get("output", []) or []:
            if not isinstance(item, dict):
                continue
            self._append_citations(item.get("citations"), sources, seen)
            for content in item.get("content", []) or []:
                if not isinstance(content, dict) or content.get("type") != "output_text":
                    continue
                text = content.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
                self._append_citations(content.get("annotations"), sources, seen)
                self._append_citations(content.get("citations"), sources, seen)

        self._append_citations(data.get("citations"), sources, seen)
        return self._finish_answer(text_parts, sources)

    def _parse_chat_data(self, data: dict[str, Any]) -> str:
        text_parts: list[str] = []
        sources: list[dict[str, str]] = []
        seen: set[str] = set()
        self._append_citations(data.get("citations"), sources, seen)

        for choice in data.get("choices", []) or []:
            if not isinstance(choice, dict):
                continue
            self._append_citations(choice.get("citations"), sources, seen)
            message = choice.get("message")
            if not isinstance(message, dict):
                continue
            self._append_citations(message.get("citations"), sources, seen)
            self._append_citations(message.get("annotations"), sources, seen)
            content = message.get("content")
            if isinstance(content, str) and content:
                text_parts.append(content)
            elif isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    text = part.get("text")
                    if isinstance(text, str) and text:
                        text_parts.append(text)
                    self._append_citations(part.get("annotations"), sources, seen)

        return self._finish_answer(text_parts, sources)

    def _parse_messages_data(self, data: dict[str, Any]) -> str:
        text_parts: list[str] = []
        sources: list[dict[str, str]] = []
        seen: set[str] = set()
        self._append_citations(data.get("citations"), sources, seen)

        for block in data.get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str) and text:
                    text_parts.append(text)
                self._append_citations(block.get("citations"), sources, seen)
            if block.get("type") == "web_search_tool_result":
                self._append_citations(block.get("content"), sources, seen)

        return self._finish_answer(text_parts, sources)

    def _parse_google_data(self, data: dict[str, Any]) -> str:
        text_parts: list[str] = []
        sources: list[dict[str, str]] = []
        seen: set[str] = set()

        candidates = data.get("candidates", []) or []
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            content = candidate.get("content")
            if isinstance(content, dict):
                for part in content.get("parts", []) or []:
                    if not isinstance(part, dict) or part.get("thought") is True:
                        continue
                    text = part.get("text")
                    if isinstance(text, str) and text:
                        text_parts.append(text)

            grounding = candidate.get("groundingMetadata")
            if isinstance(grounding, dict):
                self._append_citations(grounding.get("groundingChunks"), sources, seen)
            citation_metadata = candidate.get("citationMetadata")
            if isinstance(citation_metadata, dict):
                self._append_citations(citation_metadata.get("citationSources"), sources, seen)

        grounding = data.get("groundingMetadata")
        if isinstance(grounding, dict):
            self._append_citations(grounding.get("groundingChunks"), sources, seen)
        return self._finish_answer(text_parts, sources)

    async def _parse_response(self, response: httpx.Response, ctx=None) -> str:
        data = response.json()
        if not isinstance(data, dict):
            answer = ""
        elif self.api_format == "responses":
            answer = self._parse_responses_data(data)
        elif self.api_format == "chat-completions":
            answer = self._parse_chat_data(data)
        elif self.api_format == "messages":
            answer = self._parse_messages_data(data)
        else:
            answer = self._parse_google_data(data)

        await log_info(ctx, f"content: {answer}", config.debug_enabled)
        return answer
