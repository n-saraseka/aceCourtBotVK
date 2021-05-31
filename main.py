import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from typing import List
from objection_engine.comment import Comment
from objection_engine.renderer import render_comment_list
import os, shutil
import base64
import requests
import random
from tokens import group_token, user_token, group_id
from vk_methods import sender, user_get, group_name_get
from api_and_stuff import vk_session, vk_user_session, current_dir
from render_messages import bot_render
from multiprocessing import Process, Queue

longpoll = VkBotLongPoll(vk_session, group_id)

def render_video(msg, id, video_name):
    bot_render(msg, id, video_name)

def worker(queue):
    while True:
        task = queue.get()
        id = task[0]
        msg = task[1]
        if list(msg.keys()).count('action')>0 and msg['action']['type']=='chat_invite_user':
            sender(id, 'Добрый день, господа юристы! Я — бот, создающий сцены в стиле Ace Attorney.\nПерешлите мне переписку с командой "@aceCourtBotVK суд" и я создам с ней видео.\nПомощь по всем командам можно получить по команде "@aceCourtBotVK помощь".\nО всех проблемах, связанных с работой бота, обращайтесь в группу: vk.com/aceCourtBotVK или к создателю vk.com/saraseka.')
        elif msg['text'].startswith('[club204496105'):
                if 'суд' in msg['text']:
                    messages = vk_session.method('messages.getByConversationMessageId', {'peer_id': msg['peer_id'], 'conversation_message_ids': msg['conversation_message_id'], 'extended': 1})
                    messages = messages['items'][0]['fwd_messages']
                    if len(messages)>0 and len(messages)<=100:
                        name = base64.b64encode(os.urandom(16)).decode('ascii').replace('/', '').replace('=', '').replace('+', '')
                        bot_render(msg, id, name)
                    elif len(messages)>100:
                        sender(id, 'Вы переслали слишком много сообщений. Пожалуйста, уменьшите количество сообщений и перешлите их ещё раз.')
                    else:
                        sender(id, 'В самом деле, Вы удивили судью, не переслав ни одного сообщения!\nДанный бот принимает только пересланные сообщения; ответы не работают. Если Вы попытались запросить видео ответом на сообщение, то попробуйте его переслать.\nВ ином случае, по всей видимости, Вам захотелось подразнить судью. Не отвлекайте его от работы!')
                elif 'помощь' in msg['text']:
                    sender(id, "Команды:\nсуд — создание видео. \n-p — видео будет публичным и Вы сможете его сохранить себе.\n-ig — выбор персонажей с игнорированием пола пользователей.\n-m — выбор OST'а по коду. Коды для -m:\nPWR - Phoenix Wright: Ace Attorney\nJFA - Ace Attorney: Justice For All\nT&T - Ace Attorney: Trials and Tribulations\nAJ - Apollo Justice: Ace Attorney\nRND - случайное аудио, стоит по умолчанию.")

if __name__=='__main__':
    task_queue = Queue()
    worker_1 = Process(target=worker, args=((task_queue),))
    worker_1.start()
    worker_2 = Process(target=worker, args=((task_queue),))
    worker_2.start()
    worker_3 = Process(target=worker, args=((task_queue),))
    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            if event.from_chat:
                task_queue.put([event.chat_id, event.object.message], True, 1/3)