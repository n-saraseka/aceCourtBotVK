from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import vk_api
from typing import List
from chat_worker import chat_worker
from user_worker import user_worker
from tokens import group_token, user_token, group_id
from vk_methods import sender
from api_and_stuff import vk_session, vk_user_session, current_dir, Chat, Video, db, dbx, del_from_dropbox
from render_messages import bot_render
from multiprocessing import Process, Queue
import logging
import signal
import time
import requests
from vk_api import ApiError

class AABotLongPoll(VkBotLongPoll):
    def listen(self):
        while True:
            try:
                for event in self.check():
                    yield event
            except Exception as e:
                print(f'Longpoll failed with exception {e}')


longpoll = AABotLongPoll(vk_session, group_id)
logging.basicConfig(filename='info.log', format='%(asctime)s - %(message)s', level=logging.INFO)

def render_video(msg, id, video_name):
    bot_render(msg, id, video_name)

def worker(queue, worker_id):
    db.connect()
    try:
        while True:
            task = queue.get()
            id = task[0]
            msg = task[1]
            from_chat = task[2]
            try:
                del_from_dropbox()
            except Exception:
                pass
            if list(msg.keys()).count('action')>0:
                query = Chat.select().where(Chat.id == id)
                if msg['action']['type']=='chat_invite_user' and msg['action']['member_id']==group_id*(-1):
                    logging.info(f'Bot added to chat. CHAT_ID: {id}')
                    if (query.exists())==False:
                        chat = Chat.create(id = id, message_received = True, bot_notifications = True, kicked=False, from_chat = True)
                    else:
                        chat = query.get()
                        chat.kicked = False
                    chat.save()
                    sender(id, 'Добрый день, господа юристы! Я — бот, создающий сцены в стиле Ace Attorney.\nПерешлите мне переписку с командой "@AABot_VK суд" и я создам с ней видео.\nПомощь по всем командам можно получить по команде "@acecourtbotvk помощь".\nО всех проблемах, связанных с работой бота, обращайтесь в группу: vk.com/aceCourtBotVK или к создателю vk.com/saraseka.', from_chat)
            else:
                if from_chat:
                    chat_worker(id, msg, from_chat)
                else:
                    user_worker(id, msg, from_chat)
    except Exception as e: 
        print(f'Worker stopped with exception {e}')

if __name__=='__main__':
    try:
        open('info.log', 'w').close()
        del_from_dropbox()

        task_queue = Queue()
        workers = []
        workers_amount = 3
        for i in range(workers_amount):
            worker_id = i
            workers.append(Process(target=worker, args=(task_queue, worker_id)))
            workers[i].start()
            print(f'Worker No. {i} has started working')
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                if event.from_chat:
                    task_queue.put([event.chat_id, event.object.message, True], True, 1/3)
                else:
                    task_queue.put([event.object.message['from_id'], event.object.message, False], True, 1/3)
                for i in range(workers_amount):
                    if workers[i].is_alive()==False:
                        print(f'Worker No. {i} has stopped working. Restarting...')
                        workers[i] = Process(target=worker, args=(task_queue, worker_id))
                        workers[i].start()
            time.sleep(1/3)
    except KeyboardInterrupt:
        del_from_dropbox()
