# coding: utf8
import feedparser
import urllib2
import logic

def index(): redirect('/')

def _add_article(data):
    if data.has_key('feedburner_origlink'):
        url = data['feedburner_origlink']
    else:
        url = data['link']

    article = logic.get_article_by_url(url)
    if article is None:
        if data.has_key('author'):
            author = data['author']
        else:
            author = None

        article = db.article.insert(
            url=url,
            title=data.title,
            domain=urllib2.Request(url=url).get_host(),
            author=author,
            excerpt=data.summary,
            date_published=data.updated,
        )
    return article

def rss():
    rss = db().select(db.rss_feed.ALL)
    count = 0
    pins = []
    for r in rss:
        try:
            d = feedparser.parse(r.url)
            for item in d['entries']:
                try:
                    a = _add_article(item)
                    p = logic.add_pin(a, r.board)
                    if p:
                        count+=1
                except:
                    pass
        except:
            pass

    return count
