"""
MandarinParser tests.
"""

import tempfile
import os
import pytest

# pylint: disable=wrong-import-order
from lute.models.term import Term
from lute.parse.base import ParsedToken

from lute_mandarin_parser.parser import MandarinParser


def test_token_count(mandarin_chinese):
    """
    token_count checks.
    """
    cases = [
        ("我", 1),
        ("运气", 1),
        ("你说", 2),
        ("我不相信", 3),
        ("我冒了严寒 ，回到相隔二千馀里，别了二十馀年的故乡去。", 21),
    ]
    for text, expected_count in cases:
        t = Term(mandarin_chinese, text)
        assert t.token_count == expected_count, text
        assert t.text_lc == t.text, "case"


def assert_tokens_equals(text, lang, expected):
    """
    Parsing a text using a language should give the expected parsed tokens.

    expected is given as array of:
    [ original_text, is_word, is_end_of_sentence ]
    """
    p = MandarinParser()
    actual = p.get_parsed_tokens(text, lang)
    expected = [ParsedToken(*a) for a in expected]
    assert [str(a) for a in actual] == [str(e) for e in expected]


def test_end_of_sentence_stored_in_parsed_tokens(mandarin_chinese):
    """
    ParsedToken is marked as EOS=True at ends of sentences.
    """
    s = "你好。吃饭了吗？现在是2024年。"

    expected = [
        ("你好", True),
        ("。", False, True),
        ("吃饭", True),
        ("了", True),
        ("吗", True),
        ("？", False, True),
        ("现在", True),
        ("是", True),
        ("2024", False, False),
        ("年", True),
        ("。", False, True),
    ]
    assert_tokens_equals(s, mandarin_chinese, expected)


def test_carriage_returns_treated_as_reverse_p_character(mandarin_chinese):
    """
    Returns need to be marked with the backwards P for rendering etc.
    """
    s = "你好。\n现在。"

    expected = [
        ("你好", True),
        ("。", False, True),
        ("¶", False, True),
        ("现在", True),
        ("。", False, True),
    ]
    assert_tokens_equals(s, mandarin_chinese, expected)


def test_readings():
    """
    Parser returns readings if they add value.
    """
    p = MandarinParser()

    no_reading = ["Hello"]  # roman  # only katakana  # only hiragana

    for c in no_reading:
        assert p.get_reading(c) is None, c

    cases = [("你好", "nǐ hǎo"), ("欢迎", "huān yíng"), ("中国", "zhōng guó")]

    for c in cases:
        assert p.get_reading(c[0]) == c[1], c[0]


@pytest.fixture(name="_datadir")
def datadir():
    "The data_directory for the plugin."
    with tempfile.TemporaryDirectory() as temp_dir:
        MandarinParser.data_directory = temp_dir
        MandarinParser.init_data_directory()
        exceptions_file = os.path.join(temp_dir, "parser_exceptions.txt")
        assert os.path.exists(exceptions_file), "File should exist after init"
        yield


def test_term_found_in_exceptions_file_is_split(mandarin_chinese, _datadir):
    "User can specify parsing exceptions in file."
    s = "清华大学"

    def parsed_tokens():
        p = MandarinParser()
        return [t.token for t in p.get_parsed_tokens(s, mandarin_chinese)]

    assert ["清华大学"] == parsed_tokens(), "No exceptions"

    exceptions_file = MandarinParser.parser_exceptions_file()
    assert os.path.exists(exceptions_file), "Sanity check only."

    def set_parse_exceptions(array_of_exceptions):
        with open(exceptions_file, "w", encoding="utf8") as ef:
            ef.write("\n".join(array_of_exceptions))

    set_parse_exceptions(["清华大学"])
    assert ["清华大学"] == parsed_tokens(), "mapped to self"

    set_parse_exceptions(["清华,大学"])
    assert ["清华", "大学"] == parsed_tokens(), "Exceptions consulted during parse"

    set_parse_exceptions(["清华,大,学"])
    assert ["清华", "大", "学"] == parsed_tokens(), "multiple splits tokens"

    set_parse_exceptions(["清华,大,学", "清华,大学"])
    assert ["清华", "大学"] == parsed_tokens(), "Last rule takes precedence"

    set_parse_exceptions(["清学"])
    assert ["清华大学"] == parsed_tokens(), "no match = parsed as-is"

    set_parse_exceptions(["清华,大学", "大,学"])
    assert ["清华", "大", "学"] == parsed_tokens(), "Recursive splitting"

    set_parse_exceptions(["大,学", "清华,大学"])
    assert ["清华", "大", "学"] == parsed_tokens(), "Order doesn't matter"

    set_parse_exceptions(["清华, 大学", " 大 ,  学 "])
    assert ["清华", "大", "学"] == parsed_tokens(), "Spaces are ignored"
