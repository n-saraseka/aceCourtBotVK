from api_and_stuff import vk_session, vk_user_session, current_dir, Chat
from vk_api import ApiError
from vk_methods import sender
from render_messages import bot_render
import shutil
import os
import base64
import logging
import math

def chat_worker(id, msg, from_chat):
    chat = Chat.get_or_none(Chat.id == id)
    if chat==None:
        chat = Chat.create(id = id, message_received = True, bot_notifications = True, kicked=False, from_chat = True)
        chat.save()
        sender(id, 'Теперь беседа подписана на оповещения о включении и отключении бота.', from_chat)
    else:
        chat.kicked = False
        chat.save()
    
    if msg['text'].startswith('[club204496105'):
        if 'суд' in msg['text'].lower().split() or ('сус' in msg['text'].lower().split() and 'суд' not in msg['text'].lower().split()):
            messages = vk_session.method('messages.getByConversationMessageId', {'peer_id': msg['peer_id'], 'conversation_message_ids': msg['conversation_message_id'], 'extended': 1})
            if 'reply_message' in messages['items'][0].keys():
                messages = [messages['items'][0]['reply_message']]
            elif len(messages['items'][0]['attachments'])>0 and messages['items'][0]['attachments'][0]['type']=='wall_reply':
                messages = [messages['items'][0]['attachments'][0]['wall_reply']]
                try:
                    temp = messages
                    temp_count = temp[0]['thread']['count']
                    i = 0
                    while temp_count-len(messages)+1>0:
                        messages = messages + vk_user_session.method('wall.getComments', {'owner_id': temp[0]['owner_id'], 'post_id': temp[0]['post_id'], 'comment_id': temp[0]['id'], 'offset': i*100-1*(i//1), 'count': 100})['items']
                        i+=1
                except ApiError:
                    messages = []
            else:
                messages = messages['items'][0]['fwd_messages']
            if len(messages)>0:
                logging.info(f'Video is being rendered. CHAT_ID: {id}')
                name = base64.b64encode(os.urandom(16)).decode('ascii').replace('/', '').replace('=', '').replace('+', '')
                try:
                    bot_render(msg, id, name, from_chat)
                except ApiError:
                    chat = Chat.get_or_none(Chat.id == id)
                    chat.kicked == True
                    chat.save()
                    if os.path.exists(f'{name}.mp4'):
                        os.remove(f'{name}.mp4')
                    if os.path.exists(f'{name}.mp4.audio.mp3'):
                        os.remove(f'{name}.mp4.audio.mp3')
                    if os.path.exists(f'{name}.mp4.txt'):
                        os.remove(f'{name}.mp4.txt')
                    if os.path.exists(name):
                        shutil.rmtree(name)
        elif 'помощь' in msg['text'].lower().split():
            try:
                if '-m' in msg['text'].lower().split():
                    sender(id, "PWR — Phoenix Wright: Ace Attorney\nJFA — Phoenix Wright: Ace Attorney — Justice For All\nT&T — Phoenix Wright: Ace Attorney — Trials and Tribulations\nAAI — Ace Attorney Investigations: Miles Edgeworth\nAAI2 — Ace Attorney Investigations: Miles Edgeworth 2\nAJ — Apollo Justice: Ace Attorney\nDD — Phoenix Wright: Ace Attorney — Dual Destinies\nSOJ — Phoenix Wright: Ace Attorney — Spirit of Justice\nRND — случайное аудио, стоит по умолчанию.", from_chat)
                else:
                    sender(id, "Видео:\nсуд — создание видео.\n-ig — выбор персонажей с игнорированием пола пользователей.\n-m — выбор OST'а по коду. Коды для данной команды вы можете получить по команде '@acecourtbotvk помощь -m'.\nОповещения:\nотключить оповещения - отписаться от оповещений о включении и отключении бота.\nвключить оповещения - подписаться на оповещения о включении и отключении бота.", from_chat)
                    logging.info(f'"Help" command executed. CHAT_ID: {id}')
            except ApiError:
                    chat = Chat.get_or_none(Chat.id == id)
                    chat.kicked == True
                    chat.save()
        elif 'отключить оповещения' in msg['text'].lower():
            try:
                if chat.bot_notifications == True:
                    chat = Chat.get(Chat.id == id)
                    chat.bot_notifications = False
                    chat.save() 
                    sender(id, 'Беседа отписана от оповещений о включении и отключении бота. Судья будет скучать!', from_chat)
                else:
                    sender(id, 'Вы уже отписаны от оповещений о включении бота. Не делайте глупостей в суде!', from_chat)
            except ApiError:
                    chat = Chat.get_or_none(Chat.id == id)
                    chat.kicked == True
                    chat.save()
        elif 'включить оповещения' in msg['text'].lower():
            try:
                chat = Chat.get(Chat.id == id)
                if chat.bot_notifications == False:
                    chat.bot_notifications = True
                    chat.save()
                    sender(id, 'Теперь беседа подписана на оповещения о включении и отключении бота.', from_chat)
                else:
                    sender(id, 'Вы уже подписаны на оповещения о включении бота. Не делайте глупостей в суде!', from_chat)
            except ApiError:
                    chat = Chat.get_or_none(Chat.id == id)
                    chat.kicked == True
                    chat.save()