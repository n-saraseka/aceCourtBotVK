import os
import requests
from vk_methods import user_get, group_get
from api_and_stuff import replace_mentions
from render_messages import current_dir
from PIL import Image, ImageDraw, ImageFont
import textwrap

def gen_reply(msg, video_name, counter):
    text = msg['text'] if len(msg['text'])<=700 else msg['text'][:700]+'...'
    if text == '':
        text = ' '
    received_id = msg['from_id']
    if (received_id*(-1))<0:
        fwds_user = user_get(received_id)
        full_name = f"{fwds_user['first_name']} {fwds_user['last_name']}"
    else:
        fwds_user = group_get(received_id)
        full_name = fwds_user['name']
    avatar = fwds_user['photo_200']
    r = requests.get(avatar)
    if os.path.exists(f'evidence-{video_name}')==False:
        os.mkdir(f'evidence-{video_name}')
    evidence_dir = os.path.join(current_dir, f'evidence-{video_name}')
    with open(os.path.join(evidence_dir, 'avatar.jpg'), 'wb') as f:
        f.write(r.content)
    avatar = Image.open(os.path.join(evidence_dir, 'avatar.jpg'))
    mask = Image.new("L", avatar.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0,0,200,200), fill=255)
    mask.save(os.path.join(evidence_dir, 'mask.jpg'), quality=100)
    if 'attachments' in msg.keys():
        pic = msg['attachments']
        if pic!=[]:
            pic = pic[0]
            if pic['type']=='audio':
                if text != ' ':
                    text+=': '
                text+=f"\n♬　{pic['audio']['artist']} — {pic['audio']['title']}　♬"
            if pic['type']=='wall':
                text+="\n[Пост]"
            if pic['type']=='audio_message':
                text = pic['audio_message']['transcript']
                if text=='':
                    text='[Голосовое сообщение]'
            if pic['type']=='doc':
                if 'preview' in pic['doc'].keys():
                    pic = pic['doc']['preview']['photo']['sizes'][-1]['src']
                    r = requests.get(pic)
                    with open(os.path.join(evidence_dir, 'embed.jpg'), 'wb') as f:
                        f.write(r.content)
                else:
                    if text!= ' ':
                        text+=': '
                    text+=f'[Документ "{pic["doc"]["title"]}"'
            elif pic['type'] in ['video', 'photo', 'sticker', 'graffiti']:
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
                with open(os.path.join(evidence_dir, 'embed.jpg'), 'wb') as f:
                    f.write(r.content)
    text = replace_mentions(text)
    canvas = Image.new("RGB", (1000, 1000), color = "white")
    draw = ImageDraw.Draw(canvas)
    canvas.paste(avatar, (0,0), mask)
    name_font = ImageFont.truetype("fonts/Montserrat-Bold.ttf", 36)
    nw, nh = draw.textsize(full_name, name_font)
    draw.text((210, 10), full_name, font=name_font, fill="black")
    text = textwrap.fill(text=text, width=45)
    text_font = ImageFont.truetype("fonts/Montserrat-Regular.ttf", 30)
    draw.text((210, 56), text, font=text_font, fill="black")
    w, h = draw.textsize(text, text_font)
    if os.path.exists(os.path.join(evidence_dir, 'embed.jpg')):
        embed = Image.open(os.path.join(evidence_dir, 'embed.jpg'))
        if embed.size[0]>720:
            embed = embed.resize((720, int(embed.size[1]*720/embed.size[0])))
        canvas.paste(embed, (210, 70+h))
        if 70+h+embed.size[1]<avatar.size[1]:
            canvas = canvas.crop((0,0, canvas.size[0], avatar.size[1]))
        else:
            canvas = canvas.crop((0,0, canvas.size[0], 75+h+embed.size[1]))
        if embed.size[0]==720:
            canvas = canvas.crop((0,0,930,70+h+embed.size[1]))
        else:
            if w>embed.size[0]:
                canvas = canvas.crop((0,0, w+210,70+h+embed.size[1]))
            elif nw>embed.size[0]:
                canvas = canvas.crop((0,0,nw+210,70+h+embed.size[1]))
            else:
                canvas = canvas.crop((0,0, 210+embed.size[0],70+h+embed.size[1]))
    else:
        if 70+h<avatar.size[1]:
            canvas = canvas.crop((0,0, canvas.size[0], avatar.size[1]))
        else:
            canvas = canvas.crop((0,0, canvas.size[0], 75+h))
        if nw>w:
            canvas = canvas.crop((0,0, nw+210, canvas.size[1]))
        else:
            canvas = canvas.crop((0,0, w+210, canvas.size[1]))
    canvas.save(os.path.join(evidence_dir, f'{counter}.jpg'))
    os.remove(os.path.join(evidence_dir, 'avatar.jpg'))
    os.remove(os.path.join(evidence_dir, 'mask.jpg'))
    if os.path.exists(os.path.join(evidence_dir, 'embed.jpg')):
        os.remove(os.path.join(evidence_dir, 'embed.jpg'))
    return os.path.join(evidence_dir, f'{counter}.jpg')
