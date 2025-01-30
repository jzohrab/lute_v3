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


def evaluate_selector(s, term):
    "Parse the selector, return True or False for the given term."

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

    AND = Keyword("and")
    OR = Keyword("or")

    multi_check = infixNotation(
        tag_matcher.set_parse_action(has_any_matching_tags)
        | lang_matcher.set_parse_action(matches_lang)
        | has_matcher.set_parse_action(check_has)
        | parent_count_matcher.set_parse_action(check_parent_count),
        [
            (AND, 2, opAssoc.LEFT, BoolAnd),
            (OR, 2, opAssoc.LEFT, BoolOr),
        ],
    )

    result = multi_check.parseString(s)
    # print(f"{result}, {result[0]}")
    # print(bool(result[0]))
    return bool(result[0])


###############
# CHECKS


def test_matcher(title, examples, matcher):
    "Try out matchers."
    exes = [
        ex for ex in examples.split("\n") if ex.strip() != "" and not ex.startswith("#")
    ]
    for ex in exes:
        parsed = matcher.parseString(ex).asList()
        # print(f"{title}: {ex} => {parsed}")


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


class Term:
    "Stub term class."

    def __init__(self):
        self.language = None
        self.text = None
        self.tags = []
        self.parents = []
        self.image = None


term = Term()
term.language = "German"
term.parents = ["hello", "there"]
term.tags = ["der", "blah"]
term.image = "something.jpg"

final_examples = """
language:"German" and tags:["der", "die", "das"] and has:image
language:"German" and parents.count = 1
language:"German" and parents.count = 1 and has:image and tags:["plural", "plural and singular"]
language:"German" and parents.count > 0 and tags:"part participle"
language:"German" and parents.count >= 1 and has:image
"""
use_examples = [
    e.strip()
    for e in final_examples.split("\n")
    if e.strip() != "" and not e.startswith("#")
]
for e in use_examples:
    print(e)
    ret = evaluate_selector(e, term)
    print(ret)
