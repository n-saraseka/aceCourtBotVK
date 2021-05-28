import vk_api
import json
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from typing import List
from objection_engine.comment import Comment
from objection_engine.renderer import render_comment_list
import os, shutil
import requests
from tokens import group_token, user_token, group_id

vk_session = vk_api.VkApi(token = group_token)
vk_user_session = vk_api.VkApi(token = user_token)
longpoll = VkBotLongPoll(vk_session, group_id)
current_dir = os.path.dirname(os.path.abspath(__file__))

def sender(id, text):
    vk_session.method('messages.send', {'chat_id': id, 'message': text, 'random_id': 0})

def user_get(id, name_case = 'nom'):
    user_get = vk_session.method('users.get', {'user_id' : id, 'name_case': name_case})
    user_get = user_get[0]
    return user_get
def group_name_get(group_id):
    group_name_get = vk_user_session.method('groups.getById', {'group_ids': group_id*(-1)})
    group_name_get = group_name_get[0]['name']
    return group_name_get
for event in longpoll.listen():
    if event.type == VkBotEventType.MESSAGE_NEW:
        if event.from_chat:
            id = event.chat_id
            msg = event.object.message
            if list(msg.keys()).count('action')>0 and msg['action']['type']=='chat_invite_user':
                sender(id, 'Добрый день, господа юристы! Я - бот, создающий сцены в стиле Ace Attorney.\nПерешлите мне переписку с командой "@aceCourtBotVK суд" и я создам с ней видео.\nПомощь по всем командам можно получить по команде "@aceCourtBotVK помощь".\nО всех проблемах, связанных с работой бота, обращайтесь в группу: vk.com/aceCourtBotVK или к создателю vk.com/saraseka.\n')
            if msg['text'].startswith('[club204496105'):
                if 'суд' in msg['text']:
                    if len(msg['fwd_messages'])>0:
                        request = msg['text']
                        sender(id, 'Заседание начинается.')
                        sender_id = msg['from_id']
                        sender_guy = user_get(sender_id)
                        sender_name = sender_guy['first_name']
                        msg = vk_session.method('messages.getByConversationMessageId', {'peer_id': msg['peer_id'], 'conversation_message_ids': msg['conversation_message_id'], 'extended': 1})
                        messages = msg['items'][0]['fwd_messages']
                        photo_ev_detected = False
                        j = 0
                        comments = []
                        unique_ids = []
                        messages_counter = []
                        for i in range(len(messages)):
                            if len(messages)>100:
                                sender(id, 'Вы переслали более 100 сообщений.\nПожалуйста, уменьшите количество сообщений и перешлите переписку снова.')
                                break
                            current_message = messages[i]
                            text = current_message['text']
                            if text == '':
                                text = ' '
                            received_id = current_message['from_id']
                            if unique_ids.count(received_id)==0:
                                unique_ids.append(received_id)
                                messages_counter.append(0)
                                messages_counter[unique_ids.index(received_id)]+=1
                            else:
                                while len(messages_counter)<len(unique_ids):
                                    messages_counter.append(0)
                                messages_counter[unique_ids.index(received_id)]+=1
                            if (received_id*(-1))<0:
                                fwds_user = user_get(received_id)
                                full_name = f"{fwds_user['first_name']} {fwds_user['last_name']}"
                            else:
                                full_name = group_name_get(received_id)
                            pic = current_message['attachments']
                            ev_path = None
                            if pic!=[]:
                                pic = pic[0]
                                j = j + 1
                                if pic['type']=='audio':
                                    if text != ' ':
                                        text+=': '
                                    text+=f"♬　{pic['audio']['artist']} — {pic['audio']['title']}　♬"
                                elif pic['type']=='wall':
                                    if text != ' ':
                                            text+=': '
                                    if (pic['wall']['from_id']*(-1))>0:
                                        group_name = group_name_get(pic['wall']['from_id'])
                                        text+=f"[Запись сообщества {group_name}]"
                                    else:
                                        wall_name = user_get(pic['wall']['from_id'], name_case='gen')
                                        wall_name = f"{wall_name['first_name']} {wall_name['last_name']}"
                                        text+=f"\n[Запись {wall_name}]"
                                elif pic['type'] in ['video', 'photo', 'doc', 'sticker']:
                                    if photo_ev_detected == False:
                                        os.mkdir('evidence')
                                        evidence_dir = os.path.join(current_dir, 'evidence')
                                        photo_ev_detected = True
                                    if pic['type']=='video':
                                        vid_keys = list(pic['video'].keys())
                                        possible_sizes = ['1280', '800', '320', '160', '130']
                                        i = 0
                                        maxres = 'photo_1280'
                                        while maxres not in vid_keys and i<len(possible_sizes):
                                            i+=1
                                            maxres = f'photo_{possible_sizes[i]}'
                                        pic = pic['video'][maxres]
                                    elif pic['type']=='photo':
                                        pic = pic['photo']['sizes']
                                        pic = pic[len(pic)-1]['url']
                                    elif pic['type']=='doc':
                                        if pic['doc']['ext']=='gif':
                                            pic = pic['doc']['preview']['photo']['sizes'][2]['src']
                                    elif pic['type']=='sticker':
                                        pic = pic['sticker']['images_with_background'][4]['url']
                                    r = requests.get(pic)
                                    ev_path = os.path.join(evidence_dir, f'{j}.jpg')
                                    with open(ev_path, 'wb') as f:
                                        f.write(r.content)
                            comments.append(Comment(received_id, full_name, text, ev_path))
                            ev_path = None
                        if comments!=[]:
                            if '-bgm' in request:
                                if 'PWR' in request:
                                    ost_code = 'PWR'
                                elif 'JFA' in request:
                                    ost_code = 'JFA'
                                elif 'T&T' in request:
                                    ost_code = 'T&T'
                                elif 'AJ' in request:
                                    ost_code = 'AJ'
                                else:
                                    ost_code = 'RND'
                            else:
                                ost_code = 'RND'
                            render_comment_list(comments, output_filename = 'video.mp4', music_code=ost_code)
                            if photo_ev_detected:
                                shutil.rmtree('evidence')
                            sorted_counter = sorted(messages_counter, reverse=True)
                            attorney = unique_ids[messages_counter.index(sorted_counter[0])]
                            if (attorney*(-1))<0:
                                attorney_name = user_get(attorney, name_case='gen')
                                attorney_name = f"{attorney_name['first_name']} {attorney_name['last_name']}"
                            else:
                                attorney_name = f"сообщества {group_name_get(attorney)}"
                            if len(unique_ids)>1:
                                prosecutor = unique_ids[messages_counter.index(sorted_counter[0])]
                                if (prosecutor*(-1))<0:
                                    prosecutor_name = user_get(prosecutor, name_case='gen')
                                    prosecutor_name = f"{prosecutor_name['first_name']} {prosecutor_name['last_name']}"
                                else:
                                    prosecutor_name = f"сообщества {group_name_get(prosecutor)}"
                            if '-public' in request:
                                private = 0
                            else: private = 1
                            if len(unique_ids)>1:
                                a = vk_user_session.method('video.save', {'name': f"Спор {attorney_name} и {prosecutor_name}", 'description': 'Созданно ботом @aceCourtBotVK.', 'is_private': private, 'group_id': group_id, 'no_comments': 0, 'compression': 0})
                            else:
                                a = vk_user_session.method('video.save', {'name': f"Монолог {attorney_name}", 'description': 'Созданно ботом @aceCourtBotVK.', 'is_private': private, 'group_id': group_id, 'no_comments': 0, 'compression': 0})
                            with open('video.mp4', 'rb') as f:
                                video = requests.post(a['upload_url'], files={'video_file': f})
                            video = f"video-{group_id}_{a['video_id']}"
                            vk_session.method('messages.send', {'chat_id': id, 'message': f"[id{sender_id}|{sender_name}], видео готово.", 'attachment': video, 'random_id': 0})
                            os.remove('video.mp4')
                    else:
                        sender(id, 'В самом деле, вы удивили судью, не переслав ни одного сообщения!\nДанный бот принимает только пересланные сообщения; ответы не работают. Если вы попытались запросить видео ответом на сообщение, то попробуйте его переслать.\nВ ином случае, по всей видимости, вам захотелось подразнить судью. Не отвлекайте его от работы!')
                elif 'помощь' in msg['text']:
                    sender(id, "Команды:\nсуд - создание видео \n-public - видео будет публичным и вы сможете его сохранить себе.\n-bgm - выбор OST'а по коду. Коды для -bgm:\nPWR - Phoenix Wright: Ace Attorney\nJFA - Ace Attorney: Justice For All\nT&T - Ace Attorney: Trials and Tribulations\nAJ - Apollo Justice: Ace Attorney\nRND - случайное аудио, стоит по умолчанию.")
                else:
                    sender(id, 'Не упоминайте меня зазря, пожалуйста! Вдруг у меня важное заседание?\nЕсли вы забыли, как запросить создание видео, напишите "@aceCourtBotVK помощь".')

