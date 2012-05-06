from google.appengine.api import memcache
from gluon import current


def _expiration():
    return 60 * 60 * 24 * 30

def _from_db(kind, id):
    db = current.db
    query = 'db(db.%s.id==%d).select().as_dict()' % (kind, id)
    result = eval(query)
    if len(result) > 0:
        result = result[id]
        key = '%u' % id
        did_store = memcache.set(key, result, _expiration())

    return  result

def _from_db_multi(kind, ids):
    if len(ids) == 0:
        return {}

    db = current.db
    result = {}
    cached = {}

    list_size = 30
    lists = [ids[i:i+list_size] for i in xrange(0, len(ids), list_size)]
    query = 'db(db.%s.id.belongs(list)).select().as_list()' % kind

    #query db per list
    for list in lists:
        items = eval(query)
        for item in items:
            result[item['id']] = item
            cached['%u' %item['id']] = item

    memcache.set_multi(cached)
    return result


def flush_all():
    return memcache.flush_all()

def set(val):
    key = '%u' % val['id']
    return memcache.set(key, val, _expiration())

def get(kind, id):
    key = '%u' % id
    result = memcache.get(key)
    if result is None:
        result = _from_db(kind, id)

    return result

def get_multi(kind, ids):
    keys = ['%u' % id for id in ids]
    cached = memcache.get_multi(keys)
    result = {}
    for key, value in cached.iteritems():
        result[long(key)] = value

    db_list = []
    if len(cached) < len(keys):
        for id in ids:
            if not result.has_key(id):
                db_list.append(id)

    db_result = _from_db_multi(kind, db_list)
    result = dict(result.items() + db_result.items())

    return result

def delete(id):
    key = '%u' % id
    result = memcache.delete(key)
    return result

def delete_multi(ids):
    keys = ['%u' % id for id in ids]
    result = memcache.delete_multi(keys)
    return  result
