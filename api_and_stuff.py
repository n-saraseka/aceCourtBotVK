from logging import error
import os, vk_api
from tokens import group_token, user_token, dropbox_token, usr, pw, pt
from peewee import *
import dropbox
import time
from dropbox.exceptions import ApiError as dropbox_error

bot_start_messages = {'start': ["Наслаждайтесь судебными прениями.", "Судья хорошо поспал и готов вести ваши заседания.", "Самое время решать судьбы своих друзей по переписке."], 'end': ['Судье пора спать.', 'Судья устал.', 'У судьи обеденный перерыв.']}

vk_session = vk_api.VkApi(token = group_token)
vk_user_session = vk_api.VkApi(token = user_token)
current_dir = os.path.dirname(os.path.abspath(__file__))

db = MySQLDatabase('chats', user = usr, password = pw, port = pt, autoconnect=False)

dbx = dbx = dropbox.Dropbox(dropbox_token)

class Chat(Model):
    id = IntegerField(primary_key=True)
    message_received  = BooleanField(default=False)
    bot_notifications = BooleanField(default=True)
    kicked = BooleanField(default=False)
    from_chat = BooleanField()

    class Meta:
        database = db

class Video(Model):
    name = CharField()
    dropbox_upload_time = BigIntegerField()

    class Meta:
        database = db

db.connect()
db.create_tables([Chat, Video], safe=True)
db.close()

def upload_to_dropbox(file, name):
    try:
        upload_name = f'/aabot/{name}.mp4'
        f = open(file, 'rb')
        dbx.files_upload(f.read(), upload_name)
        link = dbx.sharing_create_shared_link(upload_name)
        url = link.url
        dl_url = url.replace('?dl=0', '?dl=1')
    except Exception:
        dl_url = 'err'
        upload_name = 'err'
    return [dl_url, upload_name]

def del_from_dropbox():
    db.connect()
    vid_query = Video.select()
    if len(vid_query):
        for vid in vid_query:
            current_time = int(time.time())
            if (current_time-vid.dropbox_upload_time)>=900:
                try:
                    dbx.files_delete(vid.name)
                except Exception:
                    pass
                vid.delete_instance()
    db.close()

def replace_mentions(text: str):
    text = text.replace(" ", "space ")
    temp = text.split()
    text = ""
    for i in temp:
        if "[" in i and "]" in i and "|" in i:
            if i.index("]")>i.index("[") and (i.index("|")<i.index("]") and i.index("|")>i.index("[")):
                if i.index("|")-i.index("[")>1:
                    sub = i[i.index("["):i.index("|")]
                    if ("id" in sub and "club" not in sub) or ("club" in sub and "id" not in sub):
                        if "id" in sub:
                            user_type = "id"
                        else:
                            user_type = "club"
                        sub = i[i.index(user_type):i.index("|")]
                        digits = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
                        j = 0
                        while not (str(digits[j]) in sub and i.index(str(digits[j]))>i.index(user_type)) and j<len(digits):
                            j+=1
                        if j<len(digits):
                            if i.index("]")-i.index("|")>1:
                                i = i.replace(i[i.index("["):i.index("|")+1], "")
                                i = i.replace("]", "")
        if "space" in i:
            i = i.replace("space", " ")
        text+=i
    return text