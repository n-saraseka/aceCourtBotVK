from api_and_stuff import vk_session, vk_user_session, current_dir, Chat, Character, db
from vk_api import ApiError
from vk_methods import sender, user_get
from render_messages import bot_render
import os
import base64
import logging
import shutil

def remove_video_content(name):
    if os.path.exists(f'{name}.mp4'):
        os.remove(f'{name}.mp4')
    if os.path.exists(f'{name}.mp4.audio.mp3'):
        os.remove(f'{name}.mp4.audio.mp3')
    if os.path.exists(f'{name}.mp4.txt'):
        os.remove(f'{name}.mp4.txt')
    if os.path.exists(name):
        shutil.rmtree(name)

def user_worker(id, msg, from_chat):
    sender_id = msg['from_id']
    sender_guy = user_get(sender_id)
    sender_name = sender_guy['first_name']
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
                    remove_video_content(name)
            except Exception as e:
                    remove_video_content(name)
                    sender(id, f'Бот не смог обработать видео! Текст сообщения:\n{e}\nПерешлите данное сообщение в сообщения группы или создателю бота, чтобы он смог решить проблему.', from_chat)
        else:
            sender(id, f'Похоже, что Вы написали "суд" без пересланного сообщения. Перешлите что-нибудь вместе с командой "суд" и попробуйте ещё раз.', from_chat)
    elif 'помощь' in msg['text'].lower().split():
        if '-m' in msg['text'].lower().split():
            sender(id, "PWR — Phoenix Wright: Ace Attorney\nJFA — Phoenix Wright: Ace Attorney — Justice For All\nT&T — Phoenix Wright: Ace Attorney — Trials and Tribulations\nAAI — Ace Attorney Investigations: Miles Edgeworth\nAAI2 — Ace Attorney Investigations: Miles Edgeworth 2\nAJ — Apollo Justice: Ace Attorney\nDD — Phoenix Wright: Ace Attorney — Dual Destinies\nSOJ — Phoenix Wright: Ace Attorney — Spirit of Justice\nRND — случайное аудио, стоит по умолчанию.", from_chat)
        elif "перс" in msg['text'].lower().split():
            sender(id, "Список персонажей можно посмотреть по ссылке: https://vk.cc/co1iQx", from_chat)
        else:
            sender(id, "Видео:\nсуд — создание видео.\n-ig — выбор персонажей с игнорированием пола пользователей.\n-m — выбор OST'а по коду. Коды для данной команды Вы можете получить по команде 'помощь -m'\nПрочие команды:\nперс - выбор собственного персонажа. Список персонажей Вы можете получить по команде 'помощь перс'.\nперс сброс - сброс персонажа.", from_chat)
    elif 'перс' in msg['text'].lower().split():
        if 'сброс' in msg['text'].lower().split():
            char = Character.get_or_none(id = sender_id)
            if (char != None):
                char.char_name = ''
                char.save()
            sender(id, 'Персонаж сброшен. Теперь в судах у вас будет случайный персонаж.', from_chat)
        else:
            char = Character.get_or_none(id = sender_id)
            if (char == None):
                char = Character.create(id = sender_id, char_name = msg['text'].split()[1].upper().encode('latin-1', 'ignore'))
            else:
                char.char_name = msg['text'].split()[1].upper()
                char.save()
            sender(id, f'Теперь Ваш персонаж - {msg["text"].split()[2].upper()}', from_chat)