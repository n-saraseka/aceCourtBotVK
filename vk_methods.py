from api_and_stuff import vk_session, vk_user_session, current_dir

def sender(id, text, from_chat):
    if from_chat:
        vk_session.method('messages.send', {'chat_id': id, 'message': text, 'random_id': 0})
    else:
        vk_session.method('messages.send', {'user_id': id, 'message': text, 'random_id': 0})

def user_get(id, name_case = 'nom'):
    user_get = vk_session.method('users.get', {'user_id' : id, 'name_case': name_case, 'fields': 'sex, photo_200'})
    user_get = user_get[0]
    return user_get

def group_get(group_id):
    group_get = vk_session.method('groups.getById', {'group_ids': group_id*(-1)})[0]
    return group_get