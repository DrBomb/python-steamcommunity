import SteamLogin
from requests.exceptions import HTTPError

class SteamWebApi(object):
    def __init__(self,Login,**kwargs):
        assert isinstance(Login, SteamLogin.SteamLogin), "Login is not a SteamLogin instance"
        self.key = kwargs.get("key")
        self.request = Login.request
        if self.key is None:
            raise Exception("No API key provided")
        self.baseURL = "https://api.steampowered.com"

class IEconService(SteamWebApi):
    endpoint = "/IEconService"
    TradeOfferResponses = {
            1:"Invalid",
            2:"Trade Offer Active",
            3:"Trade Offer has been accepted by the recipient",
            4:"The recipient made a counter offer",
            5:"The trade offer was not accepted before the expiration date",
            6:"The sender cancelled the offer",
            7:"The recipient declined the offer",
            8:"Some of the items in the offer are no longer available",
            9:"This offer is awaiting email/mobile authentication",
            10:"Either party cancelled via email/mobile",
            11:"This trade has been placed on hold",
            }
    def GetTradeOffers(self,**kwargs):
        method = "/GetTradeOffers/v1/"
        arguments = {
                'key':self.key,
                'get_sent_offers':int(kwargs.get('get_sent_offers',1)),
                'get_received_offers':int(kwargs.get('get_received_offers',0)),
                'get_descriptions':int(kwargs.get('get_descriptions',0)),
                'active_only':int(kwargs.get('active_only',1)),
                'historical_only':int(kwargs.get('historical_only',0)),
                }
        if "language" in kwargs.keys():
            arguments['language'] = kwargs['language']
        if "time_historical_cutoff" in kwargs.keys():
            arguments['time_historical_cutoff'] = kwargs['time_historical_cutoff']
        response = self.request.get(self.baseURL+self.endpoint+method,params=arguments)
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code != 403:
                raise Exception(e.message)
            raise InvalidAPIKey("This API key is invalid")
    def GetTradeOffer(self,tradeofferid,**kwargs):
        method = "/GetTradeOffer/v1/"
        arguments = {
                'key':self.key,
                'tradeofferid':tradeofferid,
                }
        if "language" in kwargs.keys():
            arguments['language'] = kwargs['language']
        response = self.request.get(self.baseURL+self.endpoint+method,params=arguments)
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code != 403:
                raise Exception(e.message)
            raise InvalidAPIKey("This API key is invalid")
    def CancelTradeOffer(self,tradeofferid):
        method = "/CancelTradeOffer/v1/"
        arguments = {
                'key':self.key,
                'tradeofferid':tradeofferid
                }
        response = self.request.post(self.baseURL+self.endpoint+method,data=arguments)
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code != 403:
                raise Exception(e.message)
            raise InvalidAPIKey("This API key is Invalid")
    def DeclineTradeOffer(self,tradeofferid):
        method = "/DeclineTradeOffer/v1/"
        arguments = {
                'key':self.key,
                'tradeofferid':tradeofferid
                }
        response = self.request.post(self.baseURL+self.endpoint+method,data=arguments)
        try:
            response.raise_for_status()
            return response.json()
        except HTTPError as e:
            if e.response.status_code != 403:
                raise Exception(e.message)
            raise InvalidAPIKey("This API key is Invalid")
class InvalidAPIKey(Exception):
    pass
