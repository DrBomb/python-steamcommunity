from SteamLogin import SteamLogin
from SteamExceptions import ReceiptFailed
from utils import ignoreConnectionErrors
from SteamInventory import Inventory, Item
from urlparse import urlparse, parse_qs
from bs4 import BeautifulSoup
import re, json, pdb

class Offer(object):
    def __init__(self,Login,**kwargs):
        assert isinstance(Login, SteamLogin), str(Login) + " is not an instance of SteamLogin"
        self.Login = Login
        self.request = Login.request
        self.MySteamID = Login.steamID
        self.myAssets = []
        self.theirAssets = []
        self.tradeMessage = ""
        self.tradeURL = kwargs.get('tradeURL')
        self.offerID = None
        if self.tradeURL is not None:
            self.newOffer(self.tradeURL)
        else:
            raise Exception("Empty TradeOffer")
        self.sent = False
        for x in self.request.cookies:
            if x.name == 'sessionid':
                self.sessionid = x.value
                break
        else:
            raise Exception("Sessionid is missing from Login cookies")
    @ignoreConnectionErrors
    def newOffer(self,tradeURL):
        self.tradeURL = tradeURL
        o = urlparse(tradeURL)
        try:
            assert o.scheme == 'https'
            assert o.netloc == 'steamcommunity.com'
            assert o.path == '/tradeoffer/new/'
            q = parse_qs(o.query)
            assert 'partner' in q.keys()
            assert 'token' in q.keys()
            self.partner = q['partner'][0]
            self.token = q['token'][0]
        except AssertionError:
            print("Invalid TradeURL")
            raise TradeURLInvalid
        tradeURLResponse = self.request.get(tradeURL)
        self.tradeURLResponse = tradeURLResponse
        if tradeURLResponse.status_code != 200:
            print tradeURLResponse.text
            raise Exception("Server Error" + str(tradeURLResponse.status_code))
        text = tradeURLResponse.text
        match = re.search("(You cannot trade with|This Trade URL is no longer valid for sending a trade offer to)",text)
        if match is not None:
            raise TradeURLInvalid("This trade URL is invalid or has expired")
        try:
            self.MyContexts = json.loads(re.search(r"var g_rgAppContextData = ([\s\"\\\/\-\w\d\{\}\[\]\:\.\,\']+);",text).group(1))
            self.PartnerContexts = json.loads(re.search(r"var g_rgPartnerAppContextData = ([\s\"\\\/\-\w\d\{\}\[\]\:\.\,\']+);",text).group(1))
            self.PartnerSteamID = long(re.search(r"UserThem\.SetSteamId\( \'(\d+)\' \);",text).group(1))
            self.OurEscrow = int(re.search(r"var g_daysMyEscrow = (\d+);",text).group(1))
            self.TheirEscrow = int(re.search(r"var g_daysTheirEscrow = (\d+);",text).group(1))
        except:
            print tradeURLResponse.text
            raise
    @ignoreConnectionErrors
    def loadPartnerInventory(self,appID,contextID):
        sessionid = self.sessionid
        url = "https://steamcommunity.com/tradeoffer/new/partnerinventory"
        parameters = {
                "sessionid":sessionid,
                "partner":self.PartnerSteamID,
                "appid":appID,
                "contextid":contextID,
                }
        self.request.headers['Referer'] = self.tradeURL
        data = self.request.get(url,params=parameters).json()
        self.PartnerInventory = Inventory(self.Login,steamID=self.PartnerSteamID)
        self.PartnerInventory.createItemsFromResponse(appID,contextID,data)
    @ignoreConnectionErrors
    def loadOurInventory(self,appID,contextID):
        self.request.headers['Referer'] = self.tradeURL
        self.MyInventory = Inventory(self.Login,steamID=self.MySteamID)
        self.MyInventory.getInventory(appID,contextID)
        
    def addOurItem(self,item):
        assert isinstance(item,Item)
        self.myAssets.append(item)

    def addTheirItem(self,item):
        assert isinstance(item,Item)
        self.theirAssets.append(item)

    def _get_json_tradeoffer(self):
        payload = {
                'newversion':True,
                'version':2,
                'me':{
                    'assets':[],
                    'currency':[],
                    'ready':False,
                },
                'them':{
                    'assets':[],
                    'currency':[],
                    'ready':False,
                },
                'captcha':"",
        }
        for x in self.myAssets:
            asset = {}
            asset['appid'] = str(x.appid)
            asset['contextid'] = str(x.contextid)
            asset['amount'] = x.amount
            asset['assetid'] = str(x.itemid)
            payload['me']['assets'].append(asset)
        for x in self.theirAssets:
            asset = {}
            asset['appid'] = str(x.appid)
            asset['contextid'] = str(x.contextid)
            asset['amount'] = x.amount
            asset['assetid'] = str(x.itemid)
            payload['them']['assets'].append(asset)
        return json.dumps(payload,separators=(',',':'))
    def _get_trade_offer_create_params(self):
        payload = {
                'trade_offer_access_token':self.token,
        }
        return json.dumps(payload,separators=(',',':'))
    @ignoreConnectionErrors
    def sendOffer(self):
        if self.offerID is not None:
            raise OfferAlreadySent("This offer has been already sent")
        self.request.headers['Referer'] = self.tradeURL
        tradedata = {
                'sessionid':self.sessionid,
                'serverid':1,
                'partner':str(self.PartnerSteamID),
                'tradeoffermessage':self.tradeMessage,
                'json_tradeoffer':self._get_json_tradeoffer(),
                'trade_offer_create_params':self._get_trade_offer_create_params(),
        }
        url = "https://steamcommunity.com/tradeoffer/new/send"
        self.sendOfferResponse = self.request.post(url,data=tradedata)
        offerdata = self.sendOfferResponse.json()
        self.offerID, self.needsMobileConfirmation, self.needEmailConfirmation, self.email_domain = (offerdata.get('tradeofferid'), 
                offerdata.get('needs_mobile_confirmation'), offerdata.get('needs_email_confirmation'), offerdata.get('email_domain'))

class Receipt(object):
    @ignoreConnectionErrors(echo=True)
    def __init__(self,Login,tradeID):
        assert isinstance(Login,SteamLogin)
        url = "".join(["http://steamcommunity.com/trade/",str(tradeID),"/receipt/"])
        self.response = Login.request.get(url)
        try:
            data = json.loads(self.response.text)
            if data['success'] == False:
                raise ReceiptFailed
        except ValueError:
            pass
        self.item = json.loads(re.search(r"oItem = ([\s\"\\\/\-\w\d\{\}\[\]\:\.\,\'\_\|\(\)]+);",self.response.text).group(1))
        self.__dict__.update(self.item)

        

class TradeOfferException(Exception):
    pass
class TradeURLInvalid(Exception):
    pass
class OfferAlreadySent(Exception):
    pass
