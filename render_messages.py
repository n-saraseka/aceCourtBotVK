import vk_api
from vk_api import ApiError
from typing import List
from objection_engine.comment import Comment
from objection_engine.renderer import render_comment_list
import os, shutil
import requests
import random
from tokens import group_token, user_token, group_id
from vk_methods import sender, user_get, group_get
from api_and_stuff import upload_to_dropbox, vk_session, vk_user_session, current_dir, db, dbx, upload_to_dropbox, Video, replace_mentions
from peewee import *
import time
from generate_reply import gen_reply

vk_session = vk_api.VkApi(token = group_token)
vk_user_session = vk_api.VkApi(token = user_token)
current_dir = os.path.dirname(os.path.abspath(__file__))

comments = []
unique_ids = []
messages_counter = []
j = 0
evidence_dir = ''
not_wall = True

def render_message(msg, request, video_name):
    global comments, unique_ids, messages_counter, j, not_wall, evidence_dir
    text = msg['text'] if len(msg['text'])<=700 else msg['text'][:700]+'...'
    if text == '':
        text = ' '
    received_id = msg['from_id']
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
        if '-ig' not in request:
            gender = 'male' if fwds_user['sex'] == 2 else 'female'
        else:
            gender = random.choice(['male', 'female'])
    else:
        full_name = group_get(received_id)['name']
        gender = random.choice(['male', 'female'])
    ev_path = None
    if 'fwd_messages' in msg.keys():
        j+=1
        ev_path = gen_reply(msg['fwd_messages'][0], video_name, j)
    elif 'attachments' in msg.keys():
        pic = msg['attachments']
        if pic!=[]:
            pic = pic[0]
            j = j + 1
            if pic['type']=='audio':
                if text != ' ':
                    text+=': '
                text+=f"♬　{pic['audio']['artist']} — {pic['audio']['title']}　♬"
            if pic['type']=='wall' and not_wall==True:
                not_wall = False
                render_message(pic['wall'], request, video_name)
                not_wall = True
            if pic['type']=='audio_message':
                text = pic['audio_message']['transcript']
                if text=='':
                    text='[Голосовое сообщение]'
            if pic['type']=='doc':
                if 'preview' in pic['doc'].keys():
                    if os.path.exists(f'evidence-{video_name}')==False:
                        os.mkdir(f'evidence-{video_name}')
                        evidence_dir = os.path.join(current_dir, f'evidence-{video_name}')
                    pic = pic['doc']['preview']['photo']['sizes'][-1]['src']
                    r = requests.get(pic)
                    ev_path = os.path.join(evidence_dir, f'{j}.jpg')
                    with open(ev_path, 'wb') as f:
                        f.write(r.content)
                else:
                    if text!= ' ':
                        text+=': '
                    text+=f'[Документ "{pic["doc"]["title"]}"'
            elif pic['type'] in ['video', 'photo', 'sticker', 'graffiti']:
                if os.path.exists(f'evidence-{video_name}')==False:
                    os.mkdir(f'evidence-{video_name}')
                    evidence_dir = os.path.join(current_dir, f'evidence-{video_name}')
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
                    pic = pic[-1]['url']
                elif pic['type']=='sticker':
                    pic = pic['sticker']['images_with_background'][-1]['url']
                elif pic['type']=='graffiti':
                    pic = pic['graffiti']['url']
                r = requests.get(pic)
                ev_path = os.path.join(evidence_dir, f'{j}.jpg')
                with open(ev_path, 'wb') as f:
                    f.write(r.content)
    text = replace_mentions(text)
    comments.append(Comment(received_id, full_name, text, ev_path, gender=gender))

def bot_render(msg, id, video_name, from_chat):
    global comments, unique_ids, messages_counter, j, not_wall, evidence_dir
    request = msg['text'].lower()
    sender_id = msg['from_id']
    sender_guy = user_get(sender_id)
    sender_name = sender_guy['first_name']
    if from_chat:
        sender(id, f"[id{sender_id}|{sender_name}], Ваши сообщения обрабатываются. По завершении заседания Вам будет отправлена его запись.", from_chat)
    else:
        sender(id, "Ваши сообщения обрабатываются. По завершении заседания Вам будет отправлена его запись.", from_chat)
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
    i = 0
    for i in range(len(messages)):
        render_message(messages[i], request, video_name)
    music_codes = ['pwr', 'jfa', 't&t', 'aai', 'aai2', 'aj', 'dd', 'soj']
    ost_code = 'RND'
    if '-m' in request:
        i = 0
        while ost_code == 'RND' and i<len(music_codes):
            music_code = music_codes[i]
            if music_code in request:
                ost_code = music_code
            i+=1
    if 'сус' in request and 'суд' not in request:
        ost_code = 'SUS'
    render_comment_list(comments, output_filename = video_name, music_code=ost_code)
    sorted_counter = sorted(messages_counter, reverse=True)
    attorney = unique_ids[messages_counter.index(sorted_counter[0])]
    if (attorney*(-1))<0:
        attorney_name = user_get(attorney, name_case='gen')
        attorney_name = f"{attorney_name['first_name']} {attorney_name['last_name']}"
    else:
        attorney_name = f"сообщества {group_get(attorney)['name']}"
    if len(unique_ids)>1:
        prosecutor = unique_ids[messages_counter.index(sorted_counter[1])]
        if attorney == prosecutor:
            matching_values = [i for i, x in enumerate(messages_counter) if x == sorted_counter[0]]
            prosecutor = unique_ids[matching_values[1]]
        if (prosecutor*(-1))<0:
            prosecutor_name = user_get(prosecutor, name_case='gen')
            prosecutor_name = f"{prosecutor_name['first_name']} {prosecutor_name['last_name']}"
        else:
            prosecutor_name = f"сообщества {group_get(prosecutor)['name']}"
    dropbox_name = f"Спор {attorney_name} и {prosecutor_name}" if len(unique_ids)>1 else f"Монолог {attorney_name}"
    if len(unique_ids)>1:
        a = vk_user_session.method('video.save', {'name': f"Спор {attorney_name} и {prosecutor_name}", 'description': 'Созданно ботом @aabot_vk.', 'is_private': 1, 'group_id': group_id, 'no_comments': 0, 'compression': 0})
    else:
        a = vk_user_session.method('video.save', {'name': f"Монолог {attorney_name}", 'description': 'Созданно ботом @aabot_vk.', 'is_private': 1, 'group_id': group_id, 'no_comments': 0, 'compression': 0})
    with open(f'{video_name}.mp4', 'rb') as f:
        video = requests.post(a['upload_url'], files={'video_file': f})
    video = f"video-{group_id}_{a['video_id']}"
    dropbox_info = upload_to_dropbox(f'{video_name}.mp4', dropbox_name)
    url = dropbox_info[0]
    name = dropbox_info[1]
    if url!='err':
        short_url = vk_session.method('utils.getShortLink', {'url': url, 'private': 0})['short_url']
        link_text = f'\nСсылка на скачивание: {short_url}. Видео будет доступно в течение 15 минут.'
        upload_time = int(time.time())
        video_info = Video.create(name = name, dropbox_upload_time = upload_time)
        video_info.save()
    else:
        link_text = ''
    if from_chat:
        vk_session.method('messages.send', {'chat_id': id, 'message': f"[id{sender_id}|{sender_name}], видео готово.{link_text}", 'attachment': video, 'random_id': 0})
    else:
        vk_session.method('messages.send', {'user_id': id, 'message': f"Видео готово.{link_text}", 'attachment': video, 'random_id': 0})
    os.remove(f'{video_name}.mp4')
    if os.path.exists(f'evidence-{video_name}'):
            shutil.rmtree(f'evidence-{video_name}')
    comments = []
    unique_ids = []
    messages_counter = []
    j = 0
    evidence_dir = ''
    not_wall = True