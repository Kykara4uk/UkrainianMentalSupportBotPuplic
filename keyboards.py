from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import types
from aiogram.utils.callback_data import CallbackData
import models
import postgres
import translates
from variables import _
menu_cd = CallbackData("show_menu", "level", "id", "extra_data")

def make_callback_data(level, id=0, extra_data=0):
    return menu_cd.new(level=level, id=id, extra_data=extra_data)

async def reject_keyboard(letter, user):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.row(InlineKeyboardButton(text=_('Do not reject', locale=user.language), callback_data=make_callback_data(level=7, id=letter.id)))

    return keyboard

async def block_keyboard(letter, user):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.row(InlineKeyboardButton(text=_('Do not block', locale=user.language), callback_data=make_callback_data(level=7, id=letter.id)))

    return keyboard

async def is_receive_letters_keyboard(user):
    keyboard = InlineKeyboardMarkup(row_width=1)
    if user.is_receive_letters:
        keyboard.row(InlineKeyboardButton(text=_('Not receive letters', locale=user.language), callback_data=make_callback_data(level=7, id=user.id)))
    else:
        keyboard.row(InlineKeyboardButton(text=_('Receive letters', locale=user.language), callback_data=make_callback_data(level=7, id=user.id)))

    return keyboard

async def add_contact_keyboard(letter):
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.row(InlineKeyboardButton(text=_('Back'), callback_data=make_callback_data(level=7, id=letter.id)))

    return keyboard

async def language_keyboard(user, current_locale, ru_level=2):
    keyboard = InlineKeyboardMarkup(row_width=2)
    if current_locale == 0:
        keyboard.row(InlineKeyboardButton(text='🇺🇦Українська✅', callback_data=make_callback_data(level=13, id=user.id, extra_data=0)))
        keyboard.row(InlineKeyboardButton(text='🇺🇸English', callback_data=make_callback_data(level=13, id=user.id, extra_data=1)))
        keyboard.row(InlineKeyboardButton(text='🇷🇺Русский', callback_data=make_callback_data(level=13, id=user.id, extra_data=ru_level)))

    else:
        keyboard.row(InlineKeyboardButton(text='🇺🇦Українська',
                                          callback_data=make_callback_data(level=13, id=user.id, extra_data=0)))
        keyboard.row(InlineKeyboardButton(text='🇺🇸English✅',
                                          callback_data=make_callback_data(level=13, id=user.id, extra_data=1)))
        keyboard.row(InlineKeyboardButton(text='🇷🇺Русский',
                                          callback_data=make_callback_data(level=13, id=user.id, extra_data=ru_level)))

    keyboard.row(InlineKeyboardButton(text=_(translates.close, locale=user.language), callback_data=make_callback_data(level=14)))

    return keyboard

async def is_correct_keyboard(letter, letter_preview_id, user):
    keyboard = InlineKeyboardMarkup(row_width=1)

    keyboard.row(types.InlineKeyboardButton(text=_(translates.button_change_content, locale=user.language), callback_data=make_callback_data(level=2, id=letter.id)))

    if letter.type == "TEXT":
        if '>&#8288;</a>' in letter.text:
            keyboard.row(InlineKeyboardButton(text=_(translates.button_del_photo, locale=user.language), callback_data=make_callback_data(level=10, id=letter.id, extra_data=letter_preview_id)))
        else:
            keyboard.row(InlineKeyboardButton(text=_(translates.button_add_photo, locale=user.language), callback_data=make_callback_data(level=9, id=letter.id, extra_data=letter_preview_id)))
            if letter.link_preview == True and "a href=" in letter.text:

                keyboard.row(InlineKeyboardButton(text=_(translates.button_disable_preview, locale=user.language), callback_data=make_callback_data(level=11, id=letter.id, extra_data=letter_preview_id)))
            elif letter.link_preview == False and "a href=" in letter.text:

                keyboard.row(InlineKeyboardButton(text=_(translates.button_enable_preview, locale=user.language), callback_data=make_callback_data(level=12, id=letter.id, extra_data=letter_preview_id)))
    keyboard.row(types.InlineKeyboardButton(text=_(translates.button_send_to_admins, locale=user.language), callback_data=make_callback_data(level=3, id=letter.id)))


    return keyboard

async def check_markup(letter: models.Letter, is_userbot_can_write_to_user_by_id=False):
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton(text="Прийняти", callback_data=make_callback_data(level=8, id=letter.id)))


    markup.row(InlineKeyboardButton(text="Відхилити", callback_data=make_callback_data(level=6, id=letter.id)))
    markup.row(InlineKeyboardButton(text="Заблокувати користувача", callback_data=make_callback_data(level=15, id=letter.id)))
    return markup

async def delivery_confirm_markup(letter: models.Letter):
    markup = InlineKeyboardMarkup()


    markup.row(InlineKeyboardButton(text="Отправить валентинку", callback_data=make_callback_data(level=8, id=letter.id, extra_data=1)))


    markup.row(InlineKeyboardButton(text="Назад", callback_data=make_callback_data(level=7, id=letter.id)))
    return markup

async def users_list_keyboard(i, user):
    markup = InlineKeyboardMarkup(row_width=1)
    users = await postgres.get_all_users()
    users.sort(key=lambda x: x.id)
    users_small = users[10*int(i):10*int(i)+10]
    for j in range (len(users_small)):
        button_text = f"{users_small[int(j)].fullname}"
        callback_data = make_callback_data(level=17, id=users_small[int(j)].tg_id, extra_data=i)

        markup.insert(InlineKeyboardMarkup(text=button_text, callback_data=callback_data))
    caption = f"{int(i)+1}/{(len(users)//10) + 1}"
    size = len(users) - 1
    if int(i) + 1 > (size//10):
        i1 = 0
    else:
        i1 = int(i) + 1
    if int(i) - 1 < 0:
        i2 = (size//10)
    else:
        i2 = int(i) - 1
    markup.row(InlineKeyboardButton(text="◀️", callback_data=make_callback_data(level=16, extra_data=i2)),
               InlineKeyboardButton(text=caption, callback_data=make_callback_data(level=16, extra_data=i)),
               InlineKeyboardButton(text="▶️", callback_data=make_callback_data(level=16, extra_data=i1)))
    markup.row(InlineKeyboardButton(text=_(translates.close, locale=user.language), callback_data=make_callback_data(level=14)))
    return markup

async def users_info_keyboard(i, item_id, user):
    markup = InlineKeyboardMarkup(row_width=1)
    if user.is_blocked_by_bot:
        markup.row(
        InlineKeyboardButton(text="Разблокувати", callback_data=make_callback_data(level=18, id=item_id, extra_data=i)))
    else:
        markup.row(
            InlineKeyboardButton(text="Заблокувати",
                                 callback_data=make_callback_data(level=18, id=item_id, extra_data=i)))
    if user.is_receive_letters:
        markup.row(
        InlineKeyboardButton(text="Не отримувати листи", callback_data=make_callback_data(level=21, id=item_id, extra_data=i)))
    else:
        markup.row(
            InlineKeyboardButton(text="Отримувати листи",
                                 callback_data=make_callback_data(level=21, id=item_id, extra_data=i)))
    if user.is_admin:
        markup.row(
        InlineKeyboardButton(text="Видалити з адмінів", callback_data=make_callback_data(level=19, id=item_id, extra_data=i)))
    else:
        markup.row(
            InlineKeyboardButton(text="Зробити адміном",
                                 callback_data=make_callback_data(level=19, id=item_id, extra_data=i)))
    if user.is_admin:
        if user.is_online:
            markup.row(
                InlineKeyboardButton(text="Зняти з лінії",
                                     callback_data=make_callback_data(level=20, id=item_id, extra_data=i)))
        else:
            markup.row(
                InlineKeyboardButton(text="Поставити на лінію",
                                     callback_data=make_callback_data(level=20, id=item_id, extra_data=i)))
    markup.row(InlineKeyboardButton(text="Оновити", callback_data=make_callback_data(level=17, id=item_id, extra_data=i)))
    markup.row(InlineKeyboardButton(text="« Назад", callback_data=make_callback_data(level=16, extra_data=i)))
    return markup