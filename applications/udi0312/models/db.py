# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite')
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db = db)
    ## or store session in Memcache, Redis, etc.
    ##from gluon.contrib.memdb import MEMDB
    ##from google.appengine.api.memcache import Client
    ##session.connect(request, response, db = MEMDB(Client()))

## allows access to db from modules - udi
from gluon import current
current.db = db

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, hmac_key=Auth.get_or_create_key())
crud, service, plugins = Crud(db), Service(), PluginManager()

## create custom field 'username' for linkedin authentication
import re
def tokenize_user(u): return [x.lower() for x in re.compile('\w+').findall(u.full_name)]
auth.settings.extra_fields['auth_user']= [
    Field('created_on', 'datetime', default=request.now),
    Field('username', writable=False, readable=False),
    Field('full_name', writable=False, readable=False),
    Field('keywords','list:string',compute=tokenize_user,writable=False,readable=False),
    Field('picture_url', writable=False, readable=False),
    Field('industry', writable=False, readable=False),
    Field('boards', 'list:integer', writable=False, readable=False),
    Field('pins', 'list:integer', writable=False, readable=False),
    Field('pins_created_on', 'list:string', writable=False, readable=False),
    Field('follow_users', 'list:integer', writable=False, readable=False),
    Field('follow_boards', 'list:integer', writable=False, readable=False)
]

## create all tables needed by auth if not custom tables
auth.define_tables()

## configure email
mail=auth.settings.mailer
mail.settings.server = 'gae'
mail.settings.sender = 'info@pinformation.co'


## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
##from gluon.contrib.login_methods.rpx_account import use_janrain
##use_janrain(auth,filename='private/janrain.key')

## LinkedIn
from linkedinAccount import LinkedInAccount
auth.settings.login_form=LinkedInAccount(
    request,
    session,
    '8rdvv5go8wj0',
    'T6Epe9UqqMCblEbt',
    'http://' + request.env.http_host + '/user/verify')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

db.define_table('category',
    Field('name'),
    Field('pins', 'list:integer'),
    Field('pins_updated_on', 'datetime'),
    Field('created_on', 'datetime', default=request.now),
    format = '%(name)s')

def tokenize_board(b): return [x.lower() for x in re.compile('\w+').findall(b.name)]
db.define_table('board',
    Field('name'),
    Field('user', db.auth_user),
    Field('user_name'),
    Field('category', db.category),
    Field('keywords','list:string',compute=tokenize_board,writable=False,readable=False),
    Field('pins', 'list:integer'),
    Field('pins_created_on', 'list:string'),
    Field('created_on', 'datetime', default=request.now),
    format = '%(name)s')

#from porter2 import stem
def tokenize_article(a):
    words = [x.lower() for x in re.compile('\w+').findall(a.title)]
#    try:
#        stems = [stem(w) for w in words]
#        words.extend(stems)
#        words = set(words)
#    except:
#        pass

    return words

db.define_table('article',
    Field('url'),
    Field('readability_url'),
    Field('title'),
    Field('keywords','list:string',compute=tokenize_article,writable=False,readable=False),
    Field('pins', 'list:integer'),
    Field('pins_created_on', 'list:string'),
    Field('domain'),
    Field('author'),
    Field('excerpt', 'text'),
    Field('word_count'),
    Field('total_pages'),
    Field('date_published'),
    Field('next_page_id'),
    Field('rendered_pages'),
    Field('created_on', 'datetime', default=request.now),
    format = '%(title)s')

db.define_table('pin',
    Field('board', db.board),
    Field('board_name'),
    Field('user', db.auth_user),
    Field('user_name'),
    Field('article', db.article),
    Field('article_title'),
    Field('article_domain'),
    Field('article_excerpt', 'text'),
    Field('original_pin', 'reference pin'),
    Field('comments', 'list:integer'),
    Field('created_on', 'datetime', default=request.now),)

db.define_table('comment',
    Field('user', db.auth_user),
    Field('user_name'),
    Field('user_picture_url'),
    Field('pin', db.pin),
    Field('content'),
    Field('created_on', 'datetime', default=request.now),)

db.define_table('star',
    Field('article', db.article),
    Field('user', db.auth_user),
    Field('created_on', 'datetime', default=request.now),)

db.define_table('rss_feed',
    Field('url'),
    Field('board', db.board),
    Field('created_on', 'datetime', default=request.now),)
