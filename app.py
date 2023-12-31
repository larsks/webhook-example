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
    else:
        app.verifier = github.GithubNullVerifier()

    @app.route("/healthz", methods=["GET"])
    def healthz():
        return "OK"

    @app.route("/hook/push", methods=["POST"])
    def handle_push_notification():
        try:
            current_app.verifier.verify_webhook_signature(request)
        except github.WebhookSignatureError as err:
            current_app.logger.error(f"invalid signature: {err}")
            abort(400, "Bad signature")

        current_app.logger.info("received valid notification from github")

        patchtext = ""
        if "compare" in request.json:
            patchres = requests.get(f"{request.json['compare']}.patch")
            if patchres.status_code == 200:
                patchtext = patchres.text

                # A text block has a max length of 3000 characters. Ensure
                # we never even come close by truncating patch text to
                # 1000 characters.
                if len(patchtext) > 1000:
                    patchtext = patchtext[:1000] + "\n.\n.\n.\n"
            else:
                current_app.logger.warn(
                    f"failed to fetch patch from {request.json['compare']}.patch"
                )

        repo = request.json["repository"]
        sender = request.json["sender"]

        if "X-GitHub-Event" not in request.headers:
            abort(400, "Missing x-github-event header")

        if request.headers["X-GitHub-Event"] == "ping":
            return {"status": "ping successful"}

        if request.headers["X-GitHub-Event"] != "push":
            abort(400, "Unsupported event")

        message = slack.SlackMessage(
            blocks=[
                slack.SlackHeaderBlock(
                    text=slack.SlackText(text=f"Push to {repo['name']}")
                ),
                slack.SlackSectionBlock(
                    text=slack.SlackMarkdown(
                        text=f"New commits have been pushed to <{repo['html_url']}|{repo['name']}> by <{sender['url']}|{sender['login']}>"
                    )
                ),
            ],
        )

        if patchtext:
            message.attachments = [
                slack.SlackAttachment(
                    blocks=[
                        slack.SlackSectionBlock(
                            text=slack.SlackMarkdown(text=f"```\n{patchtext}\n```")
                        ),
                    ]
                ),
            ]

        commit_list = []
        for commit in request.json.get("commits", []):
            commit_list.append(
                f"- {commit['message'].splitlines()[0]} (<{commit['url']}|{commit['id'][:10]}>)"
            )

        if commit_list:
            message.blocks.append(
                slack.SlackSectionBlock(
                    text=slack.SlackMarkdown(text="\n".join(commit_list))
                )
            )

        if current_app.notifier:
            try:
                current_app.notifier.notify(message)
            except slack.SlackException as err:
                current_app.logger.error("slack notification failed: %s", err)

        return {"status": "success"}

    return app


app = create_app()
