from aiogram import types
from aiogram.dispatcher.filters import BoundFilter

import postgres


class IsAnswerFilter(BoundFilter):
    """
    Check if the user is a bot admin
    """

    key = "is_answer"

    def __init__(self, is_answer: bool):
        self.is_answer = is_answer

    async def check(self, obj: types.Message):
        if obj.reply_to_message !=None:
            is_answer = await postgres.is_answer(obj.reply_to_message.message_id, obj.from_user.id)
            if is_answer:
                return self.is_answer is True
            else:
                return self.is_answer is False
        else:
            return self.is_answer is False
