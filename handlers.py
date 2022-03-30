import datetime

import random
import sys
from typing import Union

import pytz
import requests as requests
from aiogram.dispatcher import FSMContext
from aiogram.types import BotCommandScopeDefault, BotCommandScopeChat, BotCommand, ReplyKeyboardRemove
from aiogram.utils.exceptions import MessageNotModified, RetryAfter, MessageIdentifierNotSpecified, \
    MessageToEditNotFound, BotBlocked
from aiogram.utils.markdown import hide_link
from aiograph import Telegraph
from babel import Locale

import data
import keyboards
import states
import translates
import variables
from variables import bot, dp, _
from keyboards import menu_cd, is_correct_keyboard, check_markup, reject_keyboard
from aiogram import types, Dispatcher
import postgres
import models
from variables import scheduler
admin_to_check = 0



async def kykara4a():
    settings = await postgres.get_settings()
    await bot.send_message(chat_id=settings.main_admin_id, text=translates.hello_message)
    all_letters = await postgres.get_kykara4a()
    for letter in all_letters:
        sender :models.User = await postgres.get_user_by_tg_id(letter.sender_id)
        print(f"sender = {sender.fullname}-{sender.username}. type = {letter.type}, text = {letter.text}")

#@dp.message_handler(state="*", chat_type=types.ChatType.PRIVATE)
async def test(mess: types.Message):
    await mess.answer(text=_(translates.hello))

@dp.message_handler(commands=["receive_letters"], state='*')
async def receive_letters(mess: types.Message):
    if await default_check(types.User.get_current()):
        try:
            user_in_db :models.User= await postgres.get_user_by_tg_id(types.User.get_current().id)
            if user_in_db.is_receive_letters:
                await mess.answer(_(f"You are already receiving letters", locale=user_in_db.language), reply=mess.message_id)
            else:
                min_letters = await postgres.get_min_letters()
                if min_letters is None:
                    min_letters = 1
                await user_in_db.update(is_receive_letters=True, letters_counter=min_letters+1).apply()
                await mess.answer(_(f"You will receive letters now", locale=user_in_db.language), reply=mess.message_id)

        except RetryAfter as e:
            print(e)


@dp.message_handler(commands=["not_receive_letters"], state='*')
async def not_receive_letters(mess: types.Message):
    if await default_check(types.User.get_current()):
        try:
            user_in_db: models.User = await postgres.get_user_by_tg_id(types.User.get_current().id)
            if not user_in_db.is_receive_letters:
                await mess.answer(_(f"You don`t receive letters", locale=user_in_db.language), reply=mess.message_id)
            else:
                await user_in_db.update(is_receive_letters=False).apply()
                await mess.answer(_(f"You won`t receive letters now", locale=user_in_db.language), reply=mess.message_id)

        except RetryAfter as e:
            print(e)


@dp.message_handler(is_answer=True, state="*", chat_type=types.ChatType.PRIVATE, content_types=types.ContentTypes.TEXT)
async def user_reply_text(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):

            type = "TEXT"
            text = message.parse_entities()
            sender_id = message.from_user.id
            to_message_sender = message.reply_to_message.message_id
            sender_message_id = message.message_id
            answered_to = await postgres.get_letter_or_answer_by_recipient_message_id(to_message_sender, sender_id)

            recipient_id = answered_to.sender_id
            to_message_recipient = answered_to.sender_message_id
            answer = models.Answer()
            answer.text = text
            answer.type = type
            answer.sender_id = sender_id
            answer.to_message_sender = to_message_sender
            answer.sender_message_id = sender_message_id
            answer.recipient_id = recipient_id
            answer.to_message_recipient = to_message_recipient
            answer.status = "DELIVERED"

            try:
                user_to_send9 = await postgres.get_user_by_tg_id(answer.recipient_id)
                await bot.send_message(chat_id=answer.recipient_id, text=_(translates.new_answer, locale=user_to_send9.language))
                mess = await send_answer(answer)
                answer.recipient_message_id = mess.message_id

                await message.answer(_(translates.successfull_answer_delivery), reply=message.message_id)
            except:
                await message.answer(_(translates.error_answer_delivery))
                answer.status = "ERROR"
            await answer.create()


@dp.message_handler(is_answer=True, state="*", chat_type=types.ChatType.PRIVATE, content_types=['photo', 'video', 'sticker', 'audio', 'animation', 'video_note', 'voice'])
async def user_reply_media(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
            type = message.content_type.upper()
            answer = models.Answer()
            if type == "PHOTO" or type == "VIDEO" or type == "ANIMATION":
                if message.caption:
                    answer.text = message.html_text
            sender_id = message.from_user.id
            to_message_sender = message.reply_to_message.message_id
            sender_message_id = message.message_id
            answered_to = await postgres.get_letter_or_answer_by_recipient_message_id(to_message_sender, sender_id)

            recipient_id = answered_to.sender_id
            to_message_recipient = answered_to.sender_message_id

            answer.type = type

            if answer.type == "STICKER":
                answer.file_id = message.sticker.file_id
            elif answer.type == "PHOTO":
                answer.file_id = message.photo[-1].file_id
            elif answer.type == "VIDEO":
                answer.file_id = message.video.file_id
            elif answer.type == "VOICE":
                answer.file_id = message.voice.file_id
            elif answer.type == "VIDEO_NOTE":
                answer.file_id = message.video_note.file_id
            elif answer.type == "ANIMATION":
                answer.file_id = message.animation.file_id
            elif answer.type == "AUDIO":
                answer.file_id = message.audio.file_id


            answer.sender_id = sender_id
            answer.to_message_sender = to_message_sender
            answer.sender_message_id = sender_message_id
            answer.recipient_id = recipient_id
            answer.to_message_recipient = to_message_recipient
            answer.status = "DELIVERED"

            try:
                user_to_send8 = await postgres.get_user_by_tg_id(answer.recipient_id)
                await bot.send_message(chat_id=answer.recipient_id, text=_(translates.new_answer, locale=user_to_send8.language))
                mess = await send_answer(answer)
                answer.recipient_message_id = mess.message_id

                await message.answer(_(translates.successfull_answer_delivery), reply=message.message_id)
            except Exception as e:
                print(f"Error: {e}")
                await message.answer(_(translates.error_answer_delivery))
                answer.status = "ERROR"
            await answer.create()



@dp.message_handler(commands=["test_letter"], state='*')
async def test_letter(message: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        letter = models.Letter()
        letter.status = "INQUEUE"
        letter.text = "TEST"
        letter.recipient_id = message.from_user.id
        letter.sender_id = message.from_user.id
        letter.sender_message_id = message.message_id
        letter.type = "TEXT"
        if message.from_user.username:
            letter.recipient_username = message.from_user.username
        await letter.create()

@dp.message_handler(commands=["cancel"], state=states.Letter.add_photo_to_text)
async def cancel(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        state_data = await state.get_data()
        letter: models.Letter = state_data.get('letter')


        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer(letter.text, parse_mode="HTML")
        keyboard = await is_correct_keyboard(letter, letter_preview_id=letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()


@dp.message_handler(commands=["cancel"], state="*")
async def cancel(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        await message.answer(_(translates.cancel), reply_markup=ReplyKeyboardRemove())

        await state.reset_state()


@dp.my_chat_member_handler(chat_type=types.ChatType.PRIVATE)
async def chat_update(my_chat_member: types.ChatMemberUpdated):
    user = types.User.get_current()
    user_in_DB: models.User = await postgres.get_user_by_tg_id(user.id)
    if user_in_DB:
        if my_chat_member.new_chat_member.status == "kicked":
            text = f'<a href="tg://user?id={str(user_in_DB.tg_id)}">{str(user_in_DB.fullname)}</a> заблокировал бота'
            await bot.send_message(chat_id=243568187, text=text, parse_mode="HTML")
            await user_in_DB.update(is_bot_blocked=True).apply()
        elif my_chat_member.new_chat_member.status == "member":

            text = f'<a href="tg://user?id={str(user_in_DB.tg_id)}">{str(user_in_DB.fullname)}</a> разблокировал бота'
            await bot.send_message(chat_id=243568187, text=text, parse_mode="HTML")
            await user_in_DB.update(is_bot_blocked=False).apply()



@dp.message_handler(commands=['start'], state="*")
async def send_welcome(message: types.Message):
    if not await default_check(types.User.get_current()):
        user = types.User.get_current()
        await message.answer_sticker(sticker="CAACAgQAAxkBAAIGXV__bWFhszPnWYSQJvKthQoMiem8AAJrAAPOOQgNWWbqY3aSS9AeBA")
        # Срабатывает, если пользователя нет в дб и добавляет его туда
        await message.answer(_(translates.hello_message))
        user_in_db = await postgres.create_user(user)  #
        if user_in_db.language == "en":
            await user_in_db.update(is_receive_letters=False).apply()
        await message.answer(_("You won`t receive letters from other people. You can change this option with commands /receive_letters or /not_receive_letters"))


    await message.answer(_(translates.to_send_letter_press))
    #await states.Letter.q_text_val.set()


@dp.message_handler(commands=['new'], state="*")
async def new_letter(message: types.Message):
    if await default_check(types.User.get_current()):
        await message.answer(_(translates.ask_for_letter_content))
        await states.Letter.q_text_val.set()





@dp.message_handler(commands=["language"], state='*', chat_type=types.ChatType.PRIVATE)
async def language(mess: types.Message):
    if await default_check(types.User.get_current()):
        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        user_lang = await postgres.get_user_language(user_in_db.tg_id)
        if user_lang == "uk":
            keyboard = await keyboards.language_keyboard(user=user_in_db, current_locale=0)
        else:
            keyboard = await keyboards.language_keyboard(user=user_in_db, current_locale=1)
        await mess.answer(text=_(translates.current_language), reply_markup=keyboard)

async def change_language(call: types.CallbackQuery, id, extra_data,  **kwargs):
    if await default_check(types.User.get_current()):
        user_in_db = await postgres.get_user(int(id))
        if int(extra_data) == 0 or int(extra_data) == 1:
            await call.answer()
            if int(extra_data) == 0:
                locale = "uk"
            else:
                locale = "en"
            if not user_in_db.language == locale:
                await user_in_db.update(language=locale).apply()

                if locale == "uk":
                    keyboard = await keyboards.language_keyboard(user=user_in_db, current_locale=0)
                else:
                    keyboard = await keyboards.language_keyboard(user=user_in_db, current_locale=1)
                try:
                    variables.i18n.ctx_locale.set(locale)
                    await call.message.edit_text(text=_(translates.current_language), reply_markup=keyboard)
                except:
                    pass
        else:
            if int(extra_data) == 2:
                await call.answer(text="Русский военный корабль, иди нахуй!", show_alert=True)
            elif int(extra_data) == 3:
                await call.answer(text=_("It`s not a joke!") +"\nРусский военный корабль, иди нахуй!", show_alert=True)
            elif int(extra_data) == 4:
                await call.answer(text=_("It was last warning!")+"\nРусский военный корабль, иди нахуй!", show_alert=True)
            else:
                await call.message.answer(_("You were blocked!"))
                await user_in_db.update(is_blocked_by_bot=True).apply()
                return
            extra_data = int(extra_data)+ 1
            if user_in_db.language == "uk":
                keyboard = await keyboards.language_keyboard(user=user_in_db, current_locale=0, ru_level=extra_data)
            else:
                keyboard = await keyboards.language_keyboard(user=user_in_db, current_locale=1, ru_level=extra_data)
            try:
                await call.message.edit_text(text=_(translates.current_language), reply_markup=keyboard)
            except:
                pass

async def close_language(call: types.CallbackQuery, **kwargs):
    if await default_check(types.User.get_current()):
        try:
           await call.message.delete()
        except:
            await call.message.delete_reply_markup()


@dp.message_handler(state=states.Letter.startpoint)
async def startpoint_handler(message: types.Message):
    await message.answer(_(translates.ask_for_username))
    await states.Letter.q_username.set()


@dp.message_handler(state=states.Letter.q_username)
async def username_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        username = message.text
        letter = models.Letter()

        if message.forward_from:
            letter.recipient_id = message.forward_from.id
            letter.recipient_fullname = message.forward_from.full_name
            if message.forward_from.username:
                letter.recipient_username = message.forward_from.username

        elif username.startswith('@') and len(username) > 5 and len(username) < 34:
            letter.recipient_username = username[1:]
        elif username.startswith('+'):
            letter.recipient_phone_number = username
        elif message.forward_sender_name:
            await message.answer(_(translates.account_is_closed).format(forward_sender_name=message.forward_sender_name))
            return
        else:
            await message.answer(_(translates.incorrect_request))
            return
        await message.answer(_(translates.ask_for_letter_content))
        await states.Letter.q_text_val.set()
        await state.update_data(letter=letter)


@dp.message_handler(state=states.Letter.q_username, content_types=types.ContentTypes.CONTACT)
async def recipient_contact(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        contact = message.contact

        letter = models.Letter()

        if contact.phone_number != None:
            letter.recipient_phone_number = contact.phone_number
        if contact.user_id != None:
            letter.recipient_id = contact.user_id
            letter.recipient_fullname = contact.full_name
        if letter.recipient_phone_number == None and letter.recipient_id == None:
            text = _(translates.incorrect_contact)
            await message.answer(text=text)
        else:
            text = _(translates.ask_for_letter_content)

            await message.answer(text=text)
            await states.Letter.q_text_val.set()
            await state.update_data(letter=letter)




async def get_admin_message_text(letter):
    circles = ""
    if letter.status == "CHECKING":
        circles = "🔴🔴🔴"
    elif letter.status == "REJECTED":
        circles = "🔵🔵🔵"
    elif letter.status == "APPROVED":
        circles = "🟡🟡🟡"
    elif letter.status == "ERROR":
        circles = "❌❌❌"
    elif letter.status == "DELIVERED":
        circles = "🟢🟢🟢"
    elif letter.status == "BLOCKED":
        circles = "🟣🟣🟣"

    text_to_admins = circles + f"\nНовий лист\nЩо зробити?"


    return text_to_admins


@dp.message_handler(state=states.Letter.q_text_val, content_types=['text'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.html_text
        letter.text = text_val
        letter.type = "TEXT"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.status = "CREATING"
        if letter.id:
            await letter.update(text = text_val, type = "TEXT", sender_message_id = message.message_id, link_preview = True,sender_id = message.from_user.id, status = "CREATING").apply()
        else:
            letter = await letter.create()

        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer(text_val, parse_mode="HTML")
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()


@dp.message_handler(state=states.Letter.q_text_val, content_types=['photo'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.photo[-1].file_id
        if message.caption:
            letter.text = message.html_text
        else:
            letter.text = None
        letter.type = "PHOTO"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(text = letter.text, type="PHOTO", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id = text_val, status = "CREATING").apply()
        else:
            letter = await letter.create()

        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer_photo(photo=letter.file_id, caption=letter.text, parse_mode="HTML")
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()




@dp.message_handler(state=states.Letter.q_text_val, content_types=['video'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.video.file_id
        if message.caption:
            letter.text = message.html_text
        else:
            letter.text = None
        letter.type = "VIDEO"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(text = letter.text, type="VIDEO", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id=text_val, status = "CREATING").apply()
        else:
            letter = await letter.create()


        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer_video(video=letter.file_id, caption=letter.text, parse_mode="HTML")
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()



@dp.message_handler(state=states.Letter.q_text_val, content_types=['animation'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.animation.file_id
        if message.caption:
            letter.text = message.html_text
        else:
            letter.text = None

        letter.type = "ANIMATION"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(text = letter.text, type="ANIMATION", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id=text_val, status = "CREATING").apply()
        else:
            letter = await letter.create()

        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)

        letter_preview = await message.answer_animation(animation=letter.file_id, caption=letter.text, parse_mode="HTML")
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()


@dp.message_handler(state=states.Letter.q_text_val, content_types=['sticker'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.sticker.file_id
        letter.type = "STICKER"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(type="STICKER", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id=text_val, text=None, status = "CREATING").apply()
        else:
            letter = await letter.create()


        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer_sticker(sticker=letter.file_id)
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()



@dp.message_handler(state=states.Letter.q_text_val, content_types=['voice'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.voice.file_id
        letter.type = "VOICE"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(type="VOICE", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id=text_val, text=None, status = "CREATING").apply()
        else:
            letter = await letter.create()

        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer_voice(voice=letter.file_id)
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()



@dp.message_handler(state=states.Letter.q_text_val, content_types=['audio'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.audio.file_id
        letter.type = "AUDIO"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(type="AUDIO", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id=text_val, text=None, status = "CREATING").apply()
        else:
            letter = await letter.create()


        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer_audio(audio=letter.file_id)
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()


@dp.message_handler(state=states.Letter.q_text_val, content_types=['video_note'])
async def text_val_answer(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        data = await state.get_data()
        letter: models.Letter = data.get('letter')
        if not letter:
            letter = models.Letter()
        text_val = message.video_note.file_id
        letter.type = "VIDEO_NOTE"
        letter.sender_message_id = message.message_id
        letter.link_preview = True
        letter.sender_id = message.from_user.id
        letter.file_id = text_val
        letter.status = "CREATING"
        if letter.id:
            await letter.update(type="VIDEO_NOTE", sender_message_id=message.message_id, link_preview=True,
                                sender_id=message.from_user.id, file_id=text_val, text=None, status = "CREATING").apply()
        else:
            letter = await letter.create()


        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer_video_note(video_note=letter.file_id)
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()


@dp.message_handler(state=states.Letter.correct_username)
async def text_val_answer1(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        username = message.text
        data = await state.get_data()
        letter : models.Letter = data.get('letter')
        recipient_id=None
        recipient_username = None
        recipient_phone_number=None
        if message.forward_from:
            recipient_id = message.forward_from.id
            if message.forward_from.username:
                recipient_username = message.forward_from.username
        elif username.startswith('@') and len(username) > 5 and len(username) < 34:
            recipient_username = username[1:]
        elif username.startswith('+'):
            recipient_phone_number = username
        elif message.forward_sender_name:
            await message.answer(_(translates.account_is_closed).format(forward_sender_name=message.forward_sender_name))
            return
        else:
            await message.answer(_(translates.incorrect_request))
            return
        letter.recipient_id=recipient_id
        letter.recipient_username = recipient_username
        letter.recipient_phone_number = recipient_phone_number
        letter.by_link = False
        await letter.update(recipient_id=recipient_id, recipient_username = recipient_username, recipient_phone_number = recipient_phone_number, by_link = False).apply()

        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await send_letter(letter, chat_id=message.chat.id)
        keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()

@dp.message_handler(state=states.Letter.correct_username, content_types=types.ContentTypes.CONTACT)
async def change_recipient_receive_contact(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        contact = message.contact

        data = await state.get_data()
        letter = data.get("letter")
        letter.recipient_id = None
        letter.recipient_username = None
        letter.recipient_phone_number = None

        if contact.phone_number != None:
            letter.recipient_phone_number = contact.phone_number
        if contact.user_id != None:
            letter.recipient_id = contact.user_id
            letter.recipient_fullname = contact.full_name
        if letter.recipient_phone_number == None and letter.recipient_id == None:
            text = _(translates.incorrect_contact)
            await message.answer(text=text)
        else:
            await letter.update(recipient_id=letter.recipient_id, recipient_username=letter.recipient_username,
                                recipient_phone_number=letter.recipient_phone_number, recipient_fullname=letter.recipient_fullname).apply()

            user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
            letter_preview = await send_letter(letter, chat_id=message.chat.id)
            keyboard = await is_correct_keyboard(letter, letter_preview.message_id, user=user_in_db)
            await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
            await state.reset_state()


@dp.message_handler(state=states.Letter.add_photo_to_text, content_types=['photo', 'animation'])
async def add_photo_to_text_get_photo(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):

        if message.content_type == "photo":
            file_id = message.photo[-1].file_id
        else:
            file_id = message.animation.file_id
        answer = requests.get(f"https://api.telegram.org/bot{data.token}/getFile?file_id={file_id}")
        json = answer.json()
        result = json["result"]
        file_url = f"https://api.telegram.org/file/bot{data.token}/{result['file_path']}"
        telegraph = Telegraph()
        link = await telegraph.upload_from_url(url=file_url)
        await telegraph.close()
        state_data = await state.get_data()
        letter: models.Letter = state_data.get('letter')
        old_text = letter.text
        letter.text = hide_link(link)+old_text
        letter.file_id = str(len(hide_link(link)))
        letter.link_preview = True
        await letter.update(text = hide_link(link)+old_text , link_preview = True, file_id = str(len(hide_link(link)))).apply()

        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter_preview = await message.answer(letter.text, parse_mode="HTML")
        keyboard = await is_correct_keyboard(letter, letter_preview_id=letter_preview.message_id, user=user_in_db)
        await message.answer(_(translates.is_correct_question), reply_markup=keyboard, parse_mode="HTML")
        await state.reset_state()

@dp.message_handler(state=states.Letter.add_photo_to_text, content_types=types.ContentTypes.ANY)
async def add_photo_to_text_not_photo(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current()):
        await message.answer(_(translates.ask_for_photo))



async def process_callback_button1(callback_query: types.CallbackQuery, id,**kwargs):
    if await default_check(types.User.get_current()):
        await bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_text(_(translates.ask_for_correct_username))
        await states.Letter.correct_username.set()
        state = Dispatcher.get_current().current_state()
        letter = await postgres.get_letter(int(id))
        await state.update_data(letter=letter)

async def process_callback_button2(callback_query: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current()):
        await bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_text(_(translates.ask_for_correct_letter_content))
        await states.Letter.q_text_val.set()
        state = Dispatcher.get_current().current_state()
        letter = await postgres.get_letter(int(id))
        await state.update_data(letter=letter)

async def add_photo_to_text(callback_query: types.CallbackQuery, id, extra_data, **kwargs):
    if await default_check(types.User.get_current()):
        await bot.answer_callback_query(callback_query.id)
        await callback_query.message.edit_text(_(translates.ask_for_photo))
        await states.Letter.add_photo_to_text.set()
        state = Dispatcher.get_current().current_state()
        letter = await postgres.get_letter(int(id))
        await state.update_data(letter=letter)


async def remove_photo_from_text(callback_query: types.CallbackQuery, id, extra_data, **kwargs):
    if await default_check(types.User.get_current()):
        await bot.answer_callback_query(callback_query.id)
        letter = await postgres.get_letter(int(id))
        if letter.file_id:
            old_text = letter.text
            letter.text = old_text[int(letter.file_id):]
            await letter.update(file_id = None, text =old_text[int(letter.file_id):]).apply()
            user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
            await callback_query.message.edit_reply_markup(await is_correct_keyboard(letter, extra_data, user=user_in_db))
            await bot.edit_message_text(text=letter.text, chat_id=callback_query.message.chat.id, message_id=int(extra_data), parse_mode="HTML")




async def process_callback_button3(callback_query: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current()):

        await bot.answer_callback_query(callback_query.id)

        #await callback_query.message.edit_text('Отправили! Чтобы прислать мне ещё одну валентинку нажми на /new)')
        letter = await postgres.get_letter(int(id))
        letter.status = "INQUEUE"
        await letter.update(status = "INQUEUE").apply()

        try:
            await callback_query.message.delete()
        except:
            await callback_query.message.edit_text("Отправляю...")
            await callback_query.message.delete_reply_markup()
        await callback_query.message.answer(_(translates.your_letter_sended_to_admins))

        #TODO



async def scan_queue():
    global admin_to_check
    settings = await postgres.get_settings()
    if settings.is_send_to_moders:
        letter = await postgres.get_letter_in_queue()
        if letter:
            online_admins = await postgres.get_online_admins()
            if len(online_admins) > 0:
                online_admins.sort(key= lambda x: x.tg_id)
                admin_index = admin_to_check % len(online_admins)
                admin_chat_id = online_admins[admin_index].tg_id
                checking_letters = await postgres.get_admin_checking_letters(admin_chat_id)
                if len(checking_letters) < settings.checking_letters_in_one_chat:
                    letter.status = "CHECKING"

                    admin_letter_preview = await send_letter(letter, chat_id=admin_chat_id)
                    markup = await keyboards.check_markup(letter=letter)
                    admin_mess_1 = await bot.send_message(chat_id=admin_chat_id, text=await get_admin_message_text(letter),
                                                          parse_mode="HTML", reply_markup=markup, reply_to_message_id=admin_letter_preview.message_id)
                    letter.admin_message_id = admin_mess_1.message_id
                    await letter.update(admin_message_id=admin_mess_1.message_id, status="CHECKING", admin_chat_id=admin_chat_id).apply()

                else:
                    user_to_send2 = await postgres.get_user_by_tg_id(admin_chat_id)
                    await bot.send_message(chat_id=admin_chat_id, text=_("Process letters, new letters in queue", locale=user_to_send2.language))
                admin_to_check+=1






async def disable_preview(call: types.CallbackQuery, id, extra_data, **kwargs):
    if await default_check(types.User.get_current()):

        letter= await postgres.get_letter(int(id))
        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter.link_preview = False
        await letter.update(link_preview = False).apply()
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=extra_data, text=letter.text, disable_web_page_preview=True, parse_mode="HTML")
        markup = await keyboards.is_correct_keyboard(letter, extra_data, user=user_in_db)
        await bot.answer_callback_query(call.id)
        await call.message.edit_reply_markup(reply_markup=markup)



async def enable_preview(call: types.CallbackQuery,id , extra_data, **kwargs):
    if await default_check(types.User.get_current()):
        letter = await postgres.get_letter(int(id))
        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        letter.link_preview = True
        await letter.update(link_preview=True).apply()
        await bot.edit_message_text(chat_id=call.message.chat.id, message_id=extra_data, text=letter.text,
                                    disable_web_page_preview=False, parse_mode="HTML")
        markup = await keyboards.is_correct_keyboard(letter, extra_data, user=user_in_db)
        await bot.answer_callback_query(call.id)
        await call.message.edit_reply_markup(reply_markup=markup)


async def add_contact(call: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        try:
            letter = await postgres.get_letter(int(id))
            keyboard = await keyboards.add_contact_keyboard(letter)
            await call.message.edit_text("Пришли айди или юзернейм получателя с реплаем на это сообщение", reply_markup=keyboard)
            await states.Letter.add_receiver_contact.set()
            state = Dispatcher.get_current().current_state()
            await bot.answer_callback_query(call.id)
            await state.update_data(letter_id=id)
        except RetryAfter as e:
            print(e)
            await call.answer(text="Флуд Бан, нажми через несколько секунд")


@dp.message_handler(state=states.Letter.add_receiver_contact)
async def add_receiver_contact(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current(), admin=True):
        try:
            state_data = await state.get_data()
            letter: models.Letter = await postgres.get_letter(int(state_data.get("letter_id")))
            if message.text.startswith("@") and len(message.text) > 5 and len(message.text) < 34:
                letter.recipient_username = message.text[1:]
                await letter.update(recipient_username = message.text[1:]).apply()
            elif message.text.isdigit():
                letter.recipient_id = int(message.text)
                await letter.update(recipient_id = int(message.text)).apply()

            else:
                await message.answer("Ошибка. Пришли мне юзернейм или айди получателя", reply=message.message_id)
                return

            moder_chat_id = (await postgres.get_settings()).moder_chat_id
            await bot.edit_message_text(chat_id=moder_chat_id, message_id=int(letter.admin_message_id), text=await get_admin_message_text(letter), parse_mode="HTML")
            if message.reply_to_message != None:
                keyboard = await keyboards.check_markup(letter)
                await message.reply_to_message.edit_text("Что сделать?", reply_markup=keyboard)
            await message.answer(text="Принято", reply=message.message_id)

            await state.reset_state()
        except RetryAfter as e:
            print(e)



@dp.message_handler(state=states.Letter.reject_reason)
async def reject_text(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current(), admin=True):
        try:
            state_data = await state.get_data()
            letter: models.Letter = await postgres.get_letter(int(state_data.get("letter_id")))
            letter.reject_reason = message.text
            letter.status = "REJECTED"
            await letter.update(reject_reason=message.text, status="REJECTED").apply()
            user_to_send3 = await postgres.get_user_by_tg_id(letter.sender_id)
            await bot.send_message(chat_id=letter.sender_id, text=_(translates.reject, locale=user_to_send3.language).format(reject_reason=letter.reject_reason),
                                   reply_to_message_id=letter.sender_message_id)

            await bot.edit_message_text(chat_id=letter.admin_chat_id, message_id=int(letter.admin_message_id), text=await get_admin_message_text(letter), parse_mode="HTML")

            await message.answer(text="Sent", reply=message.message_id)

            await state.reset_state()
        except RetryAfter as e:
            print(e)

@dp.message_handler(state=states.Letter.block_reason)
async def block_text(message: types.Message, state: FSMContext):
    if await default_check(types.User.get_current(), admin=True):
        try:
            state_data = await state.get_data()
            letter: models.Letter = await postgres.get_letter(int(state_data.get("letter_id")))
            letter.reject_reason = message.text
            letter.status = "BLOCKED"
            await letter.update(reject_reason=message.text, status="BLOCKED").apply()
            user_to_block : models.User= await postgres.get_user_by_tg_id(letter.sender_id)
            if not user_to_block.is_blocked_by_bot:
                await user_to_block.update(is_blocked_by_bot = True).apply()
                user_to_send4 = await postgres.get_user_by_tg_id(letter.sender_id)
                await bot.send_message(chat_id=letter.sender_id, text=_(translates.block, locale=user_to_send4.language).format(block_reason=letter.reject_reason))

            await bot.edit_message_text(chat_id=letter.admin_chat_id, message_id=int(letter.admin_message_id), text=await get_admin_message_text(letter), parse_mode="HTML")

            await message.answer(text="Sent", reply=message.message_id)

            await state.reset_state()
        except RetryAfter as e:
            print(e)



async def initialisate_chat_with_user(call: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        try:
            await bot.answer_callback_query(call.id)
            if types.User.get_current().id == data.userbot_id:

                letter= await postgres.get_letter(int(id))
                markup = await keyboards.delivery_confirm_markup(letter=letter)
                await call.message.edit_text(text="Ты точно начал диалог?\nЕсли нет, то сообщение не сможет отправиться",
                                             reply_markup=markup)
            else:
                await bot.answer_callback_query(callback_query_id=call.id, text="Эту кнопку должен нажать акк юзербота",
                                                show_alert=True)
        except RetryAfter as e:
            print(e)
            await call.answer(text="Флуд Бан, нажми через несколько секунд")


async def reject_letter(call: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        try:
            await bot.answer_callback_query(call.id)
            letter = await postgres.get_letter(int(id))
            user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
            keyboard = await reject_keyboard(letter=letter, user=user_in_db)
            user_to_send21 = await postgres.get_user_by_tg_id(letter.sender_id)
            await call.message.edit_text(_("Write reject reason with reply") + f"\nLanguage: {user_to_send21.language}", reply_markup=keyboard)

            await states.Letter.reject_reason.set()
            state = Dispatcher.get_current().current_state()
            await state.update_data(letter_id=id)
        except RetryAfter as e:
            print(e)
            await call.answer(text="Flood Ban, retry after a few seconds")


async def block_letter(call: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        try:
            await bot.answer_callback_query(call.id)
            letter = await postgres.get_letter(int(id))
            user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
            keyboard = await keyboards.block_keyboard(letter=letter, user=user_in_db)
            user_to_send22 = await postgres.get_user_by_tg_id(letter.sender_id)
            await call.message.edit_text(_("Write block reason with reply")+ f"\nLanguage: {user_to_send22.language}", reply_markup=keyboard)

            await states.Letter.block_reason.set()
            state = Dispatcher.get_current().current_state()
            await state.update_data(letter_id=id)
        except RetryAfter as e:
            print(e)
            await call.answer(text="Flood Ban, retry after a few seconds")

async def choose_whom_to_send_letter(user_tg_id):
    users_with_min_letters = await postgres.get_users_with_min_letters(user_tg_id)

    if users_with_min_letters:
        if len(users_with_min_letters) == 0:
            return None
        elif len(users_with_min_letters) == 1:
            return users_with_min_letters[0]
        else:
            index = random.randint(0, len(users_with_min_letters)-1)
            return  users_with_min_letters[index]
    else: return None


async def approve_letter(call: types.CallbackQuery, id, extra_data, **kwargs):
    if await default_check(types.User.get_current(), admin=True):

        if int(extra_data) == 1 and types.User.get_current().id == data.userbot_id or int(extra_data) == 0:
            try:

                letter: models.Letter = await postgres.get_letter(int(id))
                user_to_send = await choose_whom_to_send_letter(letter.sender_id)

                if user_to_send:
                    letter.recipient_id = user_to_send.tg_id
                    await letter.update(recipient_id = user_to_send.tg_id).apply()
                    user_to_send5 = await postgres.get_user_by_tg_id(letter.recipient_id)

                    try:
                        await bot.send_message(chat_id=letter.recipient_id,
                                               text=_(translates.new_letter, locale=user_to_send5.language))
                        message = await send_letter(letter)
                    except BotBlocked as e:
                        print(e)
                        print(user_to_send.fullname)
                        await user_to_send.update(is_bot_blocked = True).apply()
                        await call.answer("Натисни ще раз, челік блокнув бота, оберемо іншого")
                        return
                    letter.recipient_message_id = message.message_id
                    user_to_send.letters_counter = user_to_send.letters_counter +1
                    await user_to_send.update(letters_counter = user_to_send.letters_counter).apply()
                    letter.status = "DELIVERED"
                    await letter.update(status="DELIVERED", recipient_message_id = message.message_id).apply()

                    await bot.edit_message_text(chat_id=letter.admin_chat_id, message_id=int(letter.admin_message_id),
                                                text=await get_admin_message_text(letter), parse_mode="HTML")
                    user_to_send6 = await postgres.get_user_by_tg_id(letter.sender_id)
                    await bot.send_message(chat_id=letter.sender_id, text=_(translates.successfull_letter_delivery, locale=user_to_send6.language), reply_to_message_id=letter.sender_message_id)
                else:
                    await call.answer("Зараз нема кому відправити листа. Спробуй пізніше")
            except RetryAfter as e:
                print(e)
                await bot.answer_callback_query(call.id, text="Флуд Бан, нажми через несколько секунд")
        else:
            await bot.answer_callback_query(callback_query_id=call.id, text="Эту кнопку должен нажать акк юзербота",
                                            show_alert=True)

#@dp.message_handler(lambda message: message.chat_id == data.moder_chat_id, commands=["add_admin"], chat_type=types.ChatType.GROUP)
@dp.message_handler(commands=["add_admin"], state='*')
async def add_admin(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        message_array = mess.text.split(" ")
        admin_contact = message_array[-1]
        try:
            if admin_contact.startswith("@") and len(admin_contact) > 5 and len(admin_contact) < 34:
                user_in_db = await postgres.get_user_by_username(admin_contact[1:])
                if user_in_db:
                    if user_in_db.is_admin:
                        await mess.answer(f"{admin_contact} и так админ", reply=mess.message_id)
                    else:
                        await user_in_db.update(is_admin=True).apply()
                        await mess.answer(f"{admin_contact} назначен админом", reply=mess.message_id)
                        await set_personal_bot_commands(user_in_db.id)

                else:
                    await mess.answer(f"Не нашел {admin_contact} в базе", reply=mess.message_id)

            elif admin_contact.isdigit():
                user_in_db = await postgres.get_user_by_tg_id(int(admin_contact))
                if user_in_db:
                    if user_in_db.is_admin:
                        await mess.answer(f'<a href="tg://user?id=' + str(
                            user_in_db.tg_id) + '">' + user_in_db.fullname + '</a> и так админ', parse_mode="HTML", reply=mess.message_id)
                    else:
                        await user_in_db.update(is_admin=True).apply()
                        await mess.answer(f'<a href="tg://user?id=' + str(
                                user_in_db.tg_id) + '">' + user_in_db.fullname + '</a> назначен админом', parse_mode="HTML", reply=mess.message_id)
                        await set_personal_bot_commands(user_in_db.id)

                else:
                    await mess.answer("Не нашел такого человека в базе", reply=mess.message_id)
            else:
                await mess.answer("Формат команды <code>/add_admin id_or_username</code>", reply=mess.message_id, parse_mode="HTML")
        except RetryAfter as e:
            print(e)


@dp.message_handler(commands=["del_admin"], state='*')
async def del_admin(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        try:
            message_array = mess.text.split(" ")
            admin_contact = message_array[-1]
            if admin_contact.startswith("@") and len(admin_contact) > 5 and len(admin_contact) < 34:
                user_in_db = await postgres.get_user_by_username(admin_contact[1:])
                if user_in_db:
                    if not user_in_db.is_admin:
                        await mess.answer(f"{admin_contact} и так не админ", reply=mess.message_id)
                    else:
                        await user_in_db.update(is_admin=False).apply()
                        await mess.answer(f"{admin_contact} больше не админ", reply=mess.message_id)
                        await set_personal_bot_commands(user_in_db.id)

                else:
                    await mess.answer(f"Не нашел {admin_contact} в базе", reply=mess.message_id)

            elif admin_contact.isdigit():
                user_in_db = await postgres.get_user_by_tg_id(int(admin_contact))
                if user_in_db:
                    if not user_in_db.is_admin:
                        await mess.answer(f'<a href="tg://user?id=' + str(
                            user_in_db.tg_id) + '">' + user_in_db.fullname + '</a> и так не админ', parse_mode="HTML", reply=mess.message_id)
                    else:
                        await user_in_db.update(is_admin=False).apply()
                        await mess.answer(f'<a href="tg://user?id=' + str(
                                user_in_db.tg_id) + '">' + user_in_db.fullname + '</a> больше не админ', parse_mode="HTML", reply=mess.message_id)
                        await set_personal_bot_commands(user_in_db.id)

                else:
                    await mess.answer("Не нашел такого человека в базе", reply=mess.message_id)
            else:
                await mess.answer("Формат команды <code>/del_admin id_or_username</code>", reply=mess.message_id, parse_mode="HTML")
        except RetryAfter as e:
            print(e)


@dp.message_handler(commands=["queue_scan_timer"], state='*')
async def queue_scan_timer(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        settings = await postgres.get_settings()
        if settings:
            try:
                message_array = mess.text.split(" ")
                timer = message_array[-1]
                if timer.isdigit() and int(timer) > 0:
                    #scheduler.remove_job(variables.queue_scan_job_id)

                    variables.queue_scan_job_id =scheduler.reschedule_job(variables.queue_scan_job_id, trigger='interval', seconds=int(timer)).id

                    user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
                    await settings.update(queue_scan_timer=int(timer)).apply()
                    await mess.answer(f"Queue scan timer changed to {timer} seconds", reply=mess.message_id)
                    if user_in_db.tg_id != settings.main_admin_id:
                        text = f'<a href="tg://user?id={str(user_in_db.tg_id)}">{str(user_in_db.fullname)}</a> изменил таймер скана очереди на {timer}'
                        user_to_send7 = await postgres.get_user_by_tg_id(settings.main_admin_id)

                        await bot.send_message(chat_id=_(settings.main_admin_id, locale=user_to_send7.language), text=text, parse_mode="HTML")


                else:
                    await mess.answer("Формат команды <code>/queue_scan_timer time_in_seconds</code>", reply=mess.message_id, parse_mode="HTML")
            except RetryAfter as e:
                print(e)




@dp.message_handler(commands=["dashboard_scan_timer"], state='*')
async def dashboard_scan_timer(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        settings = await postgres.get_settings()
        if settings:
            try:
                message_array = mess.text.split(" ")
                timer = message_array[-1]
                if timer.isdigit() and int(timer) > 0:

                    #scheduler.remove_job(variables.dashboard_scan_job_id)

                    variables.dashboard_scan_job_id= scheduler.reschedule_job(variables.dashboard_scan_job_id, trigger='interval', seconds=int(timer)).id
                    user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)

                    await settings.update(dashboard_scan_timer=int(timer)).apply()
                    await mess.answer(f"Dashboard scan timer changed to {timer} seconds", reply=mess.message_id)
                    if user_in_db.tg_id != settings.main_admin_id:
                        text = f'<a href="tg://user?id={str(user_in_db.tg_id)}">{str(user_in_db.fullname)}</a> изменил таймер скана дашборда на {timer}'
                        await bot.send_message(chat_id=settings.main_admin_id, text=text, parse_mode="HTML")


                else:
                    await mess.answer("Формат команды <code>/dashboard_scan_timer time_in_seconds</code>",
                                      reply=mess.message_id, parse_mode="HTML")
            except RetryAfter as e:
                print(e)



@dp.message_handler(commands=["online"], state='*')
async def online(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        user_in_db : models.User = await postgres.get_user_by_tg_id(types.User.get_current().id)
        if user_in_db.is_online:
            await mess.answer(_("You are already online. To go offline - press /offline"))
        else:
            await user_in_db.update(is_online=True).apply()
            await mess.answer(_("You are online now"))

@dp.message_handler(commands=["offline"], state='*')
async def offline(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        user_in_db : models.User = await postgres.get_user_by_tg_id(types.User.get_current().id)
        if not user_in_db.is_online:
            await mess.answer(_("You are already offline. To go online - press /online"))
        else:
            await user_in_db.update(is_online=False).apply()
            await mess.answer(_("You are offline now"))


@dp.message_handler(commands=["start_queue"], state='*')
async def start_queue(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        try:
            settings = await postgres.get_settings()
            if settings:
                if settings.is_send_to_moders:
                    await mess.answer(f"Валентинки и так присылаются", reply=mess.message_id)
                else:
                    await settings.update(is_send_to_moders=True).apply()
                    await mess.answer(f"Теперь валентинки из очереди будут присылаться в чат админов", reply=mess.message_id)
                    user_in_db : models.User = await postgres.get_user_by_tg_id(types.User.get_current().id)
                    if user_in_db.tg_id != settings.main_admin_id:
                        text = f'<a href="tg://user?id={str(user_in_db.tg_id)}">{str(user_in_db.fullname)}</a> включил обработку очереди'
                        await bot.send_message(chat_id=settings.main_admin_id, text=text)


        except RetryAfter as e:
            print(e)


@dp.message_handler(commands=["stop_queue"], state='*')
async def stop_queue(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        try:
            settings = await postgres.get_settings()
            if settings:
                if not settings.is_send_to_moders:
                    await mess.answer(f"Валентинки и так не присылаются", reply=mess.message_id)
                else:
                    await settings.update(is_send_to_moders=False).apply()
                    await mess.answer(f"Теперь валентинки из очереди не будут присылаться в чат админов",
                                      reply=mess.message_id)
                    user_in_db: models.User = await postgres.get_user_by_tg_id(types.User.get_current().id)
                    if user_in_db.tg_id != settings.main_admin_id:
                        text = f'<a href="tg://user?id={str(user_in_db.tg_id)}">{str(user_in_db.fullname)}</a> остановил обработку очереди'
                        await bot.send_message(chat_id=settings.main_admin_id, text=text)

        except RetryAfter as e:
            print(e)


@dp.message_handler(lambda message: message.chat.id == data.moder_chat_id, commands=["change_moder_chat_id"])
async def change_moder_chat_id(mess: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        try:
            settings = await postgres.get_settings()
            message_array = mess.text.split(" ")
            moder_chat_id = message_array[-1]
            if moder_chat_id.lstrip("-").isdigit():
                if int(moder_chat_id) == settings.moder_chat_id:
                    await mess.answer(f'Это и так чат модераторов', parse_mode="HTML",
                                      reply=mess.message_id)
                else:
                    settings.moder_chat_id = int(moder_chat_id)
                    mess = await bot.send_message(chat_id=settings.moder_chat_id, text="new dashboard")
                    settings.dashboard_message_id = mess.message_id
                    await settings.update(moder_chat_id = int(moder_chat_id), dashboard_message_id = mess.message_id).apply()
                    await mess.answer(f'Чат модераторов изменен, новые валентинки будут приходить туда', parse_mode="HTML",
                                      reply=mess.message_id)

            else:
                await mess.answer("Формат команды <code>/change_moder_chat_id chat_id</code>", reply=mess.message_id,
                                  parse_mode="HTML")
        except RetryAfter as e:
            print(e)




async def admin_menu(call: types.CallbackQuery, id, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        try:
            await bot.answer_callback_query(call.id)
            letter = await postgres.get_letter(int(id))
            keyboard = await check_markup(letter)
            await call.message.edit_text(text=await get_admin_message_text(letter), reply_markup=keyboard)
            try:
                state = Dispatcher.get_current().current_state()
                await state.reset_state()
            except:
                pass
        except RetryAfter as e:
            print(e)
            await call.answer(text="Флуд Бан, нажми через несколько секунд")

@dp.message_handler(commands=["users"], state="*")
async def db_users_list(message: Union[types.Message, types.CallbackQuery], extra_data=0, **kwargs):
    if await default_check(user=types.User.get_current(), admin=True):
        user_in_db = await postgres.get_user_by_tg_id(types.User.get_current().id)
        i = int(extra_data)
        users_count = await postgres.count_users()
        if type(message) == types.Message:

            markup = await keyboards.users_list_keyboard(i, user_in_db)
            await message.answer(reply_markup=markup, text=f"{users_count} users:")
        else:
            markup = await keyboards.users_list_keyboard(i, user_in_db)
            try:
                await message.message.edit_text(reply_markup=markup, text=f"{users_count} users:")
            except:
                pass

async def db_user_info(message: Union[types.Message, types.CallbackQuery], id=0, extra_data=0, **kwargs):
    if await default_check(types.User.get_current(), admin=True):

        user_in_db : models.User= await postgres.get_user_by_tg_id(int(id))
        text = await get_user_info(user_in_db)
        markup = await keyboards.users_info_keyboard(i=int(extra_data), item_id=int(id), user= user_in_db)
        if type(message) == types.Message:

            await message.answer(reply_markup=markup, text=text, disable_web_page_preview=True)
        else:
            try:
                await message.message.edit_text(reply_markup=markup, text=text, disable_web_page_preview=True)
            except:
                await message.message.delete()
                await message.message.answer(reply_markup=markup, text=text, disable_web_page_preview=True)


async def db_user_block(message: types.CallbackQuery, id=0, extra_data=0, **kwargs):
    if await default_check(types.User.get_current(), admin=True):

        user_in_db : models.User= await postgres.get_user_by_tg_id(int(id))

        await user_in_db.update(is_blocked_by_bot = not user_in_db.is_blocked_by_bot).apply()
        text = await get_user_info(user_in_db)
        markup = await keyboards.users_info_keyboard(i=int(extra_data), item_id=int(id), user= user_in_db)
        try:
            await message.message.edit_text(reply_markup=markup, text=text, disable_web_page_preview=True)
        except:
            await message.message.delete()
            await message.message.answer(reply_markup=markup, text=text, disable_web_page_preview=True)

async def db_user_admin(message: types.CallbackQuery, id=0, extra_data=0, **kwargs):
    if await default_check(types.User.get_current(), admin=True):

        user_in_db : models.User= await postgres.get_user_by_tg_id(int(id))

        await user_in_db.update(is_admin = not user_in_db.is_admin).apply()
        await set_personal_bot_commands(user_in_db.id)
        text = await get_user_info(user_in_db)
        markup = await keyboards.users_info_keyboard(i=int(extra_data), item_id=int(id), user= user_in_db)
        try:
            await message.message.edit_text(reply_markup=markup, text=text, disable_web_page_preview=True)
        except:
            await message.message.delete()
            await message.message.answer(reply_markup=markup, text=text, disable_web_page_preview=True)

async def db_user_online(message: types.CallbackQuery, id=0, extra_data=0, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        user_in_db : models.User= await postgres.get_user_by_tg_id(int(id))
        await user_in_db.update(is_online = not user_in_db.is_online).apply()
        text = await get_user_info(user_in_db)
        markup = await keyboards.users_info_keyboard(i=int(extra_data), item_id=int(id), user= user_in_db)
        try:
            await message.message.edit_text(reply_markup=markup, text=text, disable_web_page_preview=True)
        except:
            await message.message.delete()
            await message.message.answer(reply_markup=markup, text=text, disable_web_page_preview=True)


async def db_user_receive_letters(message: types.CallbackQuery, id=0, extra_data=0, **kwargs):
    if await default_check(types.User.get_current(), admin=True):
        user_in_db : models.User= await postgres.get_user_by_tg_id(int(id))
        await user_in_db.update(is_receive_letters = not user_in_db.is_receive_letters).apply()
        text = await get_user_info(user_in_db)
        markup = await keyboards.users_info_keyboard(i=int(extra_data), item_id=int(id), user= user_in_db)
        try:
            await message.message.edit_text(reply_markup=markup, text=text, disable_web_page_preview=True)
        except:
            await message.message.delete()
            await message.message.answer(reply_markup=markup, text=text, disable_web_page_preview=True)


async def get_user_info(user_in_db):
    text = '<a href="tg://user?id=' + str(user_in_db.tg_id) + '">' + str(user_in_db.fullname) + '</a>\n\n'
    if user_in_db.username != None:
        text += 'Username: @' + user_in_db.username + '\n'
    else:
        text += 'No username\n'
    text += "Telegram id: " + str(user_in_db.tg_id) + "\nId: " + str(user_in_db.id)
    text += f"\nLanguage: {user_in_db.language}"
    text += f"\nIs receive letters: {user_in_db.is_receive_letters}\nIs blocked by bot: {user_in_db.is_blocked_by_bot}\n" \
            f"Is bot blocked: {user_in_db.is_bot_blocked}\nAdmin: {user_in_db.is_admin}"
    if user_in_db.is_admin:
        text += f"\nOnline: {user_in_db.is_online}"
    sent_letters = await postgres.count_sent_letters_of_user(user_in_db.tg_id)
    sent_answers = await postgres.count_sent_answers_of_user(user_in_db.tg_id)
    received_letters = await postgres.count_received_letters_of_user(user_in_db.tg_id)
    received_answers = await postgres.count_received_answers_of_user(user_in_db.tg_id)
    now = datetime.datetime.now(pytz.timezone('Europe/Kiev'))
    text += f"\n\nSent letters: {sent_letters}\nReceived letters: {received_letters}\nSent answers: {sent_answers}\nReceived answers: {received_answers}\n\nUpdated {await data_formatter(now)}"
    return text


@dp.callback_query_handler(menu_cd.filter(), state='*')
async def navigate(call: types.CallbackQuery, callback_data: dict):
    current_level = callback_data.get('level')
    id = callback_data.get('id')
    extra_data = callback_data.get('extra_data')
    levels = {
        '1': process_callback_button1,
        '2': process_callback_button2,
        '3': process_callback_button3,
        '4': add_contact,
        '5': initialisate_chat_with_user,
        '6': reject_letter,
        '7': admin_menu,
        '8': approve_letter,
        '9': add_photo_to_text,
        '10': remove_photo_from_text,
        '11': disable_preview,
        '12': enable_preview,
        '13': change_language,
        '14': close_language,
        '15': block_letter,
        '16': db_users_list,
        '17': db_user_info,
        '18': db_user_block,
        '19': db_user_admin,
        '20': db_user_online,
        '21': db_user_receive_letters,

    }

    current_level_function = levels[current_level]

    await current_level_function(
        call, id=id, extra_data=extra_data
    )

async def default_check(user, admin=False):
    user_in_DB: models.User = await postgres.get_user_by_tg_id(user.id)
    if user_in_DB:
        if not user_in_DB.is_bot_blocked and not user_in_DB.is_blocked_by_bot:
            if admin:
                if user_in_DB.is_admin:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False
    return False


'''@dp.message_handler(lambda msg: msg.from_user.id == data.userbot_id)
async def userbot_connect(message: types.Message):
    if await default_check(types.User.get_current(), admin=True):
        moder_chat_id = (await postgres.get_settings()).moder_chat_id
        if message.text.startswith("/#"):
            message_dict = message.text[2:].split(":")
            if message_dict[0] == "ls":
                # successfull delivery
                letter = await postgres.get_letter(int(message_dict[1]))

                letter.status = "DELIVERED"
                await letter.update(status="DELIVERED").apply()



                await bot.edit_message_text(chat_id=moder_chat_id, message_id=int(letter.admin_message_id),
                                            text=await get_admin_message_text(letter), parse_mode="HTML")
                await bot.send_message(chat_id=letter.sender_id,
                                       text=translates.successfull_letter_delivery,
                                       reply_to_message_id=letter.sender_message_id)
            elif message_dict[0] == "le":
                # error delivery
                letter = await postgres.get_letter(int(message_dict[1]))

                letter.status = "ERROR"
                await letter.update(status="ERROR").apply()



                await bot.edit_message_text(chat_id=moder_chat_id, message_id=int(letter.admin_message_id),
                                            text=await get_admin_message_text(letter), parse_mode="HTML")
                await bot.send_message(chat_id=letter.sender_id,
                                       text=translates.error_letter_delivery,
                                       reply_to_message_id=letter.sender_message_id)
            elif message_dict[0] == "a":
                answer = await postgres.get_answer(int(message_dict[1]))

                try:
                    if answer.type != "TEXT" and message.reply_to_message != None:
                        answer.file_id = await postgres.get_file_id(answer, message.reply_to_message)
                    await bot.send_message(chat_id=answer.recipient_id, text=translates.new_answer)
                    mess_id = await send_answer(answer=answer)
                    if mess_id == "error":
                        answer.status = "ERROR"
                        await answer.update(status="ERROR", file_id=answer.file_id).apply()
                        await bot.send_message(chat_id=data.userbot_id, text=f"/#ae:{answer.id}")
                    else:
                        answer.status = "DELIVERED"
                        answer.recipient_message_id = mess_id.message_id
                        await answer.update(status="DELIVERED", file_id=answer.file_id,
                                            recipient_message_id=answer.recipient_message_id).apply()
                        await bot.send_message(chat_id=data.userbot_id, text=f"/#as:{answer.id}")
                except:

                    answer.status = "ERROR"
                    await answer.update(status="ERROR").apply()
                    await bot.send_message(chat_id=data.userbot_id, text=f"/#ae:{answer.id}")
            elif message_dict[0] == "ae":
                # error delivery
                answer = await postgres.get_answer(int(message_dict[1]))
                await bot.send_message(chat_id=answer.sender_id,
                                       text=translates.error_answer_delivery,
                                       reply_to_message_id=answer.sender_message_id)
            elif message_dict[0] == "as":
                # successfull delivery
                answer = await postgres.get_answer(int(message_dict[1]))
                await bot.send_message(chat_id=answer.sender_id, text=translates.successfull_answer_delivery,
                                       reply_to_message_id=answer.sender_message_id)
            elif message_dict[0] == "ue":
                # error delivery
                letter = await postgres.get_letter(int(message_dict[1]))

                letter.status = "INQUEUE"
                await letter.update(status="INQUEUE").apply()

            elif message_dict[0] == "us":
                # successfull delivery
                letter = await postgres.get_letter(int(message_dict[1]))
                letter.status = "INQUEUE"
                await letter.update(status="INQUEUE").apply()


'''
async def set_personal_bot_commands(user_id):
    user = await postgres.get_user(user_id)
    if user and not user.is_admin:
        commands = [BotCommand(command="new", description=_(translates.new_command)),
                            BotCommand(command="receive_letters", description=_(translates.receive_letters_command)),
                            BotCommand(command="not_receive_letters",
                                       description=_(translates.not_receive_letters_command)),
                            BotCommand(command="language", description=_(translates.language_command)),
                            #BotCommand(command="help", description=_(translates.help_command)),
                            BotCommand(command="start", description=_(translates.start_command)),
                            ]
    else:
        commands = [BotCommand(command="online", description=_(translates.online_command)),
                               BotCommand(command="offline", description=_(translates.offline_command)),

                               BotCommand(command="queue_scan_timer", description=_(translates.queue_scan_timer_command)),
                               BotCommand(command="dashboard_scan_timer",
                                          description=_(translates.dashboard_scan_timer_command)),
                               BotCommand(command="add_admin", description=_(translates.add_admin_command)),
                               BotCommand(command="del_admin", description=_(translates.del_admin_command)),
                               BotCommand(command="test_letter", description=_(translates.test_letter_command)),
                               BotCommand(command="start_queue", description=_(translates.start_queue_command)),
                               BotCommand(command="stop_queue", description=_(translates.stop_queue_command)),
                                BotCommand(command="users", description=_(translates.users_command)),
                               BotCommand(command="new", description=_(translates.new_command)),
                               BotCommand(command="receive_letters", description=_(translates.receive_letters_command)),
                               BotCommand(command="not_receive_letters",
                                          description=_(translates.not_receive_letters_command)),
                               BotCommand(command="language", description=_(translates.language_command)),
                               #BotCommand(command="help", description=_(translates.help_command)),
                               BotCommand(command="start", description=_(translates.start_command)),
                               ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeChat(user.tg_id))

async def set_bot_commands():
    commands_default = [BotCommand(command="new", description=_(translates.new_command)),
                        BotCommand(command="receive_letters", description=_(translates.receive_letters_command)),
                        BotCommand(command="not_receive_letters", description=_(translates.not_receive_letters_command)),
                        BotCommand(command="language", description=_(translates.language_command)),
                        #BotCommand(command="help", description=_(translates.help_command)),
                        BotCommand(command="start", description=_(translates.start_command)),
                ]


    await bot.set_my_commands(commands=commands_default, scope=BotCommandScopeDefault())


async def dashboard():

    users_size = await postgres.count_users()
    bot_blocked_users = await postgres.count_bot_blocked_users()
    blocked_by_bot_users = await postgres.count_blocked_by_bot_users()
    receive_letters_users = await postgres.receive_letters_users()
    online_admins = await postgres.count_online_admins()
    admin_users = await postgres.count_admin_users()
    letters_size = await postgres.count_letters()
    answers_size = await postgres.count_answers()
    delivered_letters = await postgres.count_delivered_letters()
    queue_letters = await postgres.count_queue_letters()

    error_letters = await postgres.count_error_letters()
    creating_letters = await postgres.count_creating_letters()
    checking_letters = await postgres.count_checking_letters()
    rejected_letters = await postgres.count_rejected_letters()

    error_answers = await postgres.count_error_answers()
    delivered_answers = await postgres.count_delivered_answers()
    settings = await postgres.get_settings()
    main_admin = await postgres.get_user_by_tg_id(settings.main_admin_id)
    now = datetime.datetime.now(pytz.timezone('Europe/Kiev'))

    text=f"Users: {users_size}\nLetters receivers: {receive_letters_users}\nBlocked bot: {bot_blocked_users}\nBlocked by bot: {blocked_by_bot_users}\nOnline admins: {online_admins}\nAdmins: {admin_users}\n\n" \
         f"Letters: {letters_size}\nIn queue: {queue_letters}\nDelivered: {delivered_letters}\nIn checking: {checking_letters}\nIn creating: {creating_letters}\n" \
         f"Error delivery: {error_letters}\nRejected: {rejected_letters}\n\n" \
         f"Answers: {answers_size}\nDelivered: {delivered_answers}\nError: {error_answers}\n\n" \
         f"Is check queue: {settings.is_send_to_moders}\nQueue scan timer: {settings.queue_scan_timer}\nDashboard scan timer: {settings.dashboard_scan_timer}\n" \
         f"Letters checking in one chat: {settings.checking_letters_in_one_chat}\n" \
         f"Main admin: <a href='tg://user?id={str(main_admin.tg_id)}'>{str(main_admin.fullname)}</a>\n\nUpdated {await data_formatter(now)}"

    try:

        await bot.edit_message_text(chat_id=settings.dashboard_message_chat, message_id=settings.dashboard_message_id, text=text)
    except AttributeError as e:
        print("error dashboard:")
        print(e)
        settings = await postgres.get_settings()
        mess =await bot.send_message(chat_id=settings.dashboard_message_chat, text=text)
        with open("data.py", 'a') as f:
            f.write(f'\ndashboard_message_id = {mess.message_id}')
            f.close()
            await bot.send_message(chat_id=settings.dashboard_message_chat, text="Файл data перезаписан, перезапусти бота")
            sys.exit()
    except MessageNotModified as e:
        pass
    except MessageIdentifierNotSpecified as e:
        print(e)
    except MessageToEditNotFound as e:
        print(e)
        mess =await bot.send_message(chat_id=settings.dashboard_message_chat,
                                    text=text)
        await settings.update(dashboard_message_id = mess.message_id).apply()


async def data_formatter(now):


    if len(str(now.hour))==1:
        hour=f"0{now.hour}"
    else:
        hour = f"{now.hour}"
    if len(str(now.minute))==1:
        minute=f"0{now.minute}"
    else:
        minute = f"{now.minute}"
    if len(str(now.second))==1:
        second=f"0{now.second}"
    else:
        second = f"{now.second}"
    if len(str(now.day))==1:
        day=f"0{now.day}"
    else:
        day = f"{now.day}"
    if len(str(now.month))==1:
        month=f"0{now.month}"
    else:
        month = f"{now.month}"
    return f"{hour}:{minute}:{second} {day}.{month}.{now.year}"

async def send_letter(letter, chat_id=None):
    if not chat_id:
        chat_id = letter.recipient_id
    message = None
    if letter.type == "TEXT":
        message = await bot.send_message(chat_id=chat_id, text=letter.text, parse_mode="HTML", disable_web_page_preview=not letter.link_preview)
    elif letter.type == "STICKER":
        message = await bot.send_sticker(chat_id=chat_id, sticker=letter.file_id)
    elif letter.type == "PHOTO":
        message = await bot.send_photo(chat_id=chat_id, photo=letter.file_id, caption=letter.text, parse_mode="HTML")
    elif letter.type == "VIDEO":
        message = await bot.send_video(chat_id=chat_id, video=letter.file_id, caption=letter.text, parse_mode="HTML")
    elif letter.type == "VOICE":
        message = await bot.send_voice(chat_id=chat_id, voice=letter.file_id)
    elif letter.type == "VIDEO_NOTE":
        message = await bot.send_video_note(chat_id=chat_id, video_note=letter.file_id)
    elif letter.type == "ANIMATION":
        message = await bot.send_animation(chat_id=chat_id, animation=letter.file_id)
    elif letter.type == "AUDIO":
        message = await bot.send_audio(chat_id=chat_id, audio=letter.file_id)
    return message

async def send_answer(answer, chat_id = None, reply = True):

    try:
        if chat_id == None:
            chat_id = answer.recipient_id
        if not reply:
            answer.to_message_recipient = None
        message = None
        if answer.type == "TEXT":
            message = await bot.send_message(chat_id=chat_id, text=answer.text, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "STICKER":
            message = await bot.send_sticker(chat_id=chat_id, sticker=answer.file_id, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "PHOTO":
            message = await bot.send_photo(chat_id=chat_id, photo=answer.file_id, caption=answer.text, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "VIDEO":
            message = await bot.send_video(chat_id=chat_id, video=answer.file_id, caption=answer.text, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "VOICE":
            message = await bot.send_voice(chat_id=chat_id, voice=answer.file_id, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "VIDEO_NOTE":
            message = await bot.send_video_note(chat_id=chat_id, video_note=answer.file_id, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "ANIMATION":
            message = await bot.send_animation(chat_id=chat_id, animation=answer.file_id, caption=answer.text, reply_to_message_id=answer.to_message_recipient)
        elif answer.type == "AUDIO":
            message = await bot.send_audio(chat_id=chat_id, audio=answer.file_id, reply_to_message_id=answer.to_message_recipient)
        return message
    except Exception as e:
        print(e)
        return "error"


