import httpx
import pytest

from agent_search.providers.xai_responses import XAIResponsesSearchProvider


class DummyResponse:
    def __init__(self, json_data):
        self._json_data = json_data

    def json(self):
        return self._json_data


def test_xai_responses_search_payload_uses_responses_shape_by_default():
    provider = XAIResponsesSearchProvider(
        "https://api.x.ai/v1",
        "test-key",
        "test-model",
        ["web_search", "x_search"],
    )

    payload = provider._build_search_payload("What is new?", "X")

    assert provider.api_format == "responses"
    assert provider.get_provider_name() == "xAI Responses"
    assert payload["model"] == "test-model"
    assert payload["instructions"]
    assert payload["stream"] is False
    assert payload["tools"] == [{"type": "web_search"}, {"type": "x_search"}]
    assert payload["input"][0]["role"] == "user"
    assert "What is new?" in payload["input"][0]["content"]
    assert "X" in payload["input"][0]["content"]
    assert "reasoning" not in payload


def test_chat_completions_payload_uses_native_shape_and_exposes_ignored_tools():
    provider = XAIResponsesSearchProvider(
        "https://api.x.ai/v1",
        "test-key",
        "test-model",
        ["web_search"],
        api_format="chatcompletions",
    )

    payload = provider._build_search_payload("query")

    assert provider.api_format == "chat-completions"
    assert payload["model"] == "test-model"
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][1]["role"] == "user"
    assert "tools" not in payload
    assert provider.ignored_tools == ["web_search"]
    assert payload["stream"] is False
    assert "reasoning_effort" not in payload
    assert "instructions" not in payload
    assert "input" not in payload


def test_messages_payload_uses_anthropic_native_shape_and_search_tool():
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        "claude-test",
        ["web_search", "x_search"],
        api_format="message",
    )

    payload = provider._build_search_payload("query")

    assert provider.api_format == "messages"
    assert payload["model"] == "claude-test"
    assert payload["max_tokens"] == 4096
    assert payload["system"]
    assert payload["messages"][0]["role"] == "user"
    assert payload["tools"] == [{"type": "web_search_20250305", "name": "web_search"}]
    assert provider.ignored_tools == ["x_search"]
    assert "thinking" not in payload
    assert "output_config" not in payload
    assert "stream" not in payload


def test_google_payload_uses_native_shape_and_search_tool():
    provider = XAIResponsesSearchProvider(
        "https://generativelanguage.googleapis.com/v1beta",
        "test-key",
        "gemini-test",
        ["web_search", "x_search"],
        api_format="gemini",
    )

    payload = provider._build_search_payload("query")

    assert provider.api_format == "google"
    assert payload["systemInstruction"]["parts"][0]["text"]
    assert payload["contents"][0]["role"] == "user"
    assert "query" in payload["contents"][0]["parts"][0]["text"]
    assert payload["tools"] == [{"googleSearch": {}}]
    assert provider.ignored_tools == ["x_search"]
    assert "generationConfig" not in payload
    assert "model" not in payload


@pytest.mark.parametrize(
    ("api_format", "assertion"),
    [
        ("responses", lambda payload: payload["reasoning"] == {"effort": "high"}),
        ("chat-completions", lambda payload: payload["reasoning_effort"] == "high"),
        (
            "messages",
            lambda payload: payload["output_config"] == {"effort": "high"}
            and "thinking" not in payload,
        ),
        (
            "google",
            lambda payload: payload["generationConfig"]["thinkingConfig"]["thinkingLevel"] == "HIGH",
        ),
    ],
)
def test_reasoning_effort_uses_each_protocol_native_field(api_format, assertion):
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        "test-model",
        [],
        api_format=api_format,
        reasoning_effort=" high ",
    )

    assert assertion(provider._build_search_payload("query"))


@pytest.mark.parametrize("api_format", ["responses", "chat-completions", "messages", "google"])
def test_blank_reasoning_effort_sends_no_reasoning_fields(api_format):
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        "test-model",
        [],
        api_format=api_format,
        reasoning_effort="   ",
    )

    payload = provider._build_search_payload("query")

    assert "reasoning" not in payload
    assert "reasoning_effort" not in payload
    assert "thinking" not in payload
    assert "output_config" not in payload
    assert "generationConfig" not in payload


@pytest.mark.parametrize(
    ("api_format", "expected", "unexpected"),
    [
        ("responses", {"Authorization": "Bearer test-key"}, ("x-api-key", "x-goog-api-key")),
        ("chat-completions", {"Authorization": "Bearer test-key"}, ("x-api-key", "x-goog-api-key")),
        (
            "messages",
            {"x-api-key": "test-key", "anthropic-version": "2023-06-01"},
            ("Authorization", "x-goog-api-key"),
        ),
        ("google", {"x-goog-api-key": "test-key"}, ("Authorization", "x-api-key")),
    ],
)
def test_api_headers_use_protocol_native_auth(api_format, expected, unexpected):
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        api_format=api_format,
    )

    headers = provider._build_api_headers()

    assert headers.items() >= expected.items()
    assert all(header not in headers for header in unexpected)


@pytest.mark.parametrize(
    ("api_url", "model", "api_format", "expected"),
    [
        ("https://api.x.ai/v1", "grok", "responses", "https://api.x.ai/v1/responses"),
        ("https://api.x.ai/v1/responses", "grok", "responses", "https://api.x.ai/v1/responses"),
        (
            "https://api.example/v1",
            "grok",
            "chat-completions",
            "https://api.example/v1/chat/completions",
        ),
        (
            "https://api.example/v1/chat/completions",
            "grok",
            "chat-completions",
            "https://api.example/v1/chat/completions",
        ),
        (
            "https://api.example/v1/responses",
            "grok",
            "chat-completions",
            "https://api.example/v1/chat/completions",
        ),
        ("https://api.anthropic.com/v1", "claude", "messages", "https://api.anthropic.com/v1/messages"),
        (
            "https://api.anthropic.com/v1/messages",
            "claude",
            "messages",
            "https://api.anthropic.com/v1/messages",
        ),
        (
            "https://generativelanguage.googleapis.com/v1beta",
            "models/gemini 2",
            "google",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini%202:generateContent",
        ),
        (
            "https://generativelanguage.googleapis.com/v1beta/models/gemini:generateContent",
            "other-model",
            "google",
            "https://generativelanguage.googleapis.com/v1beta/models/gemini:generateContent",
        ),
    ],
)
def test_request_url_appends_each_endpoint_once(api_url, model, api_format, expected):
    provider = XAIResponsesSearchProvider(api_url, "test-key", model, api_format=api_format)

    assert provider._request_url() == expected


def test_unknown_api_format_is_rejected():
    with pytest.raises(ValueError, match="Invalid XAI_API_FORMAT"):
        XAIResponsesSearchProvider("https://api.example/v1", "test-key", api_format="unknown")


@pytest.mark.asyncio
async def test_xai_responses_parse_output_text_and_url_citations():
    provider = XAIResponsesSearchProvider("https://api.x.ai/v1", "test-key", "test-model", ["web_search"])
    response = DummyResponse(
        {
            "output_text": "Answer [[1]](https://example.com/a).",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Answer [[1]](https://example.com/a).",
                            "annotations": [
                                {
                                    "type": "url_citation",
                                    "url": "https://example.com/a",
                                    "title": "1",
                                    "start_index": 7,
                                    "end_index": 10,
                                },
                                {
                                    "type": "url_citation",
                                    "url": "https://example.com/a",
                                    "title": "duplicate",
                                },
                            ],
                        }
                    ],
                }
            ]
        }
    )

    result = await provider._parse_response(response)

    assert "Answer [[1]](https://example.com/a)." in result
    assert result.count("Answer [[1]]") == 1
    assert 'sources([{"url": "https://example.com/a", "title": "1"}])' in result
    assert result.count("https://example.com/a") == 2


@pytest.mark.asyncio
async def test_chat_completions_parse_text_parts_and_citations():
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        api_format="chat-completions",
    )
    response = DummyResponse(
        {
            "citations": ["https://example.com/a"],
            "choices": [
                {
                    "message": {
                        "content": [{"type": "text", "text": "Chat answer"}],
                        "citations": [
                            {"url": "https://example.com/a", "title": "duplicate"},
                        ],
                        "annotations": [
                            {
                                "type": "url_citation",
                                "url_citation": {"url": "https://example.com/b", "title": "B"},
                            }
                        ],
                    }
                }
            ],
        }
    )

    result = await provider._parse_response(response)

    assert result.startswith("Chat answer")
    assert result.count("https://example.com/a") == 1
    assert '"url": "https://example.com/b", "title": "B"' in result


@pytest.mark.asyncio
async def test_messages_parse_text_citations_and_search_results():
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        api_format="messages",
    )
    response = DummyResponse(
        {
            "content": [
                {
                    "type": "text",
                    "text": "Messages answer",
                    "citations": [
                        {
                            "type": "web_search_result_location",
                            "url": "https://example.com/a",
                            "title": "A",
                        }
                    ],
                },
                {
                    "type": "web_search_tool_result",
                    "content": [
                        {
                            "type": "web_search_result",
                            "url": "https://example.com/b",
                            "title": "B",
                        }
                    ],
                },
            ]
        }
    )

    result = await provider._parse_response(response)

    assert result.startswith("Messages answer")
    assert '"url": "https://example.com/a", "title": "A"' in result
    assert '"url": "https://example.com/b", "title": "B"' in result


@pytest.mark.asyncio
async def test_google_parse_answer_without_thoughts_and_grounding_sources():
    provider = XAIResponsesSearchProvider(
        "https://api.example/v1",
        "test-key",
        api_format="google",
    )
    response = DummyResponse(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "private reasoning", "thought": True},
                            {"text": "Google answer"},
                        ]
                    },
                    "groundingMetadata": {
                        "groundingChunks": [
                            {"web": {"uri": "https://example.com/a", "title": "A"}}
                        ]
                    },
                    "citationMetadata": {
                        "citationSources": [
                            {"uri": "https://example.com/b", "title": "B"}
                        ]
                    },
                }
            ]
        }
    )

    result = await provider._parse_response(response)

    assert result.startswith("Google answer")
    assert "private reasoning" not in result
    assert '"url": "https://example.com/a", "title": "A"' in result
    assert '"url": "https://example.com/b", "title": "B"' in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("api_format", "api_url", "response_json", "expected_url"),
    [
        (
            "responses",
            "https://api.x.ai/v1/responses",
            {"output": [{"content": [{"type": "output_text", "text": "ok"}]}]},
            "https://api.x.ai/v1/responses",
        ),
        (
            "chat-completions",
            "https://api.example/v1/chat/completions",
            {"choices": [{"message": {"content": "ok"}}]},
            "https://api.example/v1/chat/completions",
        ),
        (
            "messages",
            "https://api.example/v1/messages",
            {"content": [{"type": "text", "text": "ok"}]},
            "https://api.example/v1/messages",
        ),
        (
            "google",
            "https://api.example/v1/models/model:generateContent",
            {"candidates": [{"content": {"parts": [{"text": "ok"}]}}]},
            "https://api.example/v1/models/model:generateContent",
        ),
    ],
)
async def test_execute_posts_to_selected_endpoint_once(
    monkeypatch,
    api_format,
    api_url,
    response_json,
    expected_url,
):
    provider = XAIResponsesSearchProvider(
        api_url,
        "test-key",
        "model",
        [],
        api_format=api_format,
    )
    calls = []

    class FakeAsyncClient:
        def __init__(self, timeout, follow_redirects, verify):
            self.timeout = timeout
            self.follow_redirects = follow_redirects
            self.verify = verify

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def post(self, url, headers, json):
            calls.append((url, headers, json))
            return httpx.Response(
                200,
                json=response_json,
                request=httpx.Request("POST", url),
            )

    monkeypatch.setattr("agent_search.providers.xai_responses.httpx.AsyncClient", FakeAsyncClient)

    result = await provider.search("query")

    assert result == "ok"
    assert calls[0][0] == expected_url
