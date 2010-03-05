from zope import interface, schema
from zope.i18nmessageid.message import MessageFactory
from zope.app.authentication.interfaces import IPrincipalInfo

from zojax.principal.users.interfaces import IPrincipal


_ = MessageFactory("zojax.principal.facebook")


class IFacebookAuthenticationProduct(interface.Interface):
    """ product """

    apiKey = schema.TextLine(title=_(u"Facebook API Key"),
                             description=_(u'See http://developers.facebook.com/setup.php'),
                             required=True,)

    apiSecret = schema.TextLine(title=_(u"Facebook API Secret"),
                                description=_(u'See http://developers.facebook.com/setup.php'),
                                required=True,)
    
    def initScript(request):
        """init script"""
        
        
class IFacebookPrincipalInfo(IPrincipalInfo):
    """ principal info """

    internalId = interface.Attribute('Internal ID')

    facebookId = interface.Attribute('Facebook ID')
    

class IFacebookPrincipal(IPrincipal):
    """ facebook principal """

    login = schema.TextLine(
        title=_("Login"),)

    facebookId = schema.Int(title=_(u"Facebook ID"))


class IFacebookPrincipalMarker(interface.Interface):
    """ facebook principal marker """
    

class IFacebookCredentials(interface.Interface):

    facebookId = schema.Int(title=_(u"Facebook User Id"))


class IFacebookAuthenticator(interface.Interface):

    def getPrincipalByFacebookId():
        """ Return principal id by her facebook ID. Return None if
        principal with given ID does not exist. """
