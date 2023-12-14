import hmac
import logging
from typing import Any

SIGNATURE_HEADER = "X-Hub-Signature-256"
LOG = logging.getLogger(__name__)


class WebhookSignatureError(Exception):
    pass


class GithubSignatureVerifier:
    def __init__(self, secret: str):
        self.secret = secret.encode()

    def verify_webhook_signature(self, request: Any) -> bool:
        try:
            signature_header = request.headers[SIGNATURE_HEADER]
            signature_sha_name, request_signature = signature_header.split("=", 1)
        except KeyError:
            raise WebhookSignatureError("missing signature header")
        except ValueError:
            raise WebhookSignatureError("unable to parse signature header")

        if signature_sha_name != "sha256":
            raise WebhookSignatureError(
                f"unknown signature type ({signature_sha_name})"
            )

        local_signature = hmac.HMAC(
            key=self.secret,
            msg=request.data,
            digestmod="sha256",
        )

        if not hmac.compare_digest(request_signature, local_signature.hexdigest()):
            raise WebhookSignatureError(
                f"bad signature: request {request_signature}, local {local_signature.hexdigest()}",
            )

        return True
