#!/usr/bin/env python
# coding: utf8
from gluon import *
import urllib2
try:
    import simplejson as json
except ImportError:
    import json

class Readability(object):

    def __init__(self, url=None):
        self.url = url or 'http://www.readability.com/api/content/v1/parser?token=6c36c7d0bdab21d2bb8b162d11d615cbade7f788&url='

    def content(self, url_id):
        """Retrieve content."""
        url = self.url + url_id
        f = urllib2.urlopen(url)
        content = f.read().strip()
        if content:
            return json.loads(content)
        else:
            return None
