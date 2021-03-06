# Important

This repo is not on development anymore. I developed it as part of a job but after the CSGO fiasco I didn't need to continue developing it

This module is based off [node-steamcommunity](https://github.com/DoctorMcKay/node-steamcommunity).

For a more or less guide on how to use the Trade Confirmations methods on Steam Login, take a look a [this file](https://github.com/DoctorMcKay/node-steamcommunity/blob/master/components/confirmations.js) and on how to use the trade confirmation key on SteamMobileAuth take a look at [these lines](https://github.com/DoctorMcKay/node-steam-totp/blob/master/index.js#L60-L90)

# python-steamcommunity

Python port of node-steamcommunity with a focus on a session based login using requests

Hopefully with this module eveything up to steam trading will be able to be done.

Things that are functional:
- Two-factor authentication codes given a shared secret
- Trade confirmation keys too.
- Steam login. The module is based on a set of custom exceptions when 2fa, captchas or email codes are needed, sample login code to be done
- Basic steam inventory via the json endpoints available for any steam user
- SteamTradeOffers is very much functional. It can make Trade Offers and try to get the Receipt (Steam is very unreliable)
- Now SteamLogin can both check for trade confirmations, accept and decline them, as always, documentation is missing
- SteamWebApi has only the IEconService endpoint implemented, which lets the user check for incoming, outgoing, cancelling and declining trade offers

Roadmap:
- Decent documentation and (hopefully) tests :)
- Refactoring SteamInventory to Inherit from dict
- Using utils.ignoreConnectionErrors on any method that can make use of it
- Maybe adding a max retries to utils.ignoreConnectionErrors
- Any other userful SteamWebApi endpoints
- Like node-steamcommunity, being able to assign a 2fa device via command line
- Most likely move trade confirmations to a separate module or to SteamTradeOffers
- Moving all exceptions to a central module
