from flask import Flask, request, current_app, abort
import hmac
import slack
import runner
import github


class CONFIG_DEFAULTS:
    VERIFY_WEBHOOK_SIGNATURE = "true"


def checkForChanges(commits):
    vlansChanged = False
    listOfSwitches = []

    for commit in commits:
        for path in commit["modified"] + commit["added"]:
            if path.startswith("host_vars"):
                listOfSwitches.append(path.split("/")[1])
            elif path == "group_vars/all/vlans.yaml":
                vlansChanged = True

    return vlansChanged, listOfSwitches


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

    require_config(app, "REPO_URL")
    app.runner = runner.GitRunner(
        app.config["REPO_URL"],
        workdir=app.config.get("WORKDIR", "."),
    )

    require_config(app, "GITHUB_WEBHOOK_SECRET")
    app.verifier = github.GithubSignatureVerifier(app.config["GITHUB_WEBHOOK_SECRET"])

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

        if "commits" in request.json:
            vlansChanged, listOfSwitches = checkForChanges(request.json["commits"])
            if vlansChanged or listOfSwitches:
                try:
                    ansible_res = current_app.runner.run(
                        current_app.config["PLAYBOOK"],
                        limit=None if vlansChanged else listOfSwitches,
                        ref=request.json["head_commit"]["id"],
                    )
                except IndexError as err:
                    current_app.logger.error("failed to apply changes: %s", err)
                    abort(400, "Failed to apply changes")

                compare_url = request.json["compare"]
                if ansible_res.status == "successful":
                    status_message = ":large_green_square: Successfully applied switch configuration changes."
                else:
                    status_message = ":large_red_square: Failed to apply switch configuration changes."

                message = slack.SlackMessage(
                    blocks=[
                        slack.SlackSectionBlock(
                            text=slack.SlackMarkdown(
                                text=(
                                    f"{status_message}\n\n"
                                    f"<{compare_url}|View changes>"
                                )
                            )
                        )
                    ],
                    attachments=[
                        slack.SlackAttachment(
                            blocks=[
                                slack.SlackSectionBlock(
                                    text=slack.SlackMarkdown(
                                        text=f"```{ansible_res.stdout.read()}```"
                                    ),
                                ),
                            ],
                        ),
                    ],
                )

                if ansible_res.status != "successful":
                    err = ansible_res.stderr.read()
                    if err:
                        message.attachments.append(
                            slack.SlackAttachment(
                                blocks=[
                                    slack.SlackSectionBlock(
                                        text=slack.SlackMarkdown(
                                            text=f"```{ansible_res.stderr.read()}```"
                                        ),
                                    ),
                                ],
                            ),
                        )

                if vlansChanged:
                    message.blocks.append(
                        slack.SlackSectionBlock(
                            text=slack.SlackMarkdown(
                                text="VLAN definitions have changed."
                            )
                        )
                    )

                if listOfSwitches:
                    message.blocks.extend(
                        [
                            slack.SlackSectionBlock(
                                text=slack.SlackMarkdown(
                                    text="Configuration has changed on the following switches:\n\n"
                                )
                            ),
                            slack.SlackSectionBlock(
                                text=slack.SlackMarkdown(
                                    text="\n".join(
                                        f"- `{item}`" for item in listOfSwitches
                                    )
                                )
                            ),
                        ]
                    )

            if current_app.notifier:
                try:
                    current_app.notifier.notify(message)
                except slack.SlackException as err:
                    current_app.logger.error("slack notification failed: %s", err)

        return {"status": "success"}

    return app


app = create_app()
