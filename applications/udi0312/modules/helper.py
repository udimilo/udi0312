from gluon.html import *
def myXML(text):
    sanitized = XML(text, sanitize=True,
        permitted_tags=['a', 'b', 'br/', 'i', 'li',
                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'ol', 'ul', 'p', 'cite', 'code', 'pre',
                        'img/','object','embed','div','em', 'strong',
                        'span', 'center', 'blockquote', 'iframe'],
        allowed_attributes={'a':['href', 'title'],
                            'img':['src', 'alt'],
                            'iframe': ['src', 'width', 'height'],

                            })

    return sanitized

def shrink(text, limit):
    if len(text) < limit:
        return text
    else:
        text = text[:limit-3] + '...'
        return text