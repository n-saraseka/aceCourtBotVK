import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from typing import List
import objection_engine
import os, shutil
import base64
import requests
import random
import signal
import json
from tokens import group_token, user_token, group_id
from vk_methods import sender, user_get, group_name_get
from api_and_stuff import vk_session, vk_user_session, current_dir, Chat, db
from render_messages import bot_render
from multiprocessing import Process, Queue
from peewee import *
import logging
import atexit
import time

longpoll = VkBotLongPoll(vk_session, group_id)
logging.basicConfig(filename='info.log', format='%(asctime)s - %(message)s', level=logging.INFO)


def render_video(msg, id, video_name):
    bot_render(msg, id, video_name)

def notify():
    while True:
        query = Chat.get_or_none(Chat.message_received == False and Chat.bot_notifications == True)
        if query is not None:
            print(query.message_received)
            if query.id == 5:
                sender(query.id, 'Бот запущен! Наслаждайтесь судебными прениями.')
                query.message_received = True    
                query.save()
                print(query.message_received)

def worker(queue, worker_id):
    while True:
        task = queue.get()
        id = task[0]
        msg = task[1]
        if list(msg.keys()).count('action')>0: 
            query = Chat.select().where(Chat.id == id)
            if (query.exists())==False:
                chat = Chat.create(id = id, message_received = True, bot_notifications = True)
                chat.save(force_insert=True)
            if msg['action']['type']=='chat_invite_user' and msg['action']['member_id']==group_id*(-1):
                logging.info(f'Bot added to chat. CHAT_ID: {id}')
                sender(id, 'Добрый день, господа юристы! Я — бот, создающий сцены в стиле Ace Attorney.\nПерешлите мне переписку с командой "@acecourtbotvk суд" и я создам с ней видео.\nПомощь по всем командам можно получить по команде "@acecourtbotvk помощь".\nО всех проблемах, связанных с работой бота, обращайтесь в группу: vk.com/aceCourtBotVK или к создателю vk.com/saraseka.')
        else:
            #notifs
            
            query = Chat.get_or_none(Chat.id == id)
            if query==None:
                print('passed through if statement')
                chat = Chat.create(id = id, message_received = False, bot_notifications = True)
                chat.save()
            
            if msg['text'].startswith('[club204496105'):
                if 'суд' in msg['text'].lower() or ('сус' in msg['text'].lower() and 'суд' not in msg['text'].lower()):
                    messages = vk_session.method('messages.getByConversationMessageId', {'peer_id': msg['peer_id'], 'conversation_message_ids': msg['conversation_message_id'], 'extended': 1})
                    messages = messages['items'][0]['fwd_messages']
                    if len(messages)>0 and len(messages)<=100:
                        logging.info(f'Video is being rendered. CHAT_ID: {id}')
                        name = base64.b64encode(os.urandom(16)).decode('ascii').replace('/', '').replace('=', '').replace('+', '')
                        '''
                        vid = Video.create(id = id, title = name, messages = json.dumps(msg), running = True, finished = False, worker_id = worker_id)
                        vid.save()
                        '''
                        bot_render(msg, id, name)
                    elif len(messages)>100:
                        sender(id, 'Вы переслали слишком много сообщений. Пожалуйста, уменьшите количество сообщений и перешлите их ещё раз.')
                    else:
                        sender(id, 'В самом деле, Вы удивили судью, не переслав ни одного сообщения!\nДанный бот принимает только пересланные сообщения; ответы не работают. Если Вы попытались запросить видео ответом на сообщение, то попробуйте его переслать.\nВ ином случае, по всей видимости, Вам захотелось подразнить судью. Не отвлекайте его от работы!')
                elif 'помощь' in msg['text'].lower():
                    if '-m' in msg['text'].lower():
                        sender(id, "PWR — Phoenix Wright: Ace Attorney\nJFA — Phoenix Wright: Ace Attorney — Justice For All\nT&T — Phoenix Wright: Ace Attorney — Trials and Tribulations\nAAI — Ace Attorney Investigations: Miles Edgeworth\nAAI2 — Ace Attorney Investigations: Miles Edgeworth 2\nAJ — Apollo Justice: Ace Attorney\nDD — Phoenix Wright: Ace Attorney — Dual Destinies\nSOJ — Phoenix Wright: Ace Attorney — Spirit of Justice\nRND — случайное аудио, стоит по умолчанию.")
                    else:
                        sender(id, "Команды:\nсуд — создание видео.\n-ig — выбор персонажей с игнорированием пола пользователей.\n-m — выбор OST'а по коду. Коды для данной команды вы можете получить по команде '@acecourtbotvk помощь -m'")
                        logging.info(f'"Help" command executed. CHAT_ID: {id}')

if __name__=='__main__':

    query = Chat.select().where(Chat.message_received == True)
    while query.exists():
        query = Chat.select().where(Chat.message_received == True)
        for chat in query:
            chat.message_received = False
            chat.save()
            print(chat.message_received)
    
    notificator = Process(target=notify, args=())
    notificator.start()
    
    task_queue = Queue()
    workers = []
    workers_amount = 1
    for i in range(workers_amount):
        worker_id = i
        workers.append(Process(target=worker, args=(task_queue, worker_id)))
        workers[i].start()
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat:
                for i in range(workers_amount):
                    if workers[i].is_alive()==False:
                        workers[i] = Process(target=worker, args=(task_queue, worker_id))
                        workers[i].start()
                task_queue.put([event.chat_id, event.object.message], True, 1/3)