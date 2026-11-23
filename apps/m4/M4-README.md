# Milestone 4

## Setup

Same as Milestone 2. Run from the project root.

```sh
python -m pip install -e .
python -m pip install pytest lxml
```

## Files

- API: `BeautifulSoup.__iter__` in `bs4/__init__.py`
- Tests: `bs4/tests/test_soup_iteration.py` (5 tests)
- Application: `apps/m4/iterate.py`

## New API

A `BeautifulSoup` object can now be used directly in a `for` loop. It visits
every node of the tree, in document order, one at a time.

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_doc, "html.parser")
for node in soup:
    print(node)
```

`soup` is still the object the constructor returns, there is no wrapper or
separate iterator class. Tags, strings, comments and doctypes are all
produced. The `BeautifulSoup` object itself is not, because it is the
container and not a node in the document.

The implementation is one method:

```python
def __iter__(self):
    return self.descendants
```

`Tag.descendants` already is a generator. It remembers the next node, yields
the current one, and moves on through `next_element`. So nothing is collected
into a list, and memory use does not grow with the size of the document.
(The tree itself is of course in memory, the iteration adds nothing to it.)

## Application

`apps/m4/iterate.py` walks a file with `for node in soup`, prints the first
few nodes, and counts the node types.

```sh
python apps/m4/iterate.py page.html -n 8
python apps/m4/iterate.py data.xml
```

Files ending in `.xml` use the XML parser, everything else uses
`html.parser`. On Moby Dick (1.4 MB, 12,647 nodes) parsing took about 0.2 s
and the loop over all nodes about 2 ms.

## Tests

```sh
python -m pytest -q bs4/tests/test_soup_iteration.py
python -m pytest -q
```

1. `test_visits_every_node_in_document_order`: node types, tag names and
   strings of a small document, same order as `soup.descendants`, and the soup
   itself is not in the output.
2. `test_nodes_are_produced_lazily`: `iter(soup)` is a generator, nodes come
   one per `next()`, and a tag appended during the loop is still visited.
3. `test_tag_iteration_is_unchanged`: `for child in tag` still gives direct
   children only.
4. `test_html_and_xml_parsers`: `html.parser`, `lxml` and `xml`.
5. `test_empty_and_filtered_documents`: empty input, plain text, `parse_only`
   with a `SoupStrainer`, and a document built with a `SoupReplacer`.

All five pass. The full suite has the same 6 failures as before this change
(two in `test_fuzz.py`, one in `test_htmlparser.py`, three in `test_lxml.py`).
None of them involve iteration.

## Technical brief: iterating over a soup

### What I changed and what I left alone

Before this milestone `for x in soup` already worked, but only because
`BeautifulSoup` inherits `Tag.__iter__`, which returns `iter(self.contents)`.
For a whole document that is one or two top level nodes, so it was not very
useful. I did not change `Tag.__iter__`. Only `BeautifulSoup` overrides it.

I did that because `for child in tag` is how a lot of existing code looks at
the children of a tag, and `Tag` and `BeautifulSoup` share one interface. If
`Tag` iterated over all descendants, that code would silently start to
return much more. The cost of my choice is that the two classes now behave
differently: `for x in soup` is the whole tree, `for x in soup.div` is the
direct children. I think that is acceptable, since the soup is the document
and a tag is one element of it, and `soup.children` still gives the old
behavior. It is the one thing a new user could trip over, so it is in the
docstring.

### Why reuse `descendants`

`descendants` already walks the tree lazily and already handles the stop
condition (the node after the last descendant). Writing a second walker
would duplicate that, and the two could drift apart. With the override,
`for n in soup` and `for n in soup.descendants` are the same by definition,
and test 1 checks it.

### Behavior worth knowing

- Document order, depth first: a tag comes before its children.
- The walk follows `next_element` links, so the tree can be changed while
  looping, with one limit. Nodes appended after the current position are
  visited. But extracting the current node cuts its `next_element` link and
  the loop ends early. To remove nodes, collect them first (for example
  `[n for n in soup if ...]`) and extract after the loop.
- `len(soup)` and `x in soup` are unchanged. They still look at `contents`
  only. So `len(soup)` is not the number of nodes the loop gives. I did not
  want to make `len()` walk the whole tree on every call, and an `__iter__`
  that disagrees with `__len__` is a little odd, but both were already the
  case for `Tag`.
- Nothing here depends on the parser, so `html.parser`, `lxml` and `xml` all
  work. It also works with `parse_only` and `SoupReplacer`, because both
  change what ends up in the tree and iteration only reads the tree.

### Recommendation

I would keep it this small. The alternative is a new method such as
`soup.walk()`, but the assignment asks for the soup object itself to be
iterable, and `descendants` stays available for people who want the explicit
name. If the team later wants to filter while iterating (only tags, only
strings), that fits better as a separate method than as arguments to
`__iter__`, since `__iter__` cannot take arguments.
