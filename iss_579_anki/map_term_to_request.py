"Mapping field demo."

import json
import re
import requests
import pyparsing as pp
from pyparsing import (
    quotedString,
    QuotedString,
    Suppress,
)


class Term:
    "Stub term class."

    def __init__(self):
        self.termid = None
        self.language = None
        self.text = None
        self.tags = []
        self.parents = []
        self.image = None
        self.translation = None


term = Term()
term.termid = 42
term.text = "aucher"
term.language = "German"
term.parents = ["hello", "there"]
term.translation = 'also "here"'
term.tags = ["der", "blah", "xxx", "yyy"]
# TODO - need to fix this URL trash stored in the table, should just store the filename
term.image = "/userimages/3/Geschenk.jpeg"

# images served from userimages in app_config
IMAGE_ROOT_DIR = "/Users/jeff/Documents/Projects/lute/data"

test_string = """\
Extra_info_back: {{ id }}
Word: {{ term }}
Plural: some value {{ parents }}
Article: {{ tags["der", "die", "das"] }} {{ term }}
Picture: {{ image }}
Sentence: some text {{ parents }} more text {{ parents }}
Definition: {{ translation }}
"""

print(test_string)

# Define regex pattern to capture text inside {{ }}
pattern = r"{{\s*(.*?)\s*}}"

keys = set(re.findall(pattern, test_string))
print(keys)

# For each key, eval the value, build the dict

plain_replacements = {
    "id": term.termid,
    "term": term.text,
    "language": term.language,
    "parents": ", ".join(term.parents),
    "tags": ", ".join(term.tags),
    "translation": term.translation,
}

calc_required = [k for k in keys if k not in plain_replacements]
print(calc_required)


def get_filtered_tags(tagvals):
    "Get tags matching the spec."
    # tagvals is a pyparsing ParseResults, convert to strings.
    real_tagvals = list(tagvals)
    ftags = [t for t in term.tags if t in real_tagvals]
    # print(f"got filtered tags {ftags}")
    return ", ".join(ftags)


media_actions = []


def handle_image(args):
    if term.image is None:
        return ""

    print(f"handling image with args: {args}")
    new_filename = f"LUTE_TERM_{term.termid}.jpg"
    hsh = {"filename": new_filename, "path": IMAGE_ROOT_DIR + term.image}
    media_actions.append(hsh)
    return f'<img src="{new_filename}">'


quoteval = QuotedString(quoteChar='"')
quotedString.setParseAction(pp.removeQuotes)
list_of_values = pp.delimitedList(quotedString)
tagvallist = Suppress("[") + list_of_values + Suppress("]")
tag_matcher = Suppress("tags") + tagvallist

image_matcher = Suppress("image")
image_match_result = image_matcher.set_parse_action(handle_image)


matcher = tag_matcher.set_parse_action(
    get_filtered_tags
) | image_matcher.set_parse_action(handle_image)

calc_replacements = {}

for c in calc_required:
    ret = matcher.parseString(c).asList()
    calc_replacements[c] = ret[0]

print(calc_replacements)


replacements = {**plain_replacements, **calc_replacements}

final = test_string
for k, v in replacements.items():
    escaped = re.escape(k)
    pattern = rf"{{{{\s*{escaped}\s*}}}}"
    print(f"Replacing {k} => {v} using pattern {pattern}")
    final = re.sub(pattern, f"{v}", final)

postjson = {}
mappings = [s.strip() for s in final.split("\n") if s.strip() != ""]
for s in mappings:
    print(f"handling '{s}'")
    field, val = s.split(":", 1)
    postjson[field.strip()] = val.strip()

print("=" * 25)
print(final)
print("=" * 25)
print(postjson)
print("=" * 25)
print(media_actions)
print("=" * 25)

post_media_actions = [{"action": "storeMediaFile", "params": p} for p in media_actions]

post_addnote = {
    "action": "addNote",
    "params": {
        "note": {
            "deckName": "zzTestAnkiConnect",
            "modelName": "Basic_vocab",
            "fields": postjson,
            "tags": term.tags,
        }
    },
}


all_actions = post_media_actions
all_actions.append(post_addnote)

full_post = {"action": "multi", "params": {"actions": all_actions}}

print("=" * 25)
print(json.dumps(full_post, indent=2))
print("=" * 25)


# ANKI_CONNECT_URL = "http://localhost:8765"
# ret = requests.post(ANKI_CONNECT_URL, json=full_post, timeout=5)
# rj = ret.json()
# print(rj)
