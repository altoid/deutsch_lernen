#!/usr/bin/env python

import requests
from pprint import pprint
import json

URL = "http://127.0.0.1:5000/api/post_test"
IDS = [1, 2, 3, 4, 5]
DATA = {
    "key": "value",
    "arr": IDS,
    "a": "aoeu"
}

DADA = json.dumps(DATA)

r = requests.post(URL, json=DATA)
pprint(json.loads(r.text))
