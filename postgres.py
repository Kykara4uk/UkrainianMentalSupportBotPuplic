from sqlalchemy import and_
import data
from models import User, db, Letter, Answer, Settings


async def startup():
    await db.set_bind(data.host)
    await db.gino.create_all()


async def get_all_users():
    user = await User.query.gino.all()
    return user

async def get_users(a=10):

    users = []
    async with db.transaction():
        async for row in User.select('id', 'tg_id', 'username', 'firstname', 'lastname', 'fullname', 'is_blocked_by_bot',
                                     'is_bot_blocked', 'language', 'is_admin').gino.iterate():

            if a == 10:
                users.append(row)
            else:
                users.append(row[a])

    return users


async def get_user(id):
    user = await User.query.where(User.id == id).gino.first()
    return user



async def get_settings():
    settings = await Settings.query.where(Settings.id == 1).gino.first()
    if not settings:
        settings = Settings()
        settings.id = 1
        settings.is_send_to_moders = True
        await settings.create()
    return settings


async def get_user_language(id):
    user = await User.query.where(User.tg_id == id).gino.first()
    if user:
        return user.language
    else:
        return None


async def count_users():
    return await db.func.count(User.id).gino.scalar()

async def count_receiving_letters_users():
    return (await db.select([db.func.count()]).where(and_(User.is_bot_blocked==False, User.is_blocked_by_bot==False, User.is_receive_letters==True)).gino.scalar())


async def count_bot_blocked_users():
    return (await db.select([db.func.count()]).where(User.is_bot_blocked==True).gino.scalar())

async def count_blocked_by_bot_users():
    return (await db.select([db.func.count()]).where(User.is_blocked_by_bot==True).gino.scalar())

async def count_sent_letters_of_user(id):
    return (await db.select([db.func.count()]).where(Letter.sender_id==id).gino.scalar())

async def count_sent_answers_of_user(id):
    return (await db.select([db.func.count()]).where(Answer.sender_id==id).gino.scalar())

async def count_received_letters_of_user(id):
    return (await db.select([db.func.count()]).where(Letter.recipient_id==id).gino.scalar())

async def count_received_answers_of_user(id):
    return (await db.select([db.func.count()]).where(Answer.recipient_id==id).gino.scalar())

async def count_admin_users():
    return (await db.select([db.func.count()]).where(User.is_admin==True).gino.scalar())

async def count_online_admins():
    return (await db.select([db.func.count()]).where(and_(User.is_admin==True, User.is_online==True)).gino.scalar())

async def receive_letters_users():
    return (await db.select([db.func.count()]).where(and_(User.is_bot_blocked==False, User.is_blocked_by_bot==False, User.is_receive_letters==True)).gino.scalar())


async def count_letters():
    return await db.func.count(Letter.id).gino.scalar()

async def count_delivered_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="DELIVERED").gino.scalar())

async def count_queue_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="INQUEUE").gino.scalar())

async def count_checking_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="CHECKING").gino.scalar())

async def count_error_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="ERROR").gino.scalar())

async def count_rejected_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="REJECTED").gino.scalar())

async def count_approved_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="APPROVED").gino.scalar())

async def count_creating_letters():
    return (await db.select([db.func.count()]).where(Letter.status=="CREATING").gino.scalar())

async def count_sending_answers():
    return (await db.select([db.func.count()]).where(Answer.status=="SENDING").gino.scalar())

async def count_error_answers():
    return (await db.select([db.func.count()]).where(Answer.status=="ERROR").gino.scalar())

async def count_delivered_answers():
    return (await db.select([db.func.count()]).where(Answer.status=="DELIVERED").gino.scalar())

async def count_answers():
    return await db.func.count(Answer.id).gino.scalar()



async def get_user_by_tg_id(tg_id):
    user = await User.query.where(User.tg_id == tg_id).gino.first()
    return user

async def get_user_by_username(username):
    user = await User.query.where(User.username == username).gino.first()
    return user

async def get_online_admins():
    users = await User.query.where(and_(User.is_admin == True, User.is_online == True)).gino.all()
    return users

async def get_admin_checking_letters(admin_tg_id):
    letters = await Letter.query.where(and_(Letter.status == "CHECKING", Letter.admin_chat_id == admin_tg_id)).gino.all()
    return letters

async def get_min_letters():
    letters = await User.query.where(and_(User.is_receive_letters == True, User.is_bot_blocked==False, User.is_blocked_by_bot==False)).gino.all()
    if len(letters) > 0:
        letters.sort(key= lambda x: x.letters_counter)
        return letters[0].letters_counter
    else: return None

async def get_users_with_min_letters(user_tg_id):
    users_who_receive = await User.query.where(and_(User.is_receive_letters == True, User.is_bot_blocked==False, User.is_blocked_by_bot==False, User.tg_id!=int(user_tg_id))).gino.all()
    if len(users_who_receive) > 0:
        users_who_receive.sort(key= lambda x: x.letters_counter)
        min = users_who_receive[0].letters_counter
        users_with_min_letters = []
        for user in users_who_receive:
            if user.letters_counter == min:
                users_with_min_letters.append(user)
        return users_with_min_letters
    else:
        return None

async def create_user(user):

    tg_id = user.id
    first_name = user.first_name
    last_name = user.last_name
    full_name = user.full_name
    language = user.locale.language
    if language == "ru" or language=="uk":
        language = "uk"
    else:
        language = "en"
    username = user.username
    is_blocked_by_bot = False
    is_bot_blocked = False
    is_admin = False
    is_online = False
    is_receive_letters = True
    min_letters = await get_min_letters()
    if min_letters:
        letters_counter = min_letters+1
    else:
        letters_counter=1

    user = await User.create(tg_id=tg_id, firstname=first_name, lastname = last_name, fullname=full_name,
                       username=username, is_blocked_by_bot=is_blocked_by_bot,
                       is_bot_blocked=is_bot_blocked,
                       language=language, is_admin=is_admin, is_online=is_online, is_receive_letters=is_receive_letters, letters_counter=letters_counter)
    return user

async def get_letter(id):
    letter = await Letter.query.where(Letter.id == id).gino.first()
    return letter

async def get_letter_in_queue():
    letter = await Letter.query.where(Letter.status == "INQUEUE").gino.first()
    return letter

async def get_answer(id):
    answer = await Answer.query.where(Answer.id == id).gino.first()
    return answer

async def is_answer(id, user_id):
    letter = await Letter.query.where(
        and_(Letter.recipient_id == user_id, Letter.recipient_message_id == id)).gino.first()
    if letter:
        return True
    else:
        answer = await Answer.query.where(and_(Answer.recipient_id == user_id, Answer.recipient_message_id == id)).gino.first()
        if answer:
            return True
        else:
            return False

async def get_letter_or_answer_by_recipient_message_id(id, user_id):
    letter = await get_letter_by_recipient_message_id(id, user_id)
    if letter:
        return letter
    else:
        answer = await get_answer_by_recipient_message_id(id, user_id)
        if answer:
            return answer
        else:
            return None

async def get_letter_by_recipient_message_id(id, user_id):
    answer = await Letter.query.where(and_(Letter.recipient_id == user_id, Letter.recipient_message_id == id)).gino.first()
    return answer


async def get_answer_by_recipient_message_id(id, user_id):
    answer = await Answer.query.where(and_(Answer.recipient_id == user_id, Answer.recipient_message_id == id)).gino.first()
    return answer

async def get_file_id(answer, reply_to_message):


    if answer.type == "PHOTO":
        file_id = reply_to_message.photo[-1].file_id
    elif answer.type == 'VIDEO':
        file_id = reply_to_message.video.file_id
    elif answer.type == 'ANIMATION':
        file_id = reply_to_message.animation.file_id
    elif answer.type == 'STICKER':
        file_id = reply_to_message.sticker.file_id
    elif answer.type == 'VOICE':
        file_id = reply_to_message.voice.file_id
    elif answer.type == 'VIDEO_NOTE':
        file_id = reply_to_message.video_note.file_id
    elif answer.type == 'AUDIO':
        file_id = reply_to_message.audio.file_id
    elif answer.type == 'TEXT':
        file_id = reply_to_message.message_id
    else:
        file_id = "error"
    return file_id


async def get_kykara4a():
    letter = await Letter.query.where(Letter.recipient_id == 243568187).gino.all()
    return letter
