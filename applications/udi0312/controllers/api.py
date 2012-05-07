# coding: utf8
from gluon.serializers import json, xml
from readability import Readability
import re
import feedparser
import logic
import cacher


page_size = 30

def _serialize(data):
    if request.extension == 'json':
        return XML(json(data))
    elif request.extension == 'xml':
        return XML(xml(data))

    # use the html view
    return data

def test():
    articles = db().select(db.article.ALL)

    for a in articles:
        if len(a.pins) == 0:
            pins = db(db.pin.article == a.id).select()
            pins = sorted(pins, key=lambda p: p.created_on)

            if len(pins) > 0:
                for p in pins:
                    a.pins.insert(0, p.id)
                    a.pins_created_on.insert(0, p.created_on)

                a.update_record()
                cacher.delete(a.id)

    return 'success'

def fix():
    users = db().select(db.auth_user.ALL)
    for u in users:
        boards = db(db.board.user == u.id).select()
        u.boards = []
        for b in boards:
            u.boards.insert(0,b.id)

        u.update_record()
        cacher.delete(u)

    return 'success'

##
##  RESTful API
##
@request.restful()
def pins():
    def GET(page=0):
        page = max(0, int(page)-1)
        result = logic.get_follow_boards_pins(auth.user.id, page*page_size, (page+1)*page_size)
        pin_ids = [id for (id,t,s) in result]
        dic_pins = cacher.get_multi('pin', pin_ids)
        pins = [dic_pins[id] for id in pin_ids]
        return _serialize(dict(pins=pins, show_pinner=True))
    return locals()

@request.restful()
def pin():
    def GET(id):
        id = long(id)
        pin = cacher.get('pin', id) or redirect(URL('index'))
        article = logic.get_article(pin['article'])

        if auth.user:
            user = cacher.get('auth_user', auth.user.id)
        else:
            user = None;

        comments = cacher.get_multi('comment', pin['comments']).values()
        comments = sorted(comments, key=lambda c: c['created_on'])
        return dict(user=user, pin=pin, article=article, comments=comments)
    return locals()

@request.restful()
def boards():
    def GET(id, param, page=0):
        response.view = 'api/pins.html'
        page = max(0, int(page)-1)
        id = long(id)
        board = cacher.get('board', id)

        top_pins = board['pins'][min(page*page_size, len(board['pins'])):min((page+1)*page_size, len(board['pins']))]
        dic_pins = cacher.get_multi('pin', top_pins)
        pins = [dic_pins[id] for id in top_pins]

        return _serialize(dict(pins=pins, show_pinner=False))
    return locals()

@request.restful()
def people():
    def GET(id, param, page=0):
        response.view = 'api/pins.html'
        page = max(0, int(page)-1)
        id = long(id)
        user = cacher.get('auth_user', id)

        top_pins = user['pins'][min(page*page_size, len(user['pins'])):min((page+1)*page_size, len(user['pins']))]
        dic_pins = cacher.get_multi('pin', top_pins)
        pins = [dic_pins[id] for id in top_pins]

        return _serialize(dict(pins=pins, show_pinner=False))
    return locals()

@request.restful()
def categories():
    def GET(id, param, page=0):
        response.view = 'api/pins.html'
        page = max(0, int(page)-1)

        cat = None
        try:
            cat = cacher.get('category', long(id))
        except:
            pass

        pins = logic.get_pins_by_category(cat, page*page_size, (page+1)*page_size)
        return _serialize(dict(pins=pins, show_pinner=True))
    return locals()

@request.restful()
def search():
    def GET(kind,terms,page=0):
        if kind == 'articles':
            response.view = 'api/pins.html'
            page = max(0, int(page)-1)
            ids = logic.search('article', terms, page*page_size, (page+1)*page_size)
            result = cacher.get_multi('article', ids).values()

            pin_ids = []
            for article in result:
                if len(article['pins']) > 0:
                    pin_ids.append(article['pins'][0])

            pins = cacher.get_multi('pin', pin_ids).values()
            pins = sorted(pins, key=lambda p: p['created_on'], reverse=True)
            return _serialize(dict(pins=pins))

    return locals()

##
# old methods
##
def flush_all():
    return cacher.flush_all()

def flush():
    id = long(request.vars.id)
    return cacher.delete(id)

def send_emails():
    emails = []

    if len(request.vars.email1) > 5 and IS_EMAIL()(request.vars.email1)[1] is None:
        emails.append(request.vars.email1)

    if len(request.vars.email2) > 5 and IS_EMAIL()(request.vars.email2)[1] is None:
        emails.append(request.vars.email2)

    if len(request.vars.email3) > 5 and IS_EMAIL()(request.vars.email3)[1] is None:
        emails.append(request.vars.email3)

    if len(request.vars.email4) > 5 and IS_EMAIL()(request.vars.email4)[1] is None:
        emails.append(request.vars.email4)

    if len(request.vars.email5) > 5 and IS_EMAIL()(request.vars.email5)[1] is None:
        emails.append(request.vars.email5)

    if len(emails) == 0:
        return 'No invitations sent, please check your email addresses'
    else:
        msg = request.vars.message
        current_user = cacher.get('auth_user', auth.user.id)
        message=response.render('layout/email.html',from_user=current_user, personal_msg=msg)
        auth.settings.mailer.send(to=emails,subject='I would like to invite you to Pinformation!',message=message)

        return 'Invitation successfully sent to %d recipients' % len(emails)

def send_linkedin_invites():
    subject = 'I would like to invite you to www.pinformation.co'
    msg_template = '{0}\n\n ---------------------------------------------------------------\nwww.pinformation.co is an innovative way to curate and share information on the web.\nWe help you become better at what you do.\n\nCheck out my profile on www.pinformation.co{1}'
    message = request.vars.message
    if not message or len(message) == 0:
        message = 'Hi,\n\nCheck out this new website, www.pinformation.co. It is a great way to discover and store the best articles and blog posts around the web. I use it and love it.'

    msg = msg_template.replace('{0}', message).replace('{1}', URL('default', 'people', args=[auth.user.id]))
    result = session.linkedin.send_message(subject, msg, [request.vars.username], False)
    return result

def add_comment():
    pin = db.pin(long(request.vars.pin_id))
    user = cacher.get('auth_user', auth.user.id)

    if pin:
        comment = db.comment.insert(
            user=user['id'],
            user_name=user['full_name'],
            user_picture_url=user['picture_url'],
            pin=pin['id'],
            content=request.vars.comment
        )
        pin.comments.append(comment.id)
        pin.update_record()
        cacher.delete(pin.id)

    return 'Success'

def add_repin():
    pin = cacher.get('pin', long(request.vars.id))
    board = cacher.get('board', long(request.vars.repin_board))

    if pin and board:
        repin = db((db.pin.article==pin['article'])&(db.pin.board==board['id'])).select().first()
        if repin is None:
            article = cacher.get('article', pin['article'])
            repin = logic.add_pin(article, board)
            repin.original_pin = pin['id']
            repin.update_record()
            cacher.delete(repin.id)
            if request.vars.linkedin and request.env.http_host != '127.0.0.1:8080':
                logic.share_on_linkedin(session.linkedin, repin)

    return 'Success'
    
def add_board():
    name = request.vars.name
    if re.match('(^[\w\s.-]+$)', name): #sanitize the board name
        category = cacher.get('category', long(request.vars.category))
        user = cacher.get('auth_user', auth.user.id)
        if category and user:
            boards = cacher.get_multi('board', user['boards']).values()
            already_exists = any(name == b['name'] for b in boards)
            if not already_exists:
                board = db.board.insert(
                    user=user['id'],
                    user_name = user['full_name'],
                    category=category['id'],
                    name=name
                )

                board.user.boards.append(board)
                board.user.update_record()
                cacher.delete(board.user.id)

                ##add the board to every user that follow this one
                ##should be moved to async when we have async
                try:
                    users = db(db.auth_user.follow_users.contains(board.user.id)).select()
                    for u in users:
                        logic.toggle_follow_board(u, board, 'follow')
                except:
                    pass

                return 'Success'
            else:
                return 'You already have a board with that name'
        else:
            return 'category does not exist'

    return 'please use only alpha numeric characters'
    
def add_article():
    url = request.vars.url
    board = cacher.get('board',long(request.vars.board))
    article = logic.get_article_by_url(url)

    if article is None:
        r = Readability()
        json = r.content(url)
        article = db.article.insert(
            url=json['url'],
            readability_url=json['short_url'],
            title=json['title'],
            #content=json['content'],
            domain=json['domain'],
            author=json['author'],
            excerpt=json['excerpt'],
            word_count=json['word_count'],
            total_pages=json['total_pages'],
            date_published=json['date_published'],
            next_page_id=json['next_page_id'],
            rendered_pages=json['rendered_pages'],            
        )
    
    pin = logic.add_pin(article, board)

    return 'Success'
