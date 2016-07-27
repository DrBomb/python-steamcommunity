'''

This is a Login example script

Can be used as a Log In module for your project as it generates a pickle file for keeping the Login stored


A basic LogIn flow is:

1. Define the details dictionary, username and password are required
2. LogIn with the given details, according to steam, one of 4 exceptions will be raised:
    - TwoFactorCodeRequired: Self explanatory, add the 'twoFactorCode' key to the details 
      dictionary and try logging in again
    - CaptchaRequiredException: This is a tricky one, a captcha GUID will be stored to the Login object,
      while the exception will return the URL on the message. You must solve the captcha and put the
      "captcha_text" key onto the dict in order to log in again. This is handled very roughly by the example
    - EmailAuthException: Just like the TwoFactorCodeRequired exception but with email
3. If auth was successful the Login.requests.cookies object will have the session and steam can be used as normal

'''

import SteamLogin, SteamMobileAuth, pickle

details = {
    "username":"username",
    "password":"password",
    "shared_secret":"secret",
    }

try:
    with open("Login.pickle") as f:
        Login = pickle.load(f)
except IOError:
    Login = SteamLogin.SteamLogin()
    offset = SteamMobileAuth.getTimeOffset()
    while True:
        try:
            Login.login(details)
            break
        except SteamLogin.TwoFactorCodeRequiredException:
            details['twoFactorCode'] = SteamMobileAuth.generateAuthCode(details['shared_secret'],offset)
        except SteamLogin.CaptchaRequiredException as e:
            print e
            details['captcha'] = raw_input()
        except SteamLogin.EmailAuthException as e:
            print(e)
        except SteamLogin.TooManyRequestsException as e:
            print "Retrying after " + e.retryafter+5 + " seconds"
            time.sleep(e.retryafter+5)
        with open("Login.pickle",'wb') as f:
            pickle.dump(Login,f)
