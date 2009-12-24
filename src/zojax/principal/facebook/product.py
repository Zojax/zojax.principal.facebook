from zope import interface
from zojax.product.product import Product
from zojax.principal.facebook.interfaces import IFacebookAuthenticationProduct


class FacebookAuthenticationProduct(Product):
    interface.implements(IFacebookAuthenticationProduct)

    def install(self):
        super(FacebookAuthenticationProduct, self).install()
        self.update()

    def update(self):
        pass
