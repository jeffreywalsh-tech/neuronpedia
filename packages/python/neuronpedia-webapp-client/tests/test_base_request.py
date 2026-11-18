from unittest.mock import Mock, patch

import pytest
from neuronpedia.requests.base_request import NPRequest


@pytest.mark.parametrize("headers", [{"Content-Type": "application/json"}, {}, None])
def test_custom_headers_are_forwarded_with_authentication(headers):
    request = NPRequest("feature", api_key="test-api-key")
    response = Mock(status_code=200)
    response.json.return_value = {"ok": True}

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ) as send:
        result = request.send_request(uri="example", headers=headers, json={"value": 1})

    assert result == {"ok": True}
    send.assert_called_once_with(
        "POST",
        f"{request.BASE_URL}/feature/example",
        headers={
            **(headers or {}),
            "X-Api-Key": "test-api-key",
            "Accept-Encoding": "gzip",
        },
        json={"value": 1},
    )


def test_custom_headers_are_not_modified():
    request = NPRequest("feature", api_key="test-api-key")
    headers = {"Content-Type": "application/json", "X-Api-Key": "old-key"}
    original_headers = headers.copy()
    response = Mock(status_code=200)
    response.json.return_value = {}

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ) as send:
        request.send_request(headers=headers)

    assert headers == original_headers
    assert send.call_args.kwargs["headers"]["X-Api-Key"] == "test-api-key"


def test_request_without_custom_headers_preserves_defaults():
    request = NPRequest("feature", api_key="test-api-key")
    response = Mock(status_code=200)
    response.json.return_value = {}

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ) as send:
        request.send_request(method="GET", params={"index": 1})

    send.assert_called_once_with(
        "GET",
        f"{request.BASE_URL}/feature/",
        headers={"X-Api-Key": "test-api-key", "Accept-Encoding": "gzip"},
        params={"index": 1},
    )
