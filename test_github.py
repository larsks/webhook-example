import pytest
import github

from dataclasses import dataclass, field


@dataclass
class Request:
    headers: dict[str, str] = field(default_factory=dict)
    data: bytes = b""


@pytest.fixture
def verifier():
    return github.GithubSignatureVerifier("secret")


def test_missing_header(verifier):
    request = Request()
    with pytest.raises(github.WebhookSignatureError) as err:
        verifier.verify_webhook_signature(request)

    assert str(err.value) == "missing signature header"


def test_unknown_sha(verifier):
    request = Request(headers={github.SIGNATURE_HEADER: "test=test"})
    with pytest.raises(github.WebhookSignatureError) as err:
        verifier.verify_webhook_signature(request)

    assert str(err.value) == "unknown signature type (test)"


def test_invalid_header(verifier):
    request = Request(headers={github.SIGNATURE_HEADER: "test"})
    with pytest.raises(github.WebhookSignatureError) as err:
        verifier.verify_webhook_signature(request)

    assert str(err.value) == "unable to parse signature header"


def test_bad_signature(verifier):
    request = Request(headers={github.SIGNATURE_HEADER: "sha256=test"})
    with pytest.raises(github.WebhookSignatureError) as err:
        verifier.verify_webhook_signature(request)

    assert str(err.value).startswith("bad signature")


def test_good_signature(verifier):
    request = Request(
        headers={
            github.SIGNATURE_HEADER: "sha256=f9e66e179b6747ae54108f82f8ade8b3c25d76fd30afde6c395822c530196169"
        }
    )
    verifier.verify_webhook_signature(request)
