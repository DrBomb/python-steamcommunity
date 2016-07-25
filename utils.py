from functools import wraps
from requests.exceptions import ConnectionError, InvalidSchema
import re, SteamExceptions, time

def ignoreConnectionErrors(*fun,**opts):
    def wrapper_decorator(f):
        @wraps(f)
        def wrapper(*args,**kwargs):
            while True:
                try:
                    f(*args,**kwargs)
                    break
                except ConnectionError as e:
                    if opts.get('echo',False):
                        print e
                    time.sleep(1)
        return wrapper
    if len(fun) == 1:
        if callable(fun[0]):
            return wrapper_decorator(fun[0])
        else:
            raise TypeError("argument 1 to @ignoreConnectionErrors has to be callable")
    if fun:
        raise TypeError("@ignoreConnectionErrors takes 1 argument, {0} given".format(sum([len(fun),len(opts)])))
    return wrapper_decorator

def raiseLostAuth(f):
    @wraps(f)
    def lost_auth_wrapper(*args,**kwargs):
        try:
            f(args,**kwargs)
        except InvalidSchema as e:
            if re.search(r'steammobile://lostauth',e.message) is not None:
                raise SteamExceptions.LostAuthException("Login was lost, relog again")
    return lost_auth_wrapper
