# -*- coding: utf-8 -*-
import feedparser
import logic
import cacher

##
## private functions
##
page_size = 30

@cache('categories.all', 60*60*24)
def get_all_categories():
    return db().select(db.category.ALL, orderby=db.category.name).as_list()

@cache('pins.all', 30)
def get_all_pins():
    return db().select(db.pin.ALL, orderby=~db.pin.created_on, limitby=(0,50)).as_list()

##
## public functions
##
def all():
    if request.vars.category:
        cat_name = request.vars.category
        category = db(db.category.name==cat_name.lower()).select().first()
        if category:
            api_url = URL('api', 'categories', args=[category['id'], 'pins'])
        else:
            api_url = URL('api', 'categories', args=['all', 'pins'])
    else:
        category = None
        api_url = URL('api', 'categories', args=['all', 'pins'])

    pins = logic.get_pins_by_category(category, 0, page_size)

    boards = []
    if auth.user:
        current_user = cacher.get('auth_user', auth.user.id)
        boards = cacher.get_multi('board', current_user['boards']).values()

    return dict(show_pinner=True, current_category=category, categories=get_all_categories(), boards=boards, pins=pins, api_url=api_url)

def index():

    if auth.user is None:
        return all()

    current_user = cacher.get('auth_user', auth.user.id)

    response.title = 'pinformation :: {0}'.replace('{0}', current_user['full_name'])

    boards = cacher.get_multi('board', current_user['boards']).values()

    result = logic.get_follow_boards_pins(auth.user.id, 0, page_size)
    api_url = URL('api', 'pins')
# if we want to add myself
#    me = logic.get_user_pins(auth.user.id, 0, page_size)
#    result.extend(me)
#    result = sorted(all, key=lambda (id,t,s): t, reverse=True)

    pin_ids = [id for (id,t,s) in result]
    dic_pins = cacher.get_multi('pin', pin_ids)
    pins = [dic_pins[id] for id in pin_ids]

    if len(pins) == 0 and len(boards) == 0:
        redirect(URL('default','welcome'))

    return dict(show_pinner=True, categories=get_all_categories(), boards=boards, pins=pins, api_url=api_url)


def people():
    ##if empty "/people" return to main
    if len(request.args)==0:
       redirect(URL('index'))

    id = long(request.args[0])
    page_user = cacher.get('auth_user', id) or redirect(URL('index'))
    response.title = 'pinformation :: {0}'.replace('{0}', page_user['full_name'])
    api_url = URL('api', 'people', args=[page_user['id'], 'pins'])

    action = None
    boards = []

    if auth.user:
        current_user = cacher.get('auth_user', auth.user.id)
        boards = cacher.get_multi('board', current_user['boards']).values()

        if page_user['id'] != auth.user.id:
            is_following = any(page_user['id'] == id for id in current_user['follow_users'])
            #update the follow button
            if is_following:
                action = 'unfollow'
            else:
                action = 'follow'

            ##perform actions on user
            if request.args(1):
                action = request.args(1).lower()
                if action == 'follow' or action == 'unfollow':
                    logic.toggle_follow_user(current_user, page_user, action)
                    redirect(URL('people', args=[page_user['id']]))

    #get user pins
    top_pins = page_user['pins'][:page_size]
    dic_pins = cacher.get_multi('pin', top_pins)
    pins = [dic_pins[id] for id in top_pins]

    return dict(user=page_user,pins=pins, boards=boards, show_pinner=False, action=action, api_url=api_url, categories=get_all_categories())

def boards():
    ##if empty "/boards" return to main
    if len(request.args)==0:
       redirect(URL('index'))

    id = long(request.args(0))
    current_board = cacher.get('board', id) or redirect(URL('index'))
    response.title = 'pinformation :: {0}'.replace('{0}', current_board['name'])
    api_url = URL('api', 'boards', args=[current_board['id'], 'pins'])

    top_pins = current_board['pins'][:page_size]
    dic_pins = cacher.get_multi('pin', top_pins)
    pins = [dic_pins[id] for id in top_pins]

    action = None
    boards = []
    if auth.user:
        current_user = cacher.get('auth_user', auth.user.id)
        boards = cacher.get_multi('board', current_user['boards']).values()

        is_following = any(current_board['id'] == id for id in current_user['follow_boards'])
        #update the follow button
        if is_following:
            action = 'unfollow'
        else:
            action = 'follow'

        ##perform actions on user
        if request.args(1):
            action = request.args(1).lower()
            if action == 'follow' or action == 'unfollow':
                logic.toggle_follow_board(current_user, current_board, action)
                redirect(URL('boards', args=[current_board['id']]))

    return dict(current_board=current_board, pins=pins, boards=boards, show_pinner=False, action=action, api_url=api_url, categories=get_all_categories())

def pins():
    ##if empty "/pins" return to main
    if len(request.args)==0:
       redirect(URL('index'))

    if auth.user:
        user = cacher.get('auth_user', auth.user.id)
    else:
        user = {}

    id = long(request.args(0))
    pin = cacher.get('pin', id) or redirect(URL('index'))
    article = logic.get_article(pin['article'])
    board = cacher.get('board', pin['board'])
    comments = cacher.get_multi('comment', pin['comments']).values()
    comments = sorted(comments, key=lambda c: c['created_on'])

    return dict(user=user, pin=pin, article=article, comments=comments, board=board, categories=get_all_categories())

def welcome():

    return dict(categories=get_all_categories())

##
## default functions
##
def user():
    if len(request.args)>0 and request.args(0)=='verify':
        auth.settings.login_form.verify(request.vars.oauth_verifier)
        redirect(URL('user', 'login'))

    if request.args(0)=='clear':
        session.linkedin = None
        return 'clean'
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth(), boards=[])

def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
