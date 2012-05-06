from gluon import current
from google.appengine.api import memcache
from readability import Readability
import datetime
import cacher
import re

# string -> time
def _strptime(val):
    if '.' not in val:
        return datetime.datetime.strptime(val, "%Y-%m-%d %H:%M:%S")

    nofrag, frag = val.split(".")
    date = datetime.datetime.strptime(nofrag, "%Y-%m-%d %H:%M:%S")

    frag = frag[:6]  # truncate to microseconds
    frag += (6 - len(frag)) * '0'  # add 0s
    return date.replace(microsecond=int(frag))

# time -> string
def _strftime(val):
    if val.microsecond == 0:
        return val.strftime("%Y-%m-%d %H:%M:%S")
    else:
        str = val.strftime("%Y-%m-%d %H:%M:%S")
        str += '.%d' % val.microsecond
        return str

def _get_all_pins():
    db = current.db
    key = 'category.all.pins'
    pins = memcache.get(key)
    if pins is None or len(pins)==0:
        rows =  db().select(db.pin.ALL, orderby=~db.pin.created_on, limitby=(0,500))
        pins = [r['id'] for r in rows]
        memcache.set(key, pins)

    return pins

def get_pins_by_category(cat, start, end):
    ids = []
    if cat == None:
        ids = _get_all_pins()
    else:
        #get updated list from cache - db saves once a day
        cat = cacher.get('category', cat['id'])
        ids = cat['pins']

    if ids and len(ids)>0:
        ids = ids[start:end]
        dic_pins = cacher.get_multi('pin', ids)
        pins = [dic_pins[id] for id in ids]
        return pins

    return []

# expects db pin and not cache pin
def _add_pin_to_category(pin):
    cat = cacher.get('category', pin.board.category['id'])

    cat['pins'].insert(0, pin.id)
    if len(cat['pins'])>1000: cat['pins'].pop()

    last_db_update = cat['pins_updated_on']
    if last_db_update is None:
        last_db_update = datetime.datetime.now() - datetime.timedelta(days=2)
    else:
        last_db_update = _strptime(last_db_update)

    now = datetime.datetime.now()
    if now - last_db_update > datetime.timedelta(days=1):
        pin.board.category.pins = cat['pins']
        pin.board.category.pins_updated_on = now
        pin.board.category.update_record()
        cat['pins_updated_on'] = _strftime(now)

    memcache.set('%u' % cat['id'], cat)

    all = _get_all_pins()
    all.insert(0, pin.id)
    if len(all)>1000: all.pop()
    memcache.set('category.all.pins', all)


def add_pin(article, board):
    db = current.db

    pin = db((db.pin.article==article['id'])&(db.pin.board==board['id'])).select().first()
    if pin == None:
        pin = db.pin.insert(
            article=article['id'],
            article_title = article['title'],
            article_domain = article['domain'],
            article_excerpt = article['excerpt'],
            board=board['id'],
            board_name=board['name'],
            user = board['user'],
            user_name = board['user_name'],
        )

        #put it in the cache
        cacher.get('pin', pin.id)

        #get from db as board might be from cache
        db_board = db.board(board['id'])
        db_board.pins.insert(0, pin.id)
        db_board.pins_created_on.insert(0, pin.created_on)
        db_board.update_record()
        cacher.delete(board['id'])

        #update article from db
        db_article = db.article(article['id'])
        db_article.pins.insert(0, pin.id)
        db_article.pins_created_on.insert(0, pin.created_on)
        db_article.update_record()
        cacher.delete(article['id'])

        #update user pins
        result = get_user_pins(db_board.user.id, 0, 500)
        ids = []
        ts = []
        for (i,t,s) in result:
            ids.append(i)
            ts.append(s)

        db_board.user.pins = ids
        db_board.user.pins_created_on = ts
        db_board.user.update_record()
        cacher.delete(db_board.user.id)

        _add_pin_to_category(pin)

        return pin

    return None

# returns [(pin_id, time, string)]
def _get_boards_pins(boards, start, end):
    pins = []
    for board in boards:
        pins.extend((pin, _strptime(created_on), created_on) for pin, created_on in zip(board['pins'], board['pins_created_on']))

    pins = sorted(pins, key=lambda (id,t,s): t, reverse=True)
    return pins[start:end]

# returns [(pin_id, time, string)]
def get_user_pins(id, start, end):
    user = cacher.get('auth_user', id)
    boards = cacher.get_multi('board', user['boards']).values()
    return _get_boards_pins(boards, start, end)

# returns [(pin_id, time, string)]
def get_follow_boards_pins(id, start, end):
    user = cacher.get('auth_user', id)
    boards = cacher.get_multi('board', user['follow_boards']).values()
    return _get_boards_pins(boards, start, end)

def _tokenize(val): return [x.lower() for x in re.compile('\w+').findall(val)]
def search(kind, term, start, end):
    arr = _tokenize(term)

    if len(arr)==0: return None

    key = 'search.%s.%s' % (kind, term)
    cached_ids = memcache.get(key)
    if cached_ids:
        return cached_ids[start:end]
    else:
        #fetch from db
        db = current.db
        rows = eval('db(db.%s.keywords.contains(arr[0])).select()' % kind)
        arr.pop(0)

        #iterate the rest of the terms with code
        for t in arr:
            query = lambda r: t in r.keywords
            rows = rows.find(query)

        rows = sorted(rows, key=lambda r: r.created_on, reverse=True)

        #set in cache
        ids = [r.id for r in rows]
        memcache.set(key, ids, 60 * 60)
        return ids[start:end]

def get_article(id):
    article = cacher.get('article', id)
    if not article.has_key('content'):
        #fetch content from readability in real time
        r = Readability()
        json = r.content(article['url'])
        article['content'] = json['content'].encode('UTF8', 'replace')
        cacher.set(article)

    return article

def get_article_by_url(url):
    key = 'article.url=%s' % url
    id = memcache.get(key)
    if id:
        return cacher.get('article', id)

    db = current.db
    article = db(db.article.url == url).select().first()
    if article:
        memcache.set(key, article['id'])

    return article

def get_user_by_username(username):
    key = 'user.username=%s' % username
    id = memcache.get(key)
    if id:
        return cacher.get('auth_user', id)

    db = current.db
    user = db(db.auth_user.username == username).select().first()
    if user:
        memcache.set(key, user['id'])

    return user

def get_users_by_username(usernames):
    if usernames is None or len(usernames) == 0:
        return None

    result = {}

    #username -> id from cache, get -1 if we know its not in the db
    keys = ['user.username=%s' % un for un in usernames]
    cached = memcache.get_multi(keys)

    #find cached users
    if cached and len(cached) > 0:
        cached_ids = []
        for username, id in cached.iteritems():
            if id > 0: cached_ids.append(id)

        cached_users = cacher.get_multi('auth_user', cached_ids)
        for u in cached_users.values():
            result[u['username']] = u

    # find all the usernames that were not in the cache, ignore if -1 exists in the cache
    db_usernames = []
    for un in usernames:
        if not cached.has_key('user.username=%s' % un):
            db_usernames.append(un)

    #break it to lists that that are not bigger than 30, GAE can't do belongs with over 30 results
    db = current.db
    list_size = 30
    lists = [db_usernames[i:i+list_size] for i in xrange(0, len(db_usernames), list_size)]

    to_cache = {}
    #query db per list
    for list in lists:
        users = db(db.auth_user.username.belongs(list)).select().as_list()
        for u in users:
            result[u['username']] = u
            to_cache['user.username=%s' % u['username']] = u['id']

    #set all usernames that does not exist in db as -1 in cache
    for un in usernames:
        if not result.has_key(un) and not cached.has_key('user.username=%s' % un):
            to_cache['user.username=%s' % un] = -1

    memcache.set_multi(to_cache)

    return result

def toggle_follow_board(user, board, action):
    db = current.db
    is_following = any(board['id'] == id for id in user['follow_boards'])

    if action == 'follow' and not is_following:
        db_user = db.auth_user(user['id'])
        db_user.follow_boards.append(board['id'])
        db_user.update_record()
        cacher.delete(db_user['id'])

    elif action == 'unfollow' and is_following:
        db_user = db.auth_user(user['id'])
        db_user.follow_boards.remove(board['id'])
        db_user.update_record()
        cacher.delete(db_user['id'])


def toggle_follow_user(follower, followee, action):
    db = current.db
    is_following = any(followee['id'] == id for id in follower['follow_users'])

    if action == 'follow' and not is_following:
        #update users list
        db_user = db.auth_user(follower['id'])
        db_user.follow_users.append(followee['id'])

        #update boards list
        for b in followee['boards']:
            if not b in db_user['follow_boards']:
                db_user['follow_boards'].append(b)

        db_user.update_record()
        cacher.delete(db_user['id'])

    elif action == 'unfollow' and is_following:
        #update users list
        db_user = db.auth_user(follower['id'])
        db_user.follow_users.remove(followee['id'])

        #update boards list
        for b in followee['boards']:
            if b in db_user['follow_boards']:
                db_user['follow_boards'].remove(b)

        db_user.update_record()
        cacher.delete(db_user['id'])

def share_on_linkedin(linkedin, pin):
    try:
        linkedin.share_update(
            comment='pinned "%s" on pinformation' % pin['article_title'],
            title=pin['article_title'],
            submitted_url='http://www.pinformation.co/pins/%u' % pin['id'],
            description='pinformation :: Curate the web'
        )
    except:
        pass