from flask import Flask, request, current_app, abort
import hmac


class CONFIG_DEFAULTS:
    COLOR_SUCCESS = "#05eb2f"
    COLOR_FAILURE = "#f00216"


def create_app(config_from_env=True):
    app = Flask(__name__)
    app.config.from_object(CONFIG_DEFAULTS)
    if config_from_env:
        app.config.from_prefixed_env()

    @app.route("/hook/push", methods=["POST"])
    def handle_push_notification():
        if 'GITHUB_WEBHOOK_SECRET' not in current_app.config:
            current_app.logger.error("secret has not been configured")
            abort(400, "Secret has not been configured")
        if "X-Hub-Signature-256" not in request.headers:
            current_app.logger.error("request is missing signature")
            abort(400, "Request is missing signature")
        sigheader = request.headers["X-Hub-Signature-256"]
        try:
            sigtype, sigdata = sigheader.split("=", 1)
        except ValueError:
            current_app.logger.error("invalid signature (%s)", sigheader)
            abort(400, "Invalid signature")

        if sigtype != "sha256":
            current_app.logger.error("unknown signature type (%s)", sigtype)
            abort(400, "Unknown signature type")

        sigbuilder = hmac.HMAC(
            key=current_app.config["GITHUB_WEBHOOK_SECRET"].encode(),
            msg=request.data,
            digestmod="sha256",
        )
        if sigbuilder.hexdigest() != sigdata:
            current_app.logger.error(
                "bad signature (request %s, computed %s)",
                sigdata,
                sigbuilder.hexdigest(),
            )
            abort(400, "Bad signature")

        return {"status": "success"}

    return app


app = create_app()
