import flask
import hmac

SIGNATURE_HEADER = "X-Hub-Signature-256"


class WebhookSignatureError(Exception):
    pass


class GithubSignatureVerifier:
    """Implement webhook request validation as described in [1].

    [1]: https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries
    """

    def __init__(self, secret: str):
        self.secret = secret.encode()

    def verify_webhook_signature(self, request: flask.Request) -> bool:
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


class GithubNullVerifier:
    """A null verifier that is always successful."""

    def verify_webhook_signature(self, request: flask.Request) -> bool:
        return True
