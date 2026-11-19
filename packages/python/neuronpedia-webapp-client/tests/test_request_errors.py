from unittest.mock import patch

import pytest
import requests
from neuronpedia.requests.base_request import (
    NPRateLimitError,
    NPRequest,
    NPUnauthorizedError,
)


def response_with_body(status, body, content_type="application/json"):
    response = requests.Response()
    response.status_code = status
    response._content = body
    response.encoding = "utf-8"
    response.headers["Content-Type"] = content_type
    return response


@pytest.mark.parametrize(
    ("status", "body", "content_type"),
    [
        (400, b"<html>Bad request</html>", "text/html"),
        (403, b"Forbidden", "text/plain"),
        (422, b"", "application/json"),
        (418, b'{"broken":', "application/json"),
    ],
)
def test_non_json_client_errors_preserve_http_error(status, body, content_type):
    response = response_with_body(status, body, content_type)
    request = NPRequest("feature", api_key="test-api-key")

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ):
        with pytest.raises(requests.HTTPError) as error:
            request.send_request()

    assert error.value.response is response
    assert str(status) in str(error.value)
    assert body.decode() in str(error.value)


def test_plain_text_error_details_are_bounded():
    response = response_with_body(400, b"x" * 2048, "text/plain")
    request = NPRequest("feature", api_key="test-api-key")

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ):
        with pytest.raises(requests.HTTPError) as error:
            request.send_request()

    assert str(error.value) == "Request failed with status 400: " + "x" * 1024


def test_json_error_details_are_preserved():
    response = response_with_body(422, b'{"message": "Invalid model"}')
    request = NPRequest("feature", api_key="test-api-key")

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ):
        with pytest.raises(requests.HTTPError) as error:
            request.send_request()

    assert (
        str(error.value)
        == "Request failed with status 422: {'message': 'Invalid model'}"
    )
    assert error.value.response is response


@pytest.mark.parametrize(
    ("status", "expected_exception"),
    [
        (401, NPUnauthorizedError),
        (404, requests.HTTPError),
        (429, NPRateLimitError),
        (500, requests.HTTPError),
    ],
)
def test_special_error_types_are_preserved(status, expected_exception):
    response = response_with_body(status, b"Not JSON", "text/plain")
    request = NPRequest("feature", api_key="test-api-key")

    with patch(
        "neuronpedia.requests.base_request.requests.request", return_value=response
    ):
        with pytest.raises(expected_exception):
            request.send_request()
