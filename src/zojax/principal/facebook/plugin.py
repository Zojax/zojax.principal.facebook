from zope import interface, component, event
from zope.app.authentication.interfaces import IAuthenticatorPlugin
from zope.app.container.interfaces import DuplicateIDError, INameChooser
from zope.app.security.interfaces import IAuthentication, PrincipalLookupError
from zope.cachedescriptors.property import Lazy
from zope.exceptions.interfaces import UserError
from zope.schema.fieldproperty import FieldProperty

from zojax.authentication.factory import CredentialsPluginFactory, \
    AuthenticatorPluginFactory
import datetime
import md5
import rwproperty
import simplejson
import time
import urllib

from zojax.authentication.interfaces import ICredentialsPlugin, \
    PrincipalRemovingEvent
from zojax.cache.interfaces import ICacheConfiglet
from zojax.content.type.container import ContentContainer
from zojax.content.type.item import PersistentItem
from zojax.principal.users.interfaces import IUsersPlugin
from zojax.principal.users.plugin import PrincipalInfo

from interfaces import _, IFacebookPrincipal, IFacebookPrincipalInfo, \
    IFacebookCredentials, IFacebookAuthenticator, IFacebookAuthenticationProduct


REST_SERVER = 'http://api.facebook.com/restserver.php'


_marker = object()


class FacebookPrincipalInfo(object):
    interface.implements(IFacebookPrincipalInfo)

    description = u''

    def __init__(self, id, internal):
        self.id = id
        self.facebookId = internal.facebookId
        self.title = internal.title
        self.internalId = internal.__name__

    def __repr__(self):
        return 'GoogleFCPrincipalInfo(%r)' % self.id


class FacebookPrincipal(PersistentItem):
    interface.implements(IFacebookPrincipal)

    firstname = FieldProperty(IFacebookPrincipal['firstname'])
    lastname = FieldProperty(IFacebookPrincipal['lastname'])
    login = FieldProperty(IFacebookPrincipal['login'])
    password = FieldProperty(IFacebookPrincipal['password'])
    description = FieldProperty(IFacebookPrincipal['description'])
    facebookId = FieldProperty(IFacebookPrincipal['facebookId'])

    @rwproperty.getproperty
    def title(self):
        return (u'%s %s'%(self.firstname, self.lastname)).strip()

    @rwproperty.setproperty
    def title(self, title):
        names = title.split(None, 1)
        if len(names) == 1:
            self.firstname, self.lastname = (names[0], u'')
        else:
            self.firstname, self.lastname = names

    @Lazy
    def id(self):
        self.id = '%s%s%s'%(
            component.getUtility(IAuthentication, context=self).prefix,
            self.__parent__.prefix, self.__name__)
        return self.id

    def getLogin(self):
        return self.login


class FacebookCredentials(object):
    interface.implements(IFacebookCredentials)

    def __init__(self, facebookId):
        self.facebookId = facebookId


def getFacebookSignatureHash(valuesDict, apiKey, apiSecret, isCookieCheck=False):
    signature_keys = []
    for key in sorted(valuesDict.keys()):
        if (isCookieCheck and key.startswith(apiKey + '_')):
            signature_keys.append(key)
        elif (isCookieCheck is False):
            signature_keys.append(key)
    if (isCookieCheck):
        signature_string = ''.join(['%s=%s' % (x.replace(apiKey + '_',''), valuesDict[x]) for x in signature_keys])
    else:
        signature_string = ''.join(['%s=%s' % (x, valuesDict[x]) for x in signature_keys])
    signature_string = signature_string + apiSecret

    return md5.new(signature_string).hexdigest()


def expireCookies(request, apiKey):
    cookies = request.getCookies()
    for key in sorted(cookies.keys()):
        if apiKey in key:
            request.response.expireCookie(key)


class CredentialsPlugin(PersistentItem):
    interface.implements(ICredentialsPlugin)

    def __init__(self, title=u'', description=u''):
        self.title = title
        self.description = description

    def extractCredentials(self, request):
        """Ties to extract credentials from a request.

        A return value of None indicates that no credentials could be found.
        Any other return value is treated as valid credentials.
        """
        product = component.getUtility(IFacebookAuthenticationProduct)
        apiKey = product.apiKey
        apiSecret = product.apiSecret
        if not apiKey or not apiSecret:
            # Product is not configured
            return None
        cookies = request.getCookies()
        if apiKey not in cookies:
            return None
        signatureHash = getFacebookSignatureHash(cookies, apiKey, apiSecret, True)
        if signatureHash != cookies[apiKey]:
            return None
        if(datetime.datetime.fromtimestamp(float(cookies[apiKey+'_expires'])) <= datetime.datetime.now()):
            return None

        if apiKey not in cookies:
            return None
        return FacebookCredentials(int(cookies[apiKey + '_user']))


class AuthenticatorPlugin(ContentContainer):
    interface.implements(IUsersPlugin, IAuthenticatorPlugin, IFacebookAuthenticator, INameChooser)

    def __init__(self, title=_('Facebook users'), description=u'', prefix=u'zojax.facebook.'):
        self.prefix = unicode(prefix)
        self.__name_chooser_counter = 1
        self.__id_by_login = self._newContainerData()
        self.__id_by_facebook_id = self._newContainerData()
        super(AuthenticatorPlugin, self).__init__(title=title, description=description)

    def _getFacebookUserInfo(self, facebookId):
        configlet = component.getUtility(IConfiglet, context=self, name="product.zojax-principal-facebook")
        apiKey = configlet.apiKey
        apiSecret = configlet.apiSecret
        if not apiKey or not apiSecret:
            # Product is not configured
            return None
        cache = component.getUtility(ICacheConfiglet, context=self)
        ob = ('zojax.principal.facebook', '_getFacebookUserInfo')
        key = {'facebookId': facebookId}
        result = cache.query(ob, key, _marker)
        if result is _marker:
            params = {
                'method': 'Users.getInfo',
                'api_key': apiKey,
                'call_id': time.time(),
                'v': '1.0',
                'uids': facebookId,
                'fields': 'first_name,last_name,username',
                'format': 'json',
            }
            params['sig'] = getFacebookSignatureHash(params, apiKey, apiSecret)
            params = urllib.urlencode(params)
            response  = simplejson.load(urllib.urlopen(REST_SERVER, params))
            result = response[0]
            cache.set(result, ob, key)
        return result

    def _createPrincipal(self, userInfo):
        principal = FacebookPrincipal()
        principal.login = unicode(userInfo['username'] or str(userInfo['uid']), 'utf-8')
        principal.password = u''
        principal.firstname = unicode(userInfo['first_name'], 'utf-8')
        principal.lastname = unicode(userInfo['last_name'], 'utf-8')
        principal.facebookId = userInfo['uid']
        return principal

    def authenticateCredentials(self, credentials):
        """Authenticates credentials.

        If the credentials can be authenticated, return an object that provides
        IPrincipalInfo. If the plugin cannot authenticate the credentials,
        returns None.
        """
        if not IFacebookCredentials.providedBy(credentials):
            return None

        facebookId = credentials.facebookId

        if facebookId is None:
            return None

        principalId = self.getPrincipalByFacebookId(facebookId)
        if principalId is None:
            # Principal does not exist.
            principal = self._createPrincipal(self._getFacebookUserInfo(facebookId))
            name = INameChooser(self).chooseName('', principal)
            self[name] = principal
            principalId = self.getPrincipalByFacebookId(facebookId)

        return self.principalInfo(self.prefix + principalId)


    def principalInfo(self, id):
        """Returns an IPrincipalInfo object for the specified principal id.

        If the plugin cannot find information for the id, returns None.
        """
        if id.startswith(self.prefix):
            internal = self.get(id[len(self.prefix):])
            if internal is not None:
                return FacebookPrincipalInfo(id, internal)

    def getPrincipalByLogin(self, login):
        """ return principal info by login """
        if login in self.__id_by_login:
            return self.__id_by_login.get(login)

    def getPrincipalByFacebookId(self, facebookId):
        if facebookId in self.__id_by_facebook_id:
            return self.__id_by_facebook_id.get(facebookId)

    def checkName(self, name, object):
        if not name:
            raise UserError("An empty name was provided. Names cannot be empty.")

        if isinstance(name, str):
            name = unicode(name)
        elif not isinstance(name, unicode):
            raise TypeError("Invalid name type", type(name))

        if not name.isdigit():
            raise UserError("Name must consist of digits.")

        if name in self:
            raise UserError("The given name is already being used.")

        return True

    def chooseName(self, name, object):
        while True:
            name = unicode(self.__name_chooser_counter)
            try:
                self.checkName(name, object)
                return name
            except UserError:
                self.__name_chooser_counter += 1

    def __setitem__(self, id, principal):
        # A user with the new login already exists
        login = principal.login
        if login in self.__id_by_login:
            raise DuplicateIDError('Principal Login already taken!, ' + login)

        super(AuthenticatorPlugin, self).__setitem__(id, principal)
        self.__id_by_login[principal.login] = id
        self.__id_by_facebook_id[principal.facebookId] = id

    def __delitem__(self, id):
        # notify about principal removing
        auth = component.queryUtility(IAuthentication)
        if auth is not None:
            pid = auth.prefix + self.prefix + id
            try:
                principal = auth.getPrincipal(pid)
                event.notify(PrincipalRemovingEvent(principal))
            except PrincipalLookupError:
                pass

        # actual remove
        principal = self[id]
        super(AuthenticatorPlugin, self).__delitem__(id)
        del self.__id_by_login[principal.login]
        del self.__id_by_facebook_id[principal.facebookId]


credentialsFactory = CredentialsPluginFactory(
    "credentials.facebook", CredentialsPlugin, (),
    _(u'Facebook credentials plugin'),
    u'')

authenticatorFactory = AuthenticatorPluginFactory(
    "principal.facebook", AuthenticatorPlugin, ((IUsersPlugin, ''),),
    _(u'Facebook users'),
    u'')
