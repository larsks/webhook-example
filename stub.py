import os
import slack
import dotenv

dotenv.load_dotenv()

message = slack.SlackMessage(
    attachments=[
        slack.SlackAttachment(
            color="#00ff00",
            blocks=[
                slack.SlackSectionBlock(
                    text=slack.SlackMarkdown(
                        text="Changes detected in switch configuration"
                    )
                ),
                slack.SlackDividerBlock(),
                slack.SlackSectionBlock(
                    text=slack.SlackMarkdown(text="Switches with configuration changes")
                ),
                slack.SlackSectionBlock(
                    fields=[
                        slack.SlackTextField(text="switch1"),
                        slack.SlackTextField(text="switch2"),
                        slack.SlackTextField(text="switch3"),
                    ]
                ),
            ],
        )
    ]
)

print(message.asjson(indent=2, ignore_none=True))

notifier = slack.SlackNotifier(os.environ["SLACK_WEBHOOK"])
notifier.notify(message)
