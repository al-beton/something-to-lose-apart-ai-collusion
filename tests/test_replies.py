# Implements: agents/json-replies
import pytest

from collusion_lab.agents import ReplyError, parse_reply


def test_json_replies_read_price_and_message():
    fenced = 'Sure.\n```json\n{"scratchpad": "hm", "price": 7}\n```'
    assert parse_reply(fenced, "price", 1, 12)["price"] == 7
    assert parse_reply('{"message": "hi"}', "talk", 1, 12)["message"] == "hi"


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("no json here", "no JSON object"),
        ('{"price": 13}', "between 1 and 12"),
        ('{"price": "7"}', "whole number"),
        ('{"msg": "hi"}', "message"),
    ],
)
def test_json_replies_reject_what_cant_be_read(text, reason):
    phase = "talk" if "msg" in text else "price"
    with pytest.raises(ReplyError, match=reason):
        parse_reply(text, phase, 1, 12)
