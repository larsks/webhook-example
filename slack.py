'''Code for generating slack messages using the block api [1].

[1]: https://api.slack.com/reference/block-kit/blocks
'''

from dataclasses import dataclass, asdict
import requests
import json
import enum


class SlackException(Exception):
    pass


class SlackTextType(enum.StrEnum):
    """Valid types for text blocks"""

    PLAIN_TEXT = "plain_text"
    MARKDOWN = "mrkdwn"


class SlackBlockType(enum.StrEnum):
    """Valid block types"""

    SECTION = "section"
    HEADER = "header"
    DIVIDER = "divider"


class jsonObject:
    @classmethod
    def remove_none(cls, value):
        """
        Recursively remove all None values from dictionaries and lists, and returns
        the result as a new dictionary or list.

        via https://stackoverflow.com/a/60124334/147356
        """
        if isinstance(value, list):
            return [cls.remove_none(x) for x in value if x is not None]
        elif isinstance(value, dict):
            return {
                key: cls.remove_none(val)
                for key, val in value.items()
                if val is not None
            }
        else:
            return value

    def asdict(self, ignore_none=False):
        return self.remove_none(asdict(self))

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
    type: SlackBlockType = SlackBlockType.SECTION


@dataclass
class SlackHeaderBlock(SlackBlock):
    text: SlackText
    type: SlackBlockType = SlackBlockType.HEADER


@dataclass
class SlackDividerBlock(SlackBlock):
    type: SlackBlockType = SlackBlockType.DIVIDER


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
        """Send a notification via a slack webhook url"""

        content = message.asdict(ignore_none=True)

        res = requests.post(self.notify_url, json=content)
        try:
            res.raise_for_status()
        except requests.exceptions.HTTPError:
            raise SlackException(res.text)
