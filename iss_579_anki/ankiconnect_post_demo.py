"Sample posting to ankiconnect"

import json
import requests

# Config needed:
# enabled - bool
# apiKey - optional
# webBindAddress - default 127.0.0.1
# webBindPort - default 8765

post_dict = """
{
    "action": "addNote",
    "version": 6,
    "params": {
        "note": {
            "deckName": "zzTestAnkiConnect",
            "modelName": "Basic_vocab",
            "fields": {
                "Word": "some_word",
                "Definition": "some_def"
            },
            "options": {
                "allowDuplicate": false,
                "duplicateScope": "deck",
                "duplicateScopeOptions": {
                    "deckName": "Default",
                    "checkChildren": false,
                    "checkAllModels": false
                }
            },
            "tags": [
                "yomichan"
            ],
            "picture": [{
                "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c7/A_black_cat_named_Tilly.jpg/220px-A_black_cat_named_Tilly.jpg",
                "filename": "black_cat.jpg",
                "fields": [
                    "Picture"
                ]
            }]
        }
    }
}
"""

post_dict = """
{
  "action": "multi",
  "params": {
    "actions": [
      {
        "action": "storeMediaFile",
        "params": {
          "filename": "example.png",
          "url": "https://upload.wikimedia.org/wikipedia/commons/7/70/Example.png"
        }
      },
      {
        "action": "addNote",
        "params": {
          "note": {
            "deckName": "zzTestAnkiConnect", 
            "modelName": "Basic_vocab", 
            "fields": { 
              "Word": "xx2", 
              "Definition": "Wikipedia",
              "Picture": "<img src='example.png'>"
            }, 
            "tags": []
          }
        }
      }
    ]
  }
}
"""

print(post_dict)

payload = json.loads(post_dict)
print(payload)
# import sys
# sys.exit(0)

ANKI_CONNECT_URL = "http://localhost:8765"
ret = requests.post(ANKI_CONNECT_URL, json=payload, timeout=5)
rj = ret.json()
print(rj)

# if rj["error"] is not None:
#     print("ERR")
#     print(rj)
# else:
#     print("ok???")
#     print(rj)


# From https://foosoft.net/projects/anki-connect/
### import json
### import urllib.request
###
### def request(action, **params):
###     return {'action': action, 'params': params, 'version': 6}
###
### def invoke(action, **params):
###     requestJson = json.dumps(request(action, **params)).encode('utf-8')
###     response = ... use requests here ...
###     if len(response) != 2:
###         raise Exception('response has an unexpected number of fields')
###     if 'error' not in response:
###         raise Exception('response is missing required error field')
###     if 'result' not in response:
###         raise Exception('response is missing required result field')
###     if response['error'] is not None:
###         raise Exception(response['error'])
###     return response['result']
###
### invoke('createDeck', deck='test1')
### result = invoke('deckNames')
### print('got list of decks: {}'.format(result))
