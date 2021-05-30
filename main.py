import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from typing import List
from objection_engine.comment import Comment
from objection_engine.renderer import render_comment_list
import os, shutil
import requests
import random
from tokens import group_token, user_token, group_id
from vk_methods import sender, user_get, group_name_get
from api_and_stuff import vk_session, vk_user_session, current_dir
from render_messages import bot_render

longpoll = VkBotLongPoll(vk_session, group_id)

for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_chat:
            id = event.chat_id
            msg = event.object.message
            if list(msg.keys()).count('action')>0 and msg['action']['type']=='chat_invite_user':
                sender(id, 'Добрый день, господа юристы! Я — бот, создающий сцены в стиле Ace Attorney.\nПерешлите мне переписку с командой "@aceCourtBotVK суд" и я создам с ней видео.\nПомощь по всем командам можно получить по команде "@aceCourtBotVK помощь".\nО всех проблемах, связанных с работой бота, обращайтесь в группу: vk.com/aceCourtBotVK или к создателю vk.com/saraseka.')
            if msg['text'].startswith('[club204496105'):
                if 'суд' in msg['text']:
                    if len(msg['fwd_messages'])>0 and len(msg['fwd_messages'])<=100:
                        bot_render(msg, id)
                    elif msg['fwd_messages']>100:
                        sender(id, 'Вы переслали слишком много сообщений. Пожалуйста, уменьшите количество сообщений и перешлите их ещё раз.')
                    else:
                        sender(id, 'В самом деле, вы удивили судью, не переслав ни одного сообщения!\nДанный бот принимает только пересланные сообщения; ответы не работают. Если вы попытались запросить видео ответом на сообщение, то попробуйте его переслать.\nВ ином случае, по всей видимости, вам захотелось подразнить судью. Не отвлекайте его от работы!')
                elif 'помощь' in msg['text']:
                    sender(id, "Команды:\nсуд — создание видео. \n-p — видео будет публичным и вы сможете его сохранить себе.\n-ig — выбор персонажей с игнорированием пола пользователей.\n-m — выбор OST'а по коду. Коды для -m:\nPWR - Phoenix Wright: Ace Attorney\nJFA - Ace Attorney: Justice For All\nT&T - Ace Attorney: Trials and Tribulations\nAJ - Apollo Justice: Ace Attorney\nRND - случайное аудио, стоит по умолчанию.")

