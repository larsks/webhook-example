from flask import Flask, request, current_app, abort
import hmac


class CONFIG_DEFAULTS:
    pass

class WebhookSignatureError(Exception):
    pass

def verify_webhook_signature():
    if 'GITHUB_WEBHOOK_SECRET' not in current_app.config:
        raise WebhookSignatureError("secret has not been configured")

    if "X-Hub-Signature-256" not in request.headers:
        raise WebhookSignatureError("secret is missing signature")

    sigheader = request.headers["X-Hub-Signature-256"]
    try:
        sigtype, request_signature = sigheader.split("=", 1)
    except ValueError:
       raise WebhookSignatureError(f"invalid signature ({sigheader})")

    if sigtype != "sha256":
        raise WebhookSignatureError(f"unknown signature type ({sigtype})")

    sigbuilder = hmac.HMAC(
        key=current_app.config["GITHUB_WEBHOOK_SECRET"].encode(),
        msg=request.data,
        digestmod="sha256",
    )
    calculated = sigbuilder.hexdigest()

    if calculated != request_signature:
        raise WebhookSignatureError(
            f"bad signature (request {request_signature}, computed {calculated})"
        )

def create_app(config_from_env=True):
    app = Flask(__name__)
    app.config.from_object(CONFIG_DEFAULTS)
    if config_from_env:
        app.config.from_prefixed_env()

    @app.route("/hook/push", methods=["POST"])
    def handle_push_notification():
        try:
            verify_webhook_signature()
        except WebhookSignatureError as err:
            current_app.logger.error("signature verification failed: %s", err)
            abort(400, f"Signature verification failed: {err}")

        return {"status": "success"}

    return app


app = create_app()
