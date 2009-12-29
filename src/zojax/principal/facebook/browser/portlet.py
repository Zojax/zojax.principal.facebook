from zope import component
from zope.app.security.interfaces import IUnauthenticatedPrincipal
from zope.app.component.hooks import getSite
from zope.traversing.browser import absoluteURL

from zojax.controlpanel.interfaces import IConfiglet
from zojax.portlet.portlet import PortletBase


class FacebookConnect(PortletBase):

    def update(self):
        super(FacebookConnect, self).update()
        configlet = component.getUtility(IConfiglet, name="product.zojax-principal-facebook")
        self.fbInitScript = 'FB.init("%s", "%s/xd_receiver.htm");' % (configlet.apiKey, absoluteURL(getSite(), self.request))

    def isAvailable(self):
        if not IUnauthenticatedPrincipal.providedBy(self.request.principal):
            return False
        configlet = component.getUtility(IConfiglet, name="product.zojax-principal-facebook")
        if not configlet.apiKey:
            return False
        return True
