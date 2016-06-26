#python-steamcommunity

Python port of node-steamcommunity with a focus on a session based login using requests

Hopefully with this module eveything up to steam trading will be able to be done.

Things that are functional:
- Two-factor authentication codes given a shared secret
- Steam login. The module is based on a set of custom exceptions when 2fa, captchas or email codes are needed, sample login code to be done
- Basic steam inventory via the json endpoints available for any steam user

Roadmap:
- Trade handling, creating trades, receiving trades, both interactively with steam friends and using tradeURLs
- Trade confirmations, to be added on SteamMobileAuth
- SteamWebAPI endpoints that need an API key
- Other social features
