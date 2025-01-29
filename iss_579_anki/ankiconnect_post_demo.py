import requests
import json

# Config needed:
# enabled - bool
# apiKey - optional
# webBindAddress - default 127.0.0.1
# webBindPort - default 8765

ANKI_CONNECT_URL = "http://localhost:8765"

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

print(post_dict)

payload = json.loads(post_dict)
print(payload)
# import sys
# sys.exit(0)

ret = requests.post(ANKI_CONNECT_URL, json=payload)
rj = ret.json()
if rj["error"] != None:
    print("ERRR")
    print(rj)
else:
    print("ok???")
    print(rj)


# From https://foosoft.net/projects/anki-connect/
### import json
### import urllib.request
###
### def request(action, **params):
###     return {'action': action, 'params': params, 'version': 6}
###
### def invoke(action, **params):
###     requestJson = json.dumps(request(action, **params)).encode('utf-8')
###     response = json.load(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8765', requestJson)))
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
