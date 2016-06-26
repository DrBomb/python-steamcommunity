import time, hmac, hashlib, requests, pdb
from bitstring import BitArray
from base64 import b64decode

def getTimeOffset():
    url = "http://api.steampowered.com/ITwoFactorService/QueryTime/v1/"
    headers = {'Content-Length':0}
    response = requests.post(url,headers=headers)
    offset = int(response.json()['response']['server_time']) - int(time.time())
    latency = response.elapsed.seconds
    return offset + latency

def timeOffset(offset=0):
    return(int(time.time()) + offset)

def generateAuthCode(secret,offset=0):
    secret = b64decode(secret)
    secret = BitArray(bytes=secret,length=len(secret)*8)
    buff = BitArray(8*8)
    timestamp = timeOffset(offset)
    buff[4*8:] = int(timestamp/30)
    auth_hmac = hmac.new(secret.tobytes(),buff.tobytes(),hashlib.sha1)
    hashed = auth_hmac.digest()
    hashed = BitArray(bytes=hashed,length=len(hashed)*8)
    start = hashed[(19*8):(19*8)+8] & BitArray('0x0f')
    hash_slice = hashed[start.int*8:(start.int*8)+(4*8)]
    fullcode = hash_slice & BitArray("0x7fffffff")
    fullcode = fullcode.int
    chars = '23456789BCDFGHJKMNPQRTVWXY'
    code = ""
    for x in range(5):
        code += chars[int(fullcode % len(chars))]
        fullcode = fullcode/len(chars)
    return code
