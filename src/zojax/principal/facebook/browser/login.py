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
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.app.component.hooks import getSite
from zope.traversing.browser import absoluteURL
from z3c.pt.pagetemplate import ViewPageTemplateFile

from zojax.layout.pagelet import BrowserPagelet
from zojax.resourcepackage.library import includeInplaceSource
from zojax.principal.facebook.interfaces import IFacebookAuthenticationProduct


class LoginAction(BrowserPagelet):

    id = u'facebook.login'
    order = 40
    template = ViewPageTemplateFile('login.pt')

    def update(self):
        super(LoginAction, self).update()
        self.product = component.getUtility(IFacebookAuthenticationProduct)
        self.fbInitScript = self.product.initScript(self.request)
        self.callbackURL = '%s/facebookSignIn'%absoluteURL(getSite(), self.request)
        self.onlogin = "window.location = '%s'"%self.callbackURL

    def isAvailable(self):
        if not IUnauthenticatedPrincipal.providedBy(self.request.principal):
            return False
        if not self.product.apiKey:
            return False
        return True

    def isProcessed(self):
        return False
