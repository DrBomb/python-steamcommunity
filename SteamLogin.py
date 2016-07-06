import requests, urllib, base64, time, re, pdb
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 Safari/537.36"


class SteamLogin(object):
    def __init__(self):
        self.request = requests.Session()
        self._captchaGid = -1
        self._httpRequestID = 0
        self.request.headers['User-Agent'] = USER_AGENT
        self.request.cookies.set("Steam_Language","English",domain="https://steamcommunity.com")
        self.request.cookies.set("timezoneOffset","0,0",domain="https://steamcommunity.com")
        self.login_response = None 
    def login(self,details):
        if 'steamguard' in details:
            parts = details['steamguard'].partition("||")
            self.request.cookies.set("steamMachineAuth"+parts[0],unicode(urllib.quote(parts[2])),
                    domain="https://steamcommunity.com")
        mobileHeaders = {
            "X-Requested-With": "com.valvesoftware.android.steam.community",
            "Referer": "https://steamcommunity.com/mobilelogin?oauth_client_id=DE45CD61&oauth_scope=read_profile%20write_profile%20read_client%20write_client",
            "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.1.1; en-us; Google Nexus 4 - 4.1.1 - API 16 - 768x1280 Build/JRO03S) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30",
            "Accept": "text/javascript, text/html, application/xml, text/xml, */*"
        }
        self.request.headers.update(mobileHeaders)
        self.request.cookies.set("mobileClientVersion","0 (2.1.3)",domain="https://steamcommunity.com")
        self.request.cookies.set("mobileClient","android",domain="https://steamcommunity.com")
        rsa_response = self.request.post("https://steamcommunity.com/login/getrsakey/",
                data={"username":details['username']}).json()
        key = RSA.construct((long(rsa_response['publickey_mod'],16),long(rsa_response['publickey_exp'],16)))
        cipher = PKCS1_v1_5.new(key)
        payload = {
                "captcha_text": details['captcha'] if "captcha" in details.keys() else "",
                "captchagid": self._captchaGid,
                "emailauth": details['authCode'] if "authCode" in details.keys() else "",
                "emailsteamid": "",
                "password":base64.b64encode(cipher.encrypt(details['password'])),
                "remember_login": "true",
                "rsatimestamp" : rsa_response['timestamp'],
                "twofactorcode": details['twoFactorCode'] if "twoFactorCode" in details.keys() else "",
                "username": details['username'],
                "oauth_client_id": "DE45CD61",
                "oauth_scope": "read_profile write_profile read_client write_client",
                "loginfriendlyname": "#login_emailauth_friendlyname_mobile",
                "donotcache": int(time.time())
        }
        login_response = self.request.post("https://steamcommunity.com/login/dologin/",data=payload)
        data = login_response.json()
        self.deleteMobileCookies()
        if login_response.status_code == 429:
            raise TooManyRequestsException(login_response.headers['Retry-after'])
        if login_response.status_code != 200:
            raise Error("Server Error with a reponse code " + str(login_response.status_code))
        if not data['success']:
            if data.get('emailauth_needed'):
                raise EmailAuthException(data['emaildomain'])
            elif data.get('requires_twofactor'):
                raise TwoFactorCodeRequiredException()
            elif data.get('captcha_needed') and re.match("Please verify your humanity",data.get('message')):
                self._captchaGid = data['captcha_gid']
                raise CaptchaRequiredException(self._captchaGid)
            else:
                raise AuthenticationException(data.get('message'))
        self.login_response = data
        self.custom_url = self._getCustomURL()
        self.steamID = self._getSteamID()
    def _getCustomURL(self):
        response = self.request.get("https://steamcommunity.com/my")
        if response.status_code != 200:
            raise Error("Malformed response")
        url = response.url
        match = re.search("https\:\/\/steamcommunity.com\/login\/home\/(\s\S)*",url)
        if match is not None:
            raise NotLoggedInException()
        match = re.search("https\:\/\/steamcommunity.com\/id\/(\w+)\/",url)
        if match is None:
            raise Error("Malformed Response")
        return match.groups()[0]
    def _getSteamID(self):
        response = self.request.get("https://steamcommunity.com/id/"+self.custom_url+"/?xml=1")
        match = re.search("<steamID64>(\d+)<\/steamID64>",response.text)
        if match is None:
            raise Error("Something has gone wrong")
        return match.groups()[0]
    def loggedIn(self):
        resp = self.request.get("https://steamcommunity.com/my",allow_redirects=False)
        url = resp.headers['Location']
        match = re.search("https\:\/\/steamcommunity.com\/login\/home\/(\s\S)*",url)
        if match is not None:
            return False
        else:
            return True
    def deleteMobileCookies(self):
        self.request.cookies.pop('mobileClientVersion')
        self.request.cookies.pop('mobileClient')


class Error(Exception):
    #Base Exception
    pass

class EmailAuthException(Error):
    def __init__(self,emaildomain):
        self.emailDomain = emaildomain
    def __str__(self):
        return "A code has been sent to " + self.emaildomain

class CaptchaRequiredException(Error):
    def __init__(self,captchaGid):
        self.captchaGid = captchaGid
        self.captchaURL = "https://steamcommunity.com/login/rendercaptcha/?gid=" + str(captchaGid)
    def __str__(self):
        return "Please verify your humanity using this captcha: " + self.captchaURL

class TwoFactorCodeRequiredException(Error):
    def __str__(self):
        return "A Two Factor Code is required to Log in"
class AuthenticationException(Error):
    pass
class NotLoggedInException(Error):
    def __str__(self):
        return "Not logged in"
class TooManyRequestsException(Error):
    def __init__(self,RetryAfter):
        self.retryafter = int(RetryAfter)
    def __str__(self):
        return "The server requests you to refrain sending more requests for " + self.retryafter + " seconds"
