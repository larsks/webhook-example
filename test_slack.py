import pytest
import slack


@pytest.mark.parametrize(
    "block_class,block_type",
    [(slack.SlackMarkdown, "mrkdwn"), (slack.SlackText, "plain_text")],
)
def test_text_blocks(block_class, block_type):
    block = block_class(text="test")
    assert block.asdict() == {"type": block_type, "text": "test"}
