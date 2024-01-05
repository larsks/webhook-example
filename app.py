from flask import Flask, request, current_app, abort
import requests
import slack
import github


class CONFIG_DEFAULTS:
    VERIFY_WEBHOOK_SIGNATURE = True


class ConfigurationError(Exception):
    pass


def require_config(app, name):
    if name not in app.config:
        raise ConfigurationError(f"missing {name}")


def create_app(config_from_env=True, config=None):
    app = Flask(__name__)

    # Configure application:
    #   Defaults ->
    #     Environment ->
    #       Explicit config
    app.config.from_object(CONFIG_DEFAULTS)
    if config_from_env:
        app.config.from_prefixed_env()
    app.config.from_object(config)

    require_config(app, "SLACK_WEBHOOK_URL")
    app.notifier = slack.SlackNotifier(app.config["SLACK_WEBHOOK_URL"])

    if app.config.get("VERIFY_WEBHOOK_SIGNATURE", True):
        require_config(app, "GITHUB_WEBHOOK_SECRET")
        app.verifier = github.GithubSignatureVerifier(
            app.config["GITHUB_WEBHOOK_SECRET"]
        )

    @app.errorhandler(ConfigurationError)
    def log_config_error(err):
        current_app.logger.error("configuration error: %s", err)
        return "Service configuration error", 500

    @app.route("/hook/push", methods=["POST"])
    def handle_push_notification():
        if app.config["VERIFY_WEBHOOK_SIGNATURE"]:
            try:
                app.verifier.verify_webhook_signature(request)
            except github.WebhookSignatureError as err:
                app.logger.error(f"invalid signature: {err}")
                abort(400, "Bad signature")

        if 'compare' in request.json:
            patchres = requests.get(f"{request.json['compare']}.patch")
            patchres.raise_for_status()
            patchtext = patchres.text
        else:
            patchtext = ""

        repo = request.json["repository"]

        message = slack.SlackMessage(
            blocks=[
                slack.SlackHeaderBlock(
                    text=slack.SlackText(text=f"Push to {repo['name']}")
                ),
                slack.SlackSectionBlock(
                    text=slack.SlackMarkdown(
                        text=f"New commits have been pushed to <{repo['html_url']}|{repo['name']}>"
                    )
                ),
            ],
            attachments=[
                slack.SlackAttachment(
                    blocks=[
                        slack.SlackSectionBlock(
                            text=slack.SlackMarkdown(text=f"```\n{patchtext}\n```")
                        ),
                    ]
                ),
            ],
        )

        if current_app.notifier:
            try:
                current_app.notifier.notify(message)
            except slack.SlackException as err:
                current_app.logger.error("slack notification failed: %s", err)

        return {"status": "success"}

    return app


app = create_app()
