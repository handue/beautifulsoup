import pytest

from bs4 import BeautifulSoup, SoupReplacer, SoupStrainer
from . import HTML5LIB_PRESENT, LXML_PRESENT


class TestSoupReplacer:
    def test_basic_replacement(self):
        markup = "<p>before <b title='bold'>bold</b> after</p>"
        soup = BeautifulSoup(
            markup, "html.parser", replacer=SoupReplacer("b", "blockquote")
        )
        assert (
            str(soup)
            == '<p>before <blockquote title="bold">bold</blockquote> after</p>'
        )
        assert BeautifulSoup(markup, "html.parser").b.name == "b"

        for names, error in [((None, "p"), TypeError), (("b", ""), ValueError)]:
            with pytest.raises(error):
                SoupReplacer(*names)
        with pytest.raises(TypeError):
            BeautifulSoup(markup, "html.parser", replacer="b")
        if HTML5LIB_PRESENT:
            with pytest.raises(NotImplementedError):
                BeautifulSoup(markup, "html5lib", replacer=SoupReplacer("b", "p"))

    def test_nested_replacement_during_parsing(self):
        class ObservedSoup(BeautifulSoup):
            def handle_starttag(self, name, *args, **kwargs):
                if name == "aside":
                    assert self.find("b") is None
                    assert len(self.find_all("blockquote")) == 2
                return super().handle_starttag(name, *args, **kwargs)

        markup = (
            '<root><b id="outer">one<b class="x">two</b>three</b>'
            "<aside><i>unchanged</i></aside><b>four</b><b/></root>"
        )
        parsers = ["html.parser"] + (["lxml", "xml"] if LXML_PRESENT else [])
        for parser in parsers:
            expected = BeautifulSoup(markup, parser)
            for tag in expected.find_all("b"):
                tag.name = "blockquote"
            soup = ObservedSoup(
                markup, parser, replacer=SoupReplacer("b", "blockquote")
            )
            assert str(soup) == str(expected)
            assert soup.find(id="outer").get_text() == "onetwothree"
            assert soup.find(class_="x")["class"] == (["x"] if parser != "xml" else "x")
            assert soup.i.string == "unchanged"
            for tag in soup.find_all(True):
                for child in tag.contents:
                    assert child.parent is tag
            nodes = list(soup.descendants)
            for left, right in zip(nodes, nodes[1:]):
                assert left.next_element is right
                assert right.previous_element is left

        for markup in ("<b>one<b>two", "<b>one</b>tail<b>two</b>", "<b/>"):
            expected = BeautifulSoup(markup, "html.parser")
            for tag in expected.find_all("b"):
                tag.name = "blockquote"
            soup = BeautifulSoup(
                markup, "html.parser", replacer=SoupReplacer("b", "blockquote")
            )
            assert str(soup) == str(expected)

        soup = BeautifulSoup(
            '<p>skip</p><b id="keep"><i>keep</i></b>',
            "html.parser",
            parse_only=SoupStrainer("b"),
            replacer=SoupReplacer("b", "blockquote"),
        )
        assert str(soup) == '<blockquote id="keep"><i>keep</i></blockquote>'
