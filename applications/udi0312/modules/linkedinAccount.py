#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This file is part of web2py Web Framework (Copyrighted, 2007-2009).
Developed by Massimo Di Pierro <mdipierro@cs.depaul.edu>.
License: GPL v2

Thanks to Hans Donner <hans.donner@pobox.com> for GaeGoogleAccount.
"""

from gluon.http import HTTP
try:
    import linkedin
except ImportError:
    raise HTTP(400,"linkedin module not found")

from google.appengine.api import memcache


class LinkedInAccount(object):
    """
    Login will be done via Google's Appengine login object, instead of web2py's
    login form.

    Include in your model (eg db.py)::

        from gluon.contrib.login_methods.linkedin_account import LinkedInAccount
        auth.settings.login_form=LinkedInAccount(request,KEY,SECRET,RETURN_URL)

    """

    def __init__(self,request,session,key,secret,return_url):
        self.request = request
        self.session = session

        if self.session.linkedin is None:
            self.session.verified = False
            self.session.linkedin = linkedin.LinkedIn(key,secret,return_url, gae=True)
            self.session.linkedin.request_token()

    def verify(self, verifier):
        self.session.verified = verifier and self.session.linkedin.access_token(verifier = verifier)
        return self.session.verified

    def login_url(self, next="/"):
        return self.session.linkedin.get_authorize_url()

    def logout_url(self, next="/"):
        self.session.linkedin = None
        return next

    def get_user(self):
        if self.session.verified:
            profile = self.session.linkedin.get_profile(fields=['id', 'first-name', 'last-name','picture-url','industry'])

            try:
                memcache.delete('user.username=%s' % profile.id)
            except:
                pass

            self.request.vars['remember'] = True

            return dict(first_name = profile.first_name,
                        last_name = profile.last_name,
                        full_name = profile.first_name + ' ' + profile.last_name,
                        picture_url = profile.picture_url,
                        industry = profile.industry,
                        username = profile.id)
