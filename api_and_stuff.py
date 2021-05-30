import os, vk_api
from tokens import group_token, user_token, group_id

vk_session = vk_api.VkApi(token = group_token)
vk_user_session = vk_api.VkApi(token = user_token)
current_dir = os.path.dirname(os.path.abspath(__file__))