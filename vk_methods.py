from api_and_stuff import vk_session, vk_user_session, current_dir

def sender(id, text):
    vk_session.method('messages.send', {'chat_id': id, 'message': text, 'random_id': 0})

def user_get(id, name_case = 'nom'):
    user_get = vk_session.method('users.get', {'user_id' : id, 'name_case': name_case, 'fields': 'sex'})
    user_get = user_get[0]
    return user_get

def group_name_get(group_id):
    group_name_get = vk_user_session.method('groups.getById', {'group_ids': group_id*(-1)})
    group_name_get = group_name_get[0]['name']
    return group_name_get