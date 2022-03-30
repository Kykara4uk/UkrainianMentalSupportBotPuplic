from gino import Gino


db = Gino()

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, db.Sequence("user_id_seq"), primary_key=True)
    tg_id = db.Column(db.BigInteger)
    is_receive_letters = db.Column(db.Boolean)
    username = db.Column(db.String(200))
    firstname = db.Column(db.String(200))
    lastname = db.Column(db.String(200))
    fullname = db.Column(db.String(200))
    is_blocked_by_bot = db.Column(db.Boolean)
    is_bot_blocked = db.Column(db.Boolean)
    language = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean)
    is_online = db.Column(db.Boolean)
    letters_counter = db.Column(db.Integer)

    def __eq__(self, other):
        return self.tg_id == other.tg_id

class Letter(db.Model):
    __tablename__ = "letters"

    id = db.Column(db.Integer, db.Sequence("letters_id_seq"), primary_key=True)
    sender_id = db.Column(db.BigInteger)
    recipient_id = db.Column(db.BigInteger)
    status = db.Column(db.String)
    text = db.Column(db.String)
    type = db.Column(db.String)
    file_id = db.Column(db.String)
    sender_message_id = db.Column(db.Integer)
    recipient_message_id = db.Column(db.Integer)
    link_preview = db.Column(db.Boolean)
    reject_reason = db.Column(db.String)
    admin_message_id = db.Column(db.Integer)
    admin_chat_id = db.Column(db.BigInteger)


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, db.Sequence("answers_id_seq"), primary_key=True)
    sender_id = db.Column(db.BigInteger)
    recipient_id = db.Column(db.BigInteger)
    status = db.Column(db.String)
    text = db.Column(db.String)
    type = db.Column(db.String)
    sender_message_id = db.Column(db.Integer)
    recipient_message_id = db.Column(db.Integer)
    to_message_sender = db.Column(db.Integer)
    to_message_recipient = db.Column(db.Integer)
    file_id = db.Column(db.String)


class Settings(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, db.Sequence("settings_id_seq"), primary_key=True)

    dashboard_message_id = db.Column(db.BigInteger)
    is_check_queue =db.Column(db.Boolean)
    is_send_to_users =db.Column(db.Boolean)
    is_send_to_moders = db.Column(db.Boolean)
    checking_letters_in_one_chat = db.Column(db.Integer)
    dashboard_message_chat = db.Column(db.BigInteger)
    main_admin_id = db.Column(db.BigInteger)
    dashboard_scan_timer = db.Column(db.Integer)
    queue_scan_timer = db.Column(db.Integer)