from SteamLogin import SteamLogin
from SteamInventory import Item
from urlparse import urlparse, parse_qs
import re, json

class Offer(object):
    OurContextsRE = re.compile(r'var g_rgAppContextData = ([\s\"\\\/\-\w\d\{\}\[\]\:\.\,]+);')
    TheirContextsRE = re.compile(r'var g_rgPartnerAppContextData = ([\s\"\\\/\-\w\d\{\}\[\]\:\.\,]+);')
    OurSteamIDRE = re.compile(r'UserYou\.SetSteamId\( \'(\d+)\' \);')
    TheirSteamIDRE = re.compile(r'UserThem\.SetSteamId\( \'(\d+)\' \);')
    def __init__(self,Login):
        assert isinstance(Login, SteamLogin), str(Login) + " is not an instance of SteamLogin"
        self.request = Login.request
        self.myAssets = []
        self.theirAssets = []
        self.tradeMessage = ""
        self.__parameters_loaded = False
        self.sent = False
        for x in self.request.cookies:
            if x.name == 'sessionid':
                self.sessionid = x.value
                break
        else:
            raise Exception("Sessionid is missing from Login cookies")

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
            self.partner = q['partner']
            self.token = q['token']
        except AssertionError:
            print("Invalid TradeURL")
            raise
        tradeURLResponse = self.request.get(tradeURL)
        if tradeURLResponse.status_code != 200:
            print tradeURLResponse.text
            raise Exception("Server Error" + str(tradeURLResponse.status_code))
        self.OurContexts = json.loads(self.OurContextsRE.search(tradeURLResponse.text).groups()[0])
        self.TheirContexts = json.loads(self.TheirContextsRE.search(tradeURLResponse.text).groups()[0])
        self.OurSteamID = self.OurSteamIDRE.search(tradeURLResponse.text).groups()[0]
        self.TheirSteamID = self.TheirSteamIDRE.search(tradeURLResponse.text).groups()[0]
        self.__parameters_loaded = True

    def loadPartnerInventory(self,appID,contextID):
        assert self.__parameters_loaded, "Trade URL has not been loaded"
        sessionid = self.sessionid
        url = "https://steamcommunity.com/tradeoffer/new/partnerinventory"
        parameters = {
                "sessionid":sessionid,
                "partner":self.TheirSteamID,
                "appid":appID,
                "contextid":contextID,
                }
        self.request.headers['Referer'] = self.tradeURL
        data = self.request.get(url,params=parameters).json()
        rgInventory = data['rgInventory']
        rgDescriptions = data['rgDescriptions']
        self.TheirInventory = []
        try:
            for x in rgInventory.keys():
                item_id = x 
                class_id = rgInventory[x]['classid']
                instance_id = rgInventory[x]['instanceid']
                amount = rgInventory[x]['amount']
                key = str(class_id) + "_" + str(instance_id)
                description = rgDescriptions[key]
                self.TheirInventory.append(Item(item_id,contextID,class_id,instance_id,amount,description))
        except AttributeError:
            pass
    def loadOurInventory(self,appID,contextID):
        assert self.__parameters_loaded, "Trade URL has not been loaded"
        self.request.headers['Referer'] = self.tradeURL
        url = "https://steamcommunity.com/profiles/" + str(self.OurSteamID) + "/inventory/json/" + str(appID) + "/" + str(contextID)
        data = self.request.get(url,params={'trading':1}).json()
        rgInventory = data['rgInventory']
        rgDescriptions = data['rgDescriptions']
        self.OurInventory = []
        try:
            for x in rgInventory.keys():
                item_id = x 
                class_id = rgInventory[x]['classid']
                instance_id = rgInventory[x]['instanceid']
                amount = rgInventory[x]['amount']
                key = str(class_id) + "_" + str(instance_id)
                description = rgDescriptions[key]
                self.OurInventory.append(Item(item_id,contextID,class_id,instance_id,amount,description))
        except AttributeError:
            pass
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
        }
        for x in self.myAssets:
            asset = {}
            asset['appid'] = x.appid
            asset['contextid'] = x.contextid
            asset['amount'] = x.amount
            asset['assetid'] = x.itemid
            payload['me']['assets'].append(asset)
        for x in self.theirAssets:
            asset = {}
            asset['appid'] = x.appid
            asset['contextid'] = x.contextid
            asset['amount'] = x.amount
            asset['assetid'] = x.itemid
            payload['them']['assets'].append(asset)
        return json.dumps(payload,separators=(',',':'))
    def _get_trade_offer_create_params(self):
        payload = {
                'trade_offer_access_token':self.token,
        }
        return json.dumps(payload,separators=(',',':'))
    def sendOffer(self):
        self.request.headers['Referer'] = self.tradeURL
        tradedata = {
                'sessionid':self.sessionid,
                'serverid':1,
                'partner':self.TheirSteamID,
                'tradeoffermessage':self.tradeMessage,
                'json_tradeoffer':self._get_json_tradeoffer(),
                'trade_offer_create_params':self._get_trade_offer_create_params(),
        }
        url = "https://steamcommunity.com/tradeoffer/new/send"
        self.sendOfferResponse = self.request.post(url,data=tradedata)

