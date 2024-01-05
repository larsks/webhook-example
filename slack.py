from dataclasses import dataclass, asdict, field
import requests
import json
import enum


# via https://stackoverflow.com/a/60124334/147356
def remove_none(value):
    """
    Recursively remove all None values from dictionaries and lists, and returns
    the result as a new dictionary or list.
    """
    if isinstance(value, list):
        return [remove_none(x) for x in value if x is not None]
    elif isinstance(value, dict):
        return {key: remove_none(val) for key, val in value.items() if val is not None}
    else:
        return value


class SlackException(Exception):
    pass


class SlackTextType(enum.StrEnum):
    PLAIN_TEXT = "plain_text"
    MARKDOWN = "mrkdwn"


class jsonObject:
    def asdict(self, ignore_none=False):
        return remove_none(asdict(self))

    def asjson(self, ignore_none=False, **kwargs):
        return json.dumps(self.asdict(ignore_none=ignore_none), **kwargs)


@dataclass
class SlackMarkdown(jsonObject):
    text: str
    type: SlackTextType = SlackTextType.MARKDOWN


@dataclass
class SlackText(jsonObject):
    text: str
    type: SlackTextType = SlackTextType.PLAIN_TEXT


class SlackBlock(jsonObject):
    pass


class SlackField(jsonObject):
    pass


@dataclass
class SlackMarkdownField(SlackField):
    text: str
    emoji: bool = False
    type: SlackTextType = SlackTextType.MARKDOWN


@dataclass
class SlackTextField(SlackField):
    text: str
    emoji: bool = False
    type: SlackTextType = SlackTextType.PLAIN_TEXT


@dataclass
class SlackSectionBlock(SlackBlock):
    text: SlackMarkdown | SlackText | None = None
    fields: list[SlackField] | None = None
    type: str = "section"

@dataclass
class SlackHeaderBlock(SlackBlock):
    text: SlackText
    type: str = "header"


@dataclass
class SlackDividerBlock(SlackBlock):
    type: str = "divider"


@dataclass
class SlackAttachment(jsonObject):
    blocks: list[SlackBlock] | None = None
    color: str | None = None
    text: str | None = None


@dataclass
class SlackMessage(jsonObject):
    text: str | None = None
    attachments: list[SlackAttachment] | None = None
    blocks: list[SlackBlock] | None = None


@dataclass
class SlackNotifier(jsonObject):
    notify_url: str

    def notify(self, message: SlackMessage):
        content = message.asdict(ignore_none=True)

        print(json.dumps(content, indent=2))

        res = requests.post(self.notify_url, json=content)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            raise SlackException(res.text)
