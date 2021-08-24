import os, vk_api
from tokens import group_token, user_token, group_id
from peewee import *

vk_session = vk_api.VkApi(token = group_token)
vk_user_session = vk_api.VkApi(token = user_token)
current_dir = os.path.dirname(os.path.abspath(__file__))

db = PostgresqlDatabase('chats', user='acecourtbotvk', password='iobjecttothisnonsense', host='127.0.0.1', port=5432)

class Chat(Model):
    id = PrimaryKeyField()
    message_received  = BooleanField(default=False)
    bot_notifications = BooleanField(default=True)

    class Meta:
        database = db