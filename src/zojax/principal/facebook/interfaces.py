from zope import interface, schema
from zope.i18nmessageid.message import MessageFactory
from zojax.principal.users.interfaces import IPrincipal


_ = MessageFactory("zojax.principal.facebook")


class IFacebookAuthenticationProduct(interface.Interface):
    """ product """

    apiKey = schema.TextLine(title=_(u"Facebook API Key"),
                                  required=True,)

    apiSecret = schema.TextLine(title=_(u"Facebook API Secret"),
                                  required=True,)


class IFacebookPrincipal(IPrincipal):
    """ facebook principal """

    login = schema.TextLine(
        title=_("Login"),)

    facebookId = schema.Int(title=_(u"Facebook ID"))


class IFacebookCredentials(interface.Interface):

    facebookId = schema.Int(title=_(u"Facebook User Id"))


class IFacebookAuthenticator(interface.Interface):

    def getPrincipalByFacebookId():
        """ Return principal id by her facebook ID. Return None if
        principal with given ID does not exist. """
