from SteamLogin import SteamLogin

class Inventory(object):
    def __init__(self,Login):
        assert isinstance(Login,SteamLogin), "Login is not an instance of SteamLogin"
        self.Login = Login
        self.request = Login.request
        self.items = []
    def getInventory(self,steamID,appID,contextID,tradeable=False):
        self.steamID = steamID
        self.appID = appID
        self.contextID = contextID
        self.items = []
        params = {}
        if tradeable:
            params['trading'] = 1
        response = self.request.get("https://steamcommunity.com/id/" + steamID + "/inventory/json/" + str(appID) + "/" + str(contextID),params=params)
        if response.status_code != 200:
            raise Exception("Server Error")
        data = response.json()
        if data['success'] != True:
            try:
                error = data['Error']
                if(error == "This profile is private."):
                    raise InventoryPrivateException(steamID)
            except KeyError:
                raise InventoryException(steamID)
        rgInventory = data['rgInventory']
        rgDescriptions = data['rgDescriptions']
        for x in rgInventory.keys():
            item_id = x
            class_id = rgInventory[x]['classid']
            instance_id = rgInventory[x]['instanceid']
            amount = rgInventory[x]['amount']
            key = str(class_id) + "_" + str(instance_id)
            description = rgDescriptions[key]
            self.items.append(Item(item_id,contextID,class_id,instance_id,amount,description))
    def __str__(self):
        return("Steam Inventory for " + self.steamID + " on App: " + self.appID + " and Context: " + self.contextID)

class Item(object):
    def __init__(self,item_id,contextID,class_id,instance_id,amount,description):
        self.itemid = item_id
        self.classid = class_id
        self.instanceid = instance_id
        self.amount = amount
        self.appid = description['appid']
        self.contextid = contextID
        self.icon_url = "http://cdn.steamcommunity.com/economy/image/" + description['icon_url']
        self.icon_url_large = "http://cdn.steamcommunity.com/economy/image/" + description['icon_url_large'] if 'icon_url_large' in description.keys() else ""
        self.icon_drag_url = description['icon_drag_url']
        self.name = description['name']
        self.market_hash_name = description['market_hash_name']
        self.market_name = description['market_name']
        self.name_color = description['name_color']
        self.background_color = description['background_color']
        self.type = description['type']
        self.tradable = bool(description['tradable'])
        self.marketable = bool(description['marketable'])
        self.commodity = bool(description['commodity'])
        self.market_tradable_restriction = description['market_tradable_restriction']
        self.descripctions = description['descriptions']
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
    def __init__(self,steamID,appID,contextID):
        self.steamID = steamID
        self.appID = appID
        self.contextID = contextID
    def __str__(self):
        return("The request did not return a valid response")
class InventoryPrivateException(Exception):
    def __init__(self,steamID):
        self.steamID = steamID
    def __str__(self):
        return "The steam profile " +steamID+" is private"

