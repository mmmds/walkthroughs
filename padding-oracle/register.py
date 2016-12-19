#! /usr/bin/python2

import requests
import urllib
import base64
import sys

url = sys.argv[1]

for i in range(0, 20):
    login = "m"
    for c in range(0, i):
        login += str(c)[-1:]
    s = requests.Session()
    data = {
        "username": login,
        "password": "1",
        "password_again": "1"
    }
    r = s.post(url + "/register.php", data=data)
    auth = s.cookies["auth"]
    auth = urllib.unquote_plus(auth)
    auth = base64.b64decode(auth)
    print("{} - {} - {} - {}".format(len(login), len(auth), login, s.cookies["auth"]))

