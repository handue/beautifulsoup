# Milestone 3

## Setup

Same as Milestone 2. Run from the project root.

```sh
python -m pip install -e .
python -m pip install pytest lxml
```

## Files

- API: `bs4/replacer.py`. The parser calls it from `popTag()` in `bs4/__init__.py`.
- Tests: `bs4/tests/test_replacer_xformers.py` (6 tests)
- Application: `apps/m3/task7.py`

## New API

```python
SoupReplacer(name_xformer=None, attrs_xformer=None, xformer=None)
```

- `name_xformer(tag)` returns the new name of the tag.
- `attrs_xformer(tag)` returns the new attributes of the tag.
- `xformer(tag)` changes the tag directly and returns nothing.

```python
from bs4 import BeautifulSoup, SoupReplacer

b_to_blockquote = SoupReplacer(
    name_xformer=lambda tag: "blockquote" if tag.name == "b" else tag.name
)
print(BeautifulSoup(html_doc, "html.parser", replacer=b_to_blockquote).prettify())

def remove_class_attr(tag):
    if "class" in tag.attrs:
        del tag.attrs["class"]

class_deleter = SoupReplacer(xformer=remove_class_attr)
print(BeautifulSoup(html_doc, "html.parser", replacer=class_deleter).prettify())
```

I extended the existing constructor instead of adding a second class, so
`SoupReplacer("b", "blockquote")` from M2 still works. The three functions are
keyword-only. Passing a tag pair and a function together raises `TypeError`,
because it was not clear to me which one should win.

Some details about how it behaves:

- The functions run in `popTag()`, when a tag is closed. This is the same place
  M2 used. The tree is not traversed again after parsing.
- Because it runs at closing time, the function gets a tag that already has its
  attributes and children. Children are transformed before their parent.
- The parser itself still works with the original names. If `b` is renamed to
  `blockquote`, the `</b>` end tag is still matched correctly. `SoupStrainer`
  also matches the original names.
- If more than one function is given, `name_xformer` and `attrs_xformer` both
  see the original tag. Then the name and attributes are set, and `xformer`
  runs last.
- `name_xformer` has to return a valid name and `attrs_xformer` has to return a
  dictionary. Otherwise parsing fails with an error. I did this mainly because
  it is easy to forget the `return` in `attrs_xformer`, and then every tag
  would silently lose its attributes.
- Works with `html.parser`, `lxml` and `xml`. html5lib is still not supported,
  same as M2.

## Application

M1 task 7: find all the `<p>` tags and add (or replace) a class attribute
`class="test"`, then write the tree onto a file.

```sh
python apps/m3/task7.py input.html
python apps/m3/task7.py input.xml -o result.xml
```

The M1 program parsed the file and then looped over `find_all("p")`. The new
one passes `SoupReplacer(attrs_xformer=add_test_class)` to `BeautifulSoup`, so
the `<p>` tags get the class while the file is being parsed and there is no
loop. Files ending in `.xml` use the XML parser, everything else uses
`html.parser`. The default output is
`apps/m3/outputs/task7/<stem>-test-class<suffix>`.

## Tests

```sh
python -m pytest -q bs4/tests/test_replacer_xformers.py
python -m pytest -q
```

1. `test_name_xformer`: the example from the assignment, compared with the M2 pair.
2. `test_attrs_xformer`: add or replace `class` on `<p>`, and dropping attributes.
3. `test_xformer`: the `remove_class_attr` example, plus changing name and contents.
4. `test_runs_during_parsing`: checks that earlier tags are already changed when
   a later tag starts, on all three parsers.
5. `test_all_three_together`: the order when all three functions are given.
6. `test_bad_xformers`: non-callables, mixing with a pair, wrong return values.

All six pass, and the two M2 tests still pass. The failures in the full suite
are the same ones described in the M2 README. None of them use `SoupReplacer`.

## Technical brief: M2 API vs M3 API

### Recommendation

I would recommend the M3 API (functions) as the actual extension, and keep the
M2 pair only as a shortcut for the simple rename case.

### Why

The M2 API can do one thing: rename one tag name to another. That was enough
for M1 task 6, but it already fails for task 7, which needs to change an
attribute. To support that with the M2 style we would have to add another
kind of argument, and then another one for the next request (several pairs,
rename only if some attribute is present, remove an attribute, and so on).
The API would keep growing.

With functions the user writes the rule, so the library does not need to know
about each case. Task 7 is four lines:

```python
def add_test_class(tag):
    if tag.name != "p":
        return tag.attrs
    return {**tag.attrs, "class": "test"}
```

It also fits how BeautifulSoup already works. `find_all()` and `SoupStrainer`
take a string for the simple case and a function when the user needs more, so
a replacer that takes functions should not surprise anyone who knows the
library.

### What is still good about the pair

- It is very easy to read and hard to get wrong.
- It can be fully checked in the constructor. A function can only be checked
  when it runs.
- It is plain data, so it could come from a config file.

So I would not remove it. But it is the same thing as one `name_xformer`, so
it does not need to be a separate design.

### Problems with the M3 API

**`xformer` can do too much.** It gets the real tag while its parent is still
being built. Changing the tag's own name, attributes or contents is fine and
is tested. Removing the tag from the tree or changing its parent inside the
function is not something the parser expects. I did not try to block this, I
think it should just be documented. For the same reason I would tell users to
prefer `name_xformer` and `attrs_xformer` when they are enough, because those
only return a value and the library can check it.

**Timing is not obvious.** A user might expect the function to run when the
tag opens. I kept it at closing time because renaming at opening time breaks
end tag matching in `html.parser` (the parser looks for an open `b` and finds
`blockquote`). The downside is that the function sees a finished tag but not
the rest of the document, so it cannot depend on later siblings. This needs
to be in the documentation.

**The three functions overlap.** Anything `name_xformer` or `attrs_xformer`
does can also be done with `xformer`. It is a bit redundant, but the first two
are simpler to write as lambdas, so I think keeping all three is fine.

**It is not faster.** The replacer calls a Python function for every tag,
while the M1 loop only touches the `<p>` tags, so I would not expect it to be
quicker. Parsing takes almost all of the time either way. The benefit is not
speed. It is that the rule is given once in the constructor and the rest of
the program never sees the tree before the change.

**html5lib.** Neither API works with it. If this were proposed for the real
library, that would have to be fixed first, since silently ignoring the
replacer for one parser would be worse than the current error.

### Summary

Use the function API. Keep `SoupReplacer(og_tag, alt_tag)` as a convenience.
Document that the functions run when a tag closes and that `xformer` should
only modify the tag it is given. Add html5lib support before calling it done.