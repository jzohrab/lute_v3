# Test input
test_string = """\
field0: {{ term }}
field1: some value {{ parents }}
field2: {{ tags }}
field3: {{ tags["der", "die", "das"] }} {{ term }}
field4: {{ image }}
field5: some text {{ parents }} more text {{ parents }}
field6: {{ translation }}
"""

print(test_string)

import re

# Define regex pattern to capture text inside {{ }}
pattern = r"{{\s*(.*?)\s*}}"

keys = set(re.findall(pattern, test_string))
print(keys)

# For each key, eval the value, build the dict

plain_replacements = {
    "term": "TERM",
    "language": "L",
    "parents": "P",
    "image": "IM",
    "tags": "TAGS",
    "translation": "T",
}

calc_required = [k for k in keys if k not in plain_replacements]
print(calc_required)

import pyparsing as pp
from pyparsing import (
    Word,
    alphas,
    nums,
    one_of,
    quotedString,
    QuotedString,
    infix_notation,
    OpAssoc,
    Suppress,
    OneOrMore,
    Group,
    Optional,
    ParseException,
    Literal,
    Forward,
)

# Tags selector
term_tags = ["der", "xxxx", "yyyy"]


def get_filtered_tags(tagvals):
    # print(f"checking term tags {term_tags} vs {tagvals}")
    # tagvals is a pyparsing ParseResults, convert to strings.
    real_tagvals = [t for t in tagvals]
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

print(final)

import sys

sys.exit(0)


ss = [s.strip() for s in test_string.split("\n") if s.strip() != ""]
for s in ss:
    matches = re.findall(pattern, s)
    print(matches)


### pyparsing will mostly _not_ be useful here ... the only thing it might be useful for would be the tags


from pyparsing import (
    Word,
    alphas,
    nums,
    QuotedString,
    Suppress,
    delimitedList,
    Group,
    OneOrMore,
    Regex,
    Optional,
)

# Define grammar for extracting property lookups
identifier = Word(alphas)  # Simple property names like term, parents, image

# Match tags with optional list arguments, e.g., tags["der", "die", "das"]
tag_expr = Group(
    Suppress("tags")
    + Optional(Suppress("[") + delimitedList(QuotedString('"')) + Suppress("]"))
).setParseAction(lambda t: ["tags", t.asList()] if t else ["tags", None])

# Property lookup inside {{ ... }}, allowing term, parents, image, or tags["..."]
property_lookup = Suppress("{{") + (tag_expr | identifier) + Suppress("}}")

# Matches any text that is not a property lookup
text = Regex(r"[^{}\n]+")  # Anything except {{ }}

# Define a full field mapping
field_name = Word(alphas + nums + "_")  # field0, field1, fieldX, etc.
field_value = OneOrMore(property_lookup | text)  # Mix of text and lookups

from pyparsing import (
    Word,
    Keyword,
    nums,
    OneOrMore,
    Optional,
    Suppress,
    Literal,
    alphanums,
    LineEnd,
    LineStart,
    Group,
    ParserElement,
)

# ParserElement.setDefaultWhitespaceChars(" \t")

NL = Suppress(LineEnd())

# Full field mapping: field_name: field_value
field = Group(field_name + Suppress(":") + Group(field_value) + NL)

# Parse multiple fields
mapping_parser = OneOrMore(field)

# Parse the mapping string
parsed_result = mapping_parser.parseString(test_string, parseAll=True)
print(parsed_result)
import sys

sys.exit(0)

# Convert parsed structure into a dictionary
output = {}
for field in parsed_result:
    name = field[0]
    values = field[1:]
    output[name] = values

# Print the parsed structure
import pprint

pprint.pprint(output)
