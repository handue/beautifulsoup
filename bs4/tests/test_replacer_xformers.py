import pytest

from bs4 import BeautifulSoup, SoupReplacer
from . import LXML_PRESENT

PARSERS = ["html.parser"] + (["lxml", "xml"] if LXML_PRESENT else [])


class TestSoupReplacerXformers:
    def test_name_xformer(self):
        markup = '<p>before <b title="bold">bold <i>both</i></b> after</p>'
        b_to_blockquote = SoupReplacer(
            name_xformer=lambda tag: "blockquote" if tag.name == "b" else tag.name
        )
        soup = BeautifulSoup(markup, "html.parser", replacer=b_to_blockquote)
        assert str(soup) == (
            '<p>before <blockquote title="bold">bold <i>both</i></blockquote> after</p>'
        )

        # same result as the M2 version
        old = BeautifulSoup(
            markup, "html.parser", replacer=SoupReplacer("b", "blockquote")
        )
        assert soup.prettify() == old.prettify()

        # every tag goes through the function, not just one name
        upper = SoupReplacer(name_xformer=lambda tag: tag.name.upper())
        soup = BeautifulSoup(markup, "html.parser", replacer=upper)
        assert [tag.name for tag in soup.find_all(True)] == ["P", "B", "I"]

    def test_attrs_xformer(self):
        markup = '<div id="a" class="x y"><p class="old">one</p><p>two</p></div>'

        def set_p_class(tag):
            if tag.name != "p":
                return tag.attrs
            return {**tag.attrs, "class": "test"}

        soup = BeautifulSoup(
            markup, "html.parser", replacer=SoupReplacer(attrs_xformer=set_p_class)
        )
        assert str(soup) == (
            '<div class="x y" id="a"><p class="test">one</p><p class="test">two</p></div>'
        )
        assert soup.div["class"] == ["x", "y"]

        # attributes that are not returned are dropped
        only_id = SoupReplacer(
            attrs_xformer=lambda tag: {k: v for k, v in tag.attrs.items() if k == "id"}
        )
        soup = BeautifulSoup(markup, "html.parser", replacer=only_id)
        assert str(soup) == '<div id="a"><p>one</p><p>two</p></div>'

    def test_xformer(self):
        markup = '<div class="a"><p class="b" id="keep">one</p><b>two</b></div>'

        def remove_class_attr(tag):
            if "class" in tag.attrs:
                del tag.attrs["class"]

        class_deleter = SoupReplacer(xformer=remove_class_attr)
        soup = BeautifulSoup(markup, "html.parser", replacer=class_deleter)
        assert str(soup) == '<div><p id="keep">one</p><b>two</b></div>'

        # xformer can touch more than attributes. The return value is ignored.
        def make_strong(tag):
            if tag.name == "b":
                tag.name = "strong"
                tag["data-was"] = "b"
                tag.string = tag.get_text().upper()
            return "whatever"

        soup = BeautifulSoup(
            markup, "html.parser", replacer=SoupReplacer(xformer=make_strong)
        )
        assert str(soup.div.contents[1]) == '<strong data-was="b">TWO</strong>'
        assert soup.p["class"] == ["b"]

    def test_runs_during_parsing(self):
        seen = []

        def record(tag):
            seen.append(tag.name)
            tag["data-seen"] = str(len(seen))

        class ObservedSoup(BeautifulSoup):
            # when <aside> opens, the two <b> before it should already be done
            def handle_starttag(self, name, *args, **kwargs):
                if name == "aside":
                    assert self.find("b") is None
                    assert len(self.find_all("blockquote")) == 2
                    assert seen == ["blockquote", "blockquote"]
                return super().handle_starttag(name, *args, **kwargs)

        markup = (
            '<root><b id="outer">one<b>two</b>three</b>'
            "<aside><i>unchanged</i></aside><b>four</b></root>"
        )
        replacer = SoupReplacer(
            name_xformer=lambda tag: "blockquote" if tag.name == "b" else tag.name,
            xformer=record,
        )
        for parser in PARSERS:
            seen.clear()
            soup = ObservedSoup(markup, parser, replacer=replacer)

            # inner tags close first. lxml adds html and body, skip those.
            assert [name for name in seen if name not in ("html", "body")] == [
                "blockquote", "blockquote", "i", "aside", "blockquote", "root"
            ]
            # each tag was visited exactly once
            tags = soup.find_all(True)
            assert len(tags) == len(seen)
            assert sorted(int(tag["data-seen"]) for tag in tags) == list(
                range(1, len(seen) + 1)
            )
            assert soup.find("b") is None
            assert soup.find(id="outer").get_text() == "onetwothree"

            nodes = list(soup.descendants)
            for left, right in zip(nodes, nodes[1:]):
                assert left.next_element is right
                assert right.previous_element is left

    def test_all_three_together(self):
        markup = '<p><b class="x">one</b><i class="y">two</i></p>'
        calls = []

        def name_xformer(tag):
            calls.append(("name", tag.name, dict(tag.attrs)))
            return "strong" if tag.name == "b" else tag.name

        def attrs_xformer(tag):
            calls.append(("attrs", tag.name, dict(tag.attrs)))
            return {"data-was": tag.name} if tag.name == "b" else tag.attrs

        def xformer(tag):
            calls.append(("xformer", tag.name, dict(tag.attrs)))
            if tag.name == "strong":
                tag["data-done"] = "yes"

        soup = BeautifulSoup(
            markup,
            "html.parser",
            replacer=SoupReplacer(
                name_xformer=name_xformer, attrs_xformer=attrs_xformer, xformer=xformer
            ),
        )
        assert str(soup) == (
            '<p><strong data-done="yes" data-was="b">one</strong>'
            '<i class="y">two</i></p>'
        )
        # name and attrs both get the original <b>, xformer gets the result
        assert calls[:3] == [
            ("name", "b", {"class": ["x"]}),
            ("attrs", "b", {"class": ["x"]}),
            ("xformer", "strong", {"data-was": "b"}),
        ]
        assert [c[0] for c in calls] == ["name", "attrs", "xformer"] * 3

        # no arguments at all, nothing changes
        assert str(BeautifulSoup(markup, "html.parser", replacer=SoupReplacer())) == markup

    def test_bad_xformers(self):
        markup = "<p><b>one</b></p>"

        for keyword in ("name_xformer", "attrs_xformer", "xformer"):
            with pytest.raises(TypeError):
                SoupReplacer(**{keyword: "blockquote"})

        # can't mix with the M2 pair, and the functions are keyword only
        with pytest.raises(TypeError):
            SoupReplacer("b", "blockquote", xformer=lambda tag: None)
        with pytest.raises(TypeError):
            SoupReplacer("b", "blockquote", lambda tag: tag.name)

        for bad_name, error in [(None, TypeError), ("", ValueError), ("a b", ValueError)]:
            replacer = SoupReplacer(name_xformer=lambda tag: bad_name)
            with pytest.raises(error):
                BeautifulSoup(markup, "html.parser", replacer=replacer)

        # forgot to return the attrs
        replacer = SoupReplacer(attrs_xformer=lambda tag: None)
        with pytest.raises(TypeError):
            BeautifulSoup(markup, "html.parser", replacer=replacer)

        def explode(tag):
            raise KeyError(tag.name)

        with pytest.raises(KeyError):
            BeautifulSoup(markup, "html.parser", replacer=SoupReplacer(xformer=explode))
