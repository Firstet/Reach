"""Unit tests for Conversation intent classification mapping."""

import pytest
from app.models import ReplyIntent


class TestConversationIntents:
    def test_reply_intent_enum_values(self):
        assert ReplyIntent.INTERESTED.value == "interested"
        assert ReplyIntent.NOT_INTERESTED.value == "not_interested"
        assert ReplyIntent.UNSUBSCRIBE.value == "unsubscribe"
        assert ReplyIntent.ROUTINE_QUESTION.value == "routine_question"
