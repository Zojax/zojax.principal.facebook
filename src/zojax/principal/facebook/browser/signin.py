##############################################################################
#
# Copyright (c) 2009 Zope Foundation and Contributors.
# All Rights Reserved.
#
# This software is subject to the provisions of the Zope Public License,
# Version 2.1 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
##############################################################################
"""

$Id$
"""
from zope import component
from zope.component import getUtility, getMultiAdapter
from zope.session.interfaces import ISession
from zope.traversing.browser import absoluteURL
from zope.app.component.hooks import getSite
from zope.app.security.interfaces import \
    IAuthentication, IUnauthenticatedPrincipal
    
from zojax.authentication.interfaces import ILoginService
from zojax.statusmessage.interfaces import IStatusMessage

from zojax.principal.facebook.interfaces import _, IFacebookAuthenticationProduct


class FacebookSignIn(object):

    def __call__(self, *args, **kw):
        context = self.context
        request = self.request
        principal = request.principal
        auth = getUtility(IAuthentication)

        if IUnauthenticatedPrincipal.providedBy(principal):
            msg = auth.loginMessage
            if not msg:
                msg = _('Login failed.')

            IStatusMessage(request).add(msg, 'warning')

            request.response.redirect(u'%s/login.html'%absoluteURL(context, request))
        else:
            product = getUtility(IFacebookAuthenticationProduct)
            cookie = request.getCookies().get(product.apiKey)
            if cookie:
                if getMultiAdapter((auth, request), ILoginService).success():
                    return u''

        request.response.redirect(u'%s/'%absoluteURL(getSite(), request))
        return u''
