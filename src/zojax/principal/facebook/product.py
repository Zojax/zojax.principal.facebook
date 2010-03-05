from zope import interface
from zope.traversing.browser import absoluteURL
from zope.app.component.hooks import getSite

from zojax.product.product import Product
from zojax.resourcepackage import library

from interfaces import IFacebookAuthenticationProduct


class FacebookAuthenticationProduct(Product):
    interface.implements(IFacebookAuthenticationProduct)

    def install(self):
        super(FacebookAuthenticationProduct, self).install()
        self.update()

    def update(self):
        pass

    def initScript(self, request):
        return r"""
FB.init("%(apiKey)s", "%(siteURL)s/xd_receiver.htm", {"forceBrowserPopupForLogin":true});
""" % dict(apiKey=self.apiKey, siteURL=absoluteURL(getSite(), request))