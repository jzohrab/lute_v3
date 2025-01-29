# Test input
test_string = """\
field0: {{ term }}
field1: some value {{ parents }}
field2: {{ tags }}
field3: {{ tags["der", "die", "das"] }} {{ term }}
field4: {{ image }}
field5: some text {{ parents }} and some more {{ parents }}
"""


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
