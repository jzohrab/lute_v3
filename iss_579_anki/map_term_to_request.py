"Mapping field demo."

import re
import pyparsing as pp
from pyparsing import (
    quotedString,
    QuotedString,
    Suppress,
)


test_string = """\
fid: {{ id }}
field0: {{ term }}
field1: some value {{ parents }}
field2: {{ tags }}
field3: {{ tags["der", "die", "das"] }} {{ term }}
field4: {{ image }}
field5: some text {{ parents }} more text {{ parents }}
field6: {{ translation }}
"""

print(test_string)

# Define regex pattern to capture text inside {{ }}
pattern = r"{{\s*(.*?)\s*}}"

keys = set(re.findall(pattern, test_string))
print(keys)

# For each key, eval the value, build the dict

plain_replacements = {
    "id": "ID",
    "term": "TERM",
    "language": "L",
    "parents": "P",
    "image": "IM",
    "tags": "TAGS",
    "translation": "T",
}

calc_required = [k for k in keys if k not in plain_replacements]
print(calc_required)


# Tags selector
term_tags = ["der", "xxxx", "yyyy"]


def get_filtered_tags(tagvals):
    "Get tags matching the spec."
    # tagvals is a pyparsing ParseResults, convert to strings.
    real_tagvals = list(tagvals)
    ftags = [t for t in term_tags if t in real_tagvals]
    # print(f"got filtered tags {ftags}")
    return ", ".join(ftags)


quoteval = QuotedString(quoteChar='"')
quotedString.setParseAction(pp.removeQuotes)
list_of_values = pp.delimitedList(quotedString)
tagvallist = Suppress("[") + list_of_values + Suppress("]")
tag_matcher = Suppress("tags") + tagvallist
tag_match_result = tag_matcher.add_parse_action(get_filtered_tags)


matcher = tag_match_result

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
    # print(f"Replacing {k} => {v} using pattern {pattern}")
    final = re.sub(pattern, v, final)

print("=" * 25)
print(final)
print("=" * 25)
