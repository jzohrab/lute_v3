"DSL Parsing with pyparsing"

from typing import Callable, Iterable

import pyparsing as pp
from pyparsing import (
    infixNotation,
    opAssoc,
    Keyword,
    Word,
    ParserElement,
    nums,
    one_of,
    quotedString,
    QuotedString,
    Suppress,
    Literal,
)


class Term:
    "Stub term class."

    def __init__(self):
        self.language = None
        self.text = None
        self.tags = []
        self.parents = []
        self.image = None


quoteval = QuotedString(quoteChar='"')
quotedString.setParseAction(pp.removeQuotes)
list_of_values = pp.delimitedList(quotedString)

tagvallist = Suppress("[") + list_of_values + Suppress("]")
tagcrit = tagvallist | quoteval

tag_matcher = Suppress("tags") + Suppress(":") + tagcrit

lang_matcher = Suppress("language") + Suppress(":") + quoteval

has_options = Literal("image")
has_matcher = Suppress("has") + Suppress(":") + has_options

comparison_op = one_of("< <= > >= != = == <>")
integer = Word(nums).setParseAction(lambda x: int(x[0]))

parent_count_matcher = (
    Suppress("parents") + Suppress(".") + Suppress("count") + comparison_op + integer
)

###############
# CHECKS


def test_matcher(title, examples, matcher):
    "Try out matchers."
    exes = [
        ex for ex in examples.split("\n") if ex.strip() != "" and not ex.startswith("#")
    ]
    for ex in exes:
        parsed = matcher.parseString(ex).asList()
        print(f"{title}: {ex} => {parsed}")


parent_count_examples = """
parents.count = 1
parents.count > 0
parents.count >= 2
"""
test_matcher("PCOUNT", parent_count_examples, parent_count_matcher)

tag_examples = """
tags:"m"
tags:["m"]
tags:["m", "f"]
tags:["子供", "ko"]
"""
test_matcher("TAGS", tag_examples, tag_matcher)

lang_examples = """
language:"German"
"""
test_matcher("LANGS", lang_examples, lang_matcher)

img_examples = """
has:image
# has:blah
"""
test_matcher("IMG", img_examples, has_matcher)

###############

# sys.exit(0)

term = Term()
term.language = "German"
term.tags = ["m", "x"]
term.image = "something.jpg"


def has_any_matching_tags(tagvals):
    return any(e in term.tags for e in tagvals)


def matches_lang(lang):
    return term.language == lang[0]


def check_has(args):
    "Check has:x"
    has_item = args[0]
    if has_item == "image":
        return term.image is not None
    raise RuntimeError(f"Unhandled has check for {has_item}")


def check_parent_count(args):
    "Check parents."
    opMap = {
        "<": lambda a, b: a < b,
        "<=": lambda a, b: a <= b,
        ">": lambda a, b: a > b,
        ">=": lambda a, b: a >= b,
        "!=": lambda a, b: a != b,
        "=": lambda a, b: a == b,
        "==": lambda a, b: a == b,
    }
    opstring, val = args
    oplambda = opMap[opstring]
    pcount = len(term.parents)
    return oplambda(pcount, val)


check_tags = tag_matcher.add_parse_action(has_any_matching_tags)
check_lang = lang_matcher.add_parse_action(matches_lang)
check_image = has_matcher.add_parse_action(check_has)
check_parent_count = parent_count_matcher.add_parse_action(check_parent_count)


ParserElement.enablePackrat()


class BoolNot:
    "Not unary operator."

    def __init__(self, t):
        self.arg = t[0][1]

    def __bool__(self) -> bool:
        v = bool(self.arg)
        return not v

    def __str__(self) -> str:
        return "~" + str(self.arg)

    __repr__ = __str__


class BoolBinOp:
    "Binary operation."
    repr_symbol: str = ""
    eval_fn: Callable[[Iterable[bool]], bool] = lambda _: False

    def __init__(self, t):
        self.args = t[0][0::2]

    def __str__(self) -> str:
        sep = f" {self.repr_symbol} "
        return f"({sep.join(map(str, self.args))})"

    def __bool__(self) -> bool:
        return self.eval_fn(bool(a) for a in self.args)


class BoolAnd(BoolBinOp):
    repr_symbol = "&"
    eval_fn = all


class BoolOr(BoolBinOp):
    repr_symbol = "|"
    eval_fn = any


# define keywords and simple infix notation grammar for boolean
# expressions
AND = Keyword("and")
OR = Keyword("or")


# define expression, based on expression operand and
# list of operations in precedence order
multi_check = infixNotation(
    check_tags | check_lang | check_image | check_parent_count,
    [
        (AND, 2, opAssoc.LEFT, BoolAnd),
        (OR, 2, opAssoc.LEFT, BoolOr),
    ],
).setName("boolean_expression")


final_examples = """
language:"German" and tag["der", "die", "das"] and has:image
language:"German" and parents.count = 1 and has:image and tags:["plural", "plural and singular"]
language:"German" and parents.count > 0 and tags:"part participle"
language:"German" and parents.count >= 1 and has:image
"""

term.parents = ["hello", "there"]
use_examples = [e.strip() for e in final_examples.split("\n") if e.strip() != ""]
for e in use_examples:
    result = multi_check.parseString(e)
    print(f"{e}: {result}, {result[0]}")
    print(bool(result[0]))
