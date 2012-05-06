import re
import logic
import cacher

page_size = 30

def index(): return dict(message="hello from search.py")

def articles():
    ids = logic.search('article', request.vars.q, 0, page_size)
    result = cacher.get_multi('article', ids).values()

    pin_ids = []
    for article in result:
        if len(article['pins']) > 0:
            pin_ids.append(article['pins'][0])

    pins = cacher.get_multi('pin', pin_ids).values()
    pins = sorted(pins, key=lambda p: p['created_on'], reverse=True)

    api_url = URL('api', 'search', args=['articles', request.vars.q])

    return dict(pins=pins, api_url=api_url)

def boards():
    ids = logic.search('board', request.vars.q, 0, page_size)
    result = cacher.get_multi('board', ids).values()

    return dict(results=result)

def people():
    ids = logic.search('auth_user', request.vars.q, 0, page_size)
    users = cacher.get_multi('auth_user', ids).values()

    if auth.user:
        current_user = cacher.get('auth_user', auth.user.id)
        for u in users:
            if any(u['id'] == id for id in current_user['follow_users']):
                u['action'] = 'unfollow'
            else:
                u['action'] = 'follow'
    return dict(results=users)