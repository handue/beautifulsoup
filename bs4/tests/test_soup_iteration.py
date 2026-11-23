import types

from bs4 import BeautifulSoup, SoupReplacer, SoupStrainer
from bs4.element import Comment, NavigableString, Tag
from . import LXML_PRESENT

PARSERS = ["html.parser"] + (["lxml", "xml"] if LXML_PRESENT else [])

MARKUP = "<div><p>one <b>two</b></p><!--note--><p>three</p></div>"


class TestSoupIteration:
    def test_visits_every_node_in_document_order(self):
        soup = BeautifulSoup(MARKUP, "html.parser")
        nodes = list(soup)

        assert [type(n) for n in nodes] == [
            Tag, Tag, NavigableString, Tag, NavigableString,
            Comment, Tag, NavigableString,
        ]
        assert [n.name for n in nodes if isinstance(n, Tag)] == ["div", "p", "b", "p"]
        assert [str(n) for n in nodes if isinstance(n, NavigableString)] == [
            "one ", "two", "note", "three",
        ]
        # same nodes, same order as descendants
        assert all(a is b for a, b in zip(nodes, soup.descendants))
        assert len(nodes) == len(list(soup.descendants))
        # the soup object itself is not one of the nodes
        assert not any(n is soup for n in nodes)

    def test_nodes_are_produced_lazily(self):
        soup = BeautifulSoup(MARKUP, "html.parser")
        iterator = iter(soup)
        assert isinstance(iterator, types.GeneratorType)

        first = next(iterator)
        assert first is soup.div
        # the iterator advances one node per step
        assert next(iterator) is soup.p
        assert next(iterator) == "one "

        # nodes can be added while iterating and the walk still ends
        count = 0
        for node in soup:
            count += 1
            if node is soup.b:
                soup.b.append(soup.new_tag("i"))
        assert count == 9

    def test_tag_iteration_is_unchanged(self):
        soup = BeautifulSoup(MARKUP, "html.parser")
        # a Tag still iterates over its direct children only
        assert [c.name for c in soup.div if isinstance(c, Tag)] == ["p", "p"]
        assert len(list(soup.div)) == 3
        assert list(soup.b) == ["two"]
        # while the soup walks every node below it
        assert len(list(soup)) > len(soup.contents)

    def test_html_and_xml_parsers(self):
        markup = "<root><a id='1'>x</a><a id='2'/></root>"
        for parser in PARSERS:
            soup = BeautifulSoup(markup, parser)
            names = [n.name for n in soup if isinstance(n, Tag)]
            # lxml's HTML parser adds html and body around the fragment
            assert names[-3:] == ["root", "a", "a"], parser
            ids = [n.get("id") for n in soup if isinstance(n, Tag) and n.name == "a"]
            assert ids == ["1", "2"], parser
            assert list(soup) == list(soup.descendants), parser

    def test_empty_and_filtered_documents(self):
        assert list(BeautifulSoup("", "html.parser")) == []
        assert list(BeautifulSoup("just text", "html.parser")) == ["just text"]

        only_b = BeautifulSoup(MARKUP, "html.parser", parse_only=SoupStrainer("b"))
        assert [n.name for n in only_b if isinstance(n, Tag)] == ["b"]
        assert [str(n) for n in only_b] == ["<b>two</b>", "two"]

        # a replacer renames during parsing, iteration sees the new names
        renamed = BeautifulSoup(
            MARKUP, "html.parser", replacer=SoupReplacer("b", "blockquote")
        )
        assert [n.name for n in renamed if isinstance(n, Tag)] == [
            "div", "p", "blockquote", "p",
        ]
