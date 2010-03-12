from zope import component
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.app.component.hooks import getSite
from zope.traversing.browser import absoluteURL

from zojax.portlet.portlet import PortletBase

from zojax.principal.facebook.interfaces import IFacebookAuthenticationProduct


class FacebookConnect(PortletBase):

    def update(self):
        super(FacebookConnect, self).update()
        self.product = component.getUtility(IFacebookAuthenticationProduct)
        self.fbInitScript = self.product.initScript(self.request)
        self.callbackURL = '%s/facebookSignIn'%absoluteURL(getSite(), self.request)
        self.onlogin = "window.location = '%s'"%self.callbackURL

    def isAvailable(self):
        if not IUnauthenticatedPrincipal.providedBy(self.request.principal):
            return False
        if not product.apiKey:
            return False
        return True
