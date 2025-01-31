"Mapping field demo."

import json
import re
import requests
import pyparsing as pp
from pyparsing import (
    quotedString,
    Suppress,
)


def build_ankiconnect_post_json(
    term, mapping_string, img_root_dir, deck_name, model_name
):
    "Build post json for term using the mappings."

    # List of ankiconnect "media actions" (file uploads) to execute.
    # Appended to during handle_image().
    media_actions = []

    def build_key_parser():
        """
        Build a parser for some keys in the mapping string.

        e.g. the mapping "article: {{ tags["der", "die", "das"] }}"
        needs to be parsed to extract certain tags from the current
        term.

        """

        def get_filtered_tags(tagvals):
            "Get term tags matching the list."
            # tagvals is a pyparsing ParseResults, use list() to convert to strings.
            ftags = [t for t in term.tags if t in list(tagvals)]
            return ", ".join(ftags)

        def handle_image(_):
            if term.image is None:
                return ""
            new_filename = f"LUTE_TERM_{term.termid}.jpg"
            hsh = {"filename": new_filename, "path": img_root_dir + term.image}
            media_actions.append(hsh)
            return f'<img src="{new_filename}">'

        quotedString.setParseAction(pp.removeQuotes)
        tag_matcher = (
            Suppress("tags")
            + Suppress("[")
            + pp.delimitedList(quotedString)
            + Suppress("]")
        )
        image_matcher = Suppress("image")

        matcher = tag_matcher.set_parse_action(
            get_filtered_tags
        ) | image_matcher.set_parse_action(handle_image)

        return matcher

    # One-for-one replacements in the mapping string.
    # e.g. "{{ id }}" is replaced by term.termid.
    replacements = {
        "id": term.termid,
        "term": term.text,
        "language": term.language,
        "parents": ", ".join(term.parents),
        "tags": ", ".join(term.tags),
        "translation": term.translation,
    }

    all_keys = set(re.findall(r"{{\s*(.*?)\s*}}", mapping_string))
    parser = build_key_parser()
    calc_replacements = {
        # Matchers return the value that should be used as the
        # replacement value for the given mapping string.  e.g.
        # tags["der", "die"] returns "der" if term.tags = ["der", "x"]
        k: parser.parseString(k).asList()[0]
        for k in all_keys
        if k not in replacements
    }

    def get_field_mapping_json(map_string, replacements):
        final = map_string
        for k, v in replacements.items():
            pattern = rf"{{{{\s*{re.escape(k)}\s*}}}}"
            final = re.sub(pattern, f"{v}", final)

        postjson = {}
        mappings = [s.strip() for s in final.split("\n") if s.strip() != ""]
        for s in mappings:
            field, val = s.split(":", 1)
            postjson[field.strip()] = val.strip()
        return postjson

    all_actions = [{"action": "storeMediaFile", "params": p} for p in media_actions]
    all_actions.append(
        {
            "action": "addNote",
            "params": {
                "note": {
                    "deckName": deck_name,
                    "modelName": model_name,
                    "fields": get_field_mapping_json(
                        mapping_string, {**replacements, **calc_replacements}
                    ),
                    "tags": ["lute"] + term.tags,
                }
            },
        }
    )

    return {"action": "multi", "params": {"actions": all_actions}}


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


the = Term()
the.termid = 43
the.text = "aucher"
the.language = "German"
the.parents = ["hello", "there"]
the.translation = 'also "here"'
the.tags = ["der", "blah", "xxx", "yyy"]
# TODO - need to fix this URL trash stored in the table, should just store the filename
the.image = "/userimages/3/Geschenk.jpeg"

# images served from userimages in app_config
IMAGE_ROOT_DIR = "/Users/jeff/Documents/Projects/lute/data"

test_string = """\
Extra_info_back: {{ id }}
Word: {{ term }}
Plural: some value {{ parents }}
Article: {{ tags["der", "die", "das"] }}: {{ term }}
Picture: {{ image }}
Sentence: some text {{ parents }} more text {{ parents }}
Definition: {{ translation }}
"""

p = build_ankiconnect_post_json(
    the, test_string, IMAGE_ROOT_DIR, "zzTestAnkiConnect", "Basic_vocab"
)
print("=" * 25)
print(json.dumps(p, indent=2))
print("=" * 25)


do_post = False
if do_post:
    ANKI_CONNECT_URL = "http://localhost:8765"
    ret = requests.post(ANKI_CONNECT_URL, json=p, timeout=5)
    rj = ret.json()
    print(rj)
