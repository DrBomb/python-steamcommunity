from SteamLogin import SteamLogin
from utils import ignoreConnectionErrors


class Inventory(object):
    def __init__(self,Login,**kwargs):
        assert isinstance(Login,SteamLogin), "Login is not an instance of SteamLogin"
        self.Login = Login
        self.request = Login.request
        self.custom_url = kwargs.get('custom_url')
        self.steamID = kwargs.get('steamID')
        self.items = {}
    @ignoreConnectionErrors(echo=True)
    def getInventory(self,appID,contextID,tradeable=True,**kwargs):
        update = kwargs.get('update')
        if update is None:
            if appID in self.items.keys():
                if contextID in self.items[appID].keys():
                    return
        if tradeable:
            params = {'trading':1}
        else:
            params = {'trading':0}
        if (self.custom_url is None) and (self.steamID is None):
            raise InventoryException("This inventory has no steam account associated")
        if self.custom_url is not None:
            url = "".join(["https://steamcommunity.com/id/",self.custom_url,"/inventory/json/",str(appID),"/",str(contextID)])
        else:
            url = "".join(["https://steamcommunity.com/profiles/",str(self.steamID),"/inventory/json/",str(appID),"/",str(contextID)])
        response = self.request.get(url,params=params)
        if response.status_code != 200:
            raise Exception("Server Error")
        data = response.json()
        self.createItemsFromResponse(appID,contextID,data)
    def __str__(self):
        return("Steam Inventory for " + self.steamID + " on App: " + self.appID + " and Context: " + self.contextID)
    def createItemsFromResponse(self,appID,contextID,jsonData):
        if jsonData['success'] != True:
            try:
                error = jsonData['Error']
                if(error == "This profile is private."):
                    raise InventoryPrivateException(steamID)
            except KeyError:
                raise InventoryException(appID,contextID,custom_url=self.custom_url,steamID=self.steamID)
        items = {}
        rgInventory = jsonData['rgInventory']
        rgDescriptions = jsonData['rgDescriptions']
        for x in rgInventory.keys():
            item_id = int(x)
            class_id = int(rgInventory[x]['classid'])
            instance_id = int(rgInventory[x]['instanceid'])
            amount = int(rgInventory[x]['amount'])
            key = "_".join([str(class_id),str(instance_id)])
            description = rgDescriptions[key]
            items.update({item_id:Item(item_id,contextID,class_id,instance_id,amount,description)})
        if appID not in self.items.keys():
            self.items[appID] = {}
        self.items[appID][contextID] = items

class Item(object):
    def __init__(self,item_id,contextID,class_id,instance_id,amount,description):
        self.itemid = item_id
        self.classid = class_id
        self.instanceid = instance_id
        self.amount = amount
        self.appid = description['appid']
        self.contextid = contextID
        self.icon_url = "".join(["http://cdn.steamcommunity.com/economy/image/",description['icon_url']])
        self.icon_url_large = "".join(["http://cdn.steamcommunity.com/economy/image/",description['icon_url_large']]) if 'icon_url_large' in description.keys() else ""
        self.icon_drag_url = description.get('icon_drag_url')
        self.name = description.get('name')
        self.market_hash_name = description.get('market_hash_name')
        self.market_name = description.get('market_name')
        self.name_color = description.get('name_color')
        self.background_color = description.get('background_color')
        self.type = description.get('type')
        self.tradable = bool(description.get('tradable',True))
        self.marketable = bool(description.get('marketable',True))
        self.commodity = bool(description.get('commodity',True))
        self.market_tradable_restriction = description.get('market_tradable_restriction')
        self.descripctions = description.get('descriptions')
        self.actions = description['actions'] if 'actions' in description.keys() else ""
        self.market_actions = description['market_actions'] if 'market_actions' in description.keys() else ""
        self.tags = description['tags']
    def getMarketHashName(self):
        if self.market_hash_name != "":
            return self.market_hash_name
        elif self.market_name != "":
            return self.market_name
        else:
            return self.name
    def __str__(self):
        return unicode(self).encode('utf-8')
    def __unicode__(self):
        return self.getMarketHashName()

class InventoryException(Exception):
    def __init__(self,appID,contextID,**kwargs):
        self.steamID = kwargs.get('steamID')
        self.custom_url = kwargs.get('custom_url')
        self.appID = appID
        self.contextID = contextID
    def __str__(self):
        return("The request did not return a valid response")
class InventoryPrivateException(Exception):
    def __init__(self,steamID):
        self.steamID = steamID
    def __str__(self):
        return " ".join(["The steam profile",steamID,"is private"])

