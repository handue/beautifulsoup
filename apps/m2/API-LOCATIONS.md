# Original API locations

These line numbers refer to the unmodified professor distribution, preserved in
`baseline/original-bs4.tar.gz` and Git commit `67a07d8`.
`baseline/sha256.json` records SHA-256 hashes for every original Python source file.
The archive contains the original Python files. Test input files are also
preserved in the original Git commit.

The API list was checked against the eight M1 task programs, copied in
`baseline/milestone1/`.

| API definition | Original source location |
|---|---|
| `BeautifulSoup.__init__` | `bs4/__init__.py:209` |
| `PageElement.get_text` | `bs4/element.py:524` |
| `PageElement.find_parent` | `bs4/element.py:992` |
| `Tag.__init__` | `bs4/element.py:1618` |
| `Tag.__setitem__` | `bs4/element.py:2223` |
| `Tag.prettify` | `bs4/element.py:2601` |
| `Tag.find` | `bs4/element.py:2684` |
| `Tag.find_all` | `bs4/element.py:2715` |
| `SoupStrainer.__init__` | `bs4/filter.py:345` |
| `SoupStrainer.allow_tag_creation` | `bs4/filter.py:580` |

| Application | Confirmed BeautifulSoup usage |
|---|---|
| M1 task1 | `BeautifulSoup(...)`, `Tag.prettify()` |
| M1 task2 | `BeautifulSoup(...)`, `Tag.find_all("a")` |
| M1 task3 | `BeautifulSoup(...)`, `Tag.find_all(True)` |
| M1 task4 | `BeautifulSoup(...)`, `Tag.find_all(id=True)` |
| M1 task5 | `BeautifulSoup(...)`, `Tag.find("a", href=True)`, `PageElement.find_parent()`, `Tag.name` |
| M1 task6 | `BeautifulSoup(...)`, `Tag.find_all("b")`, assignment to `Tag.name`, `Tag.prettify()` |
| M1 task7 | `BeautifulSoup(...)`, `Tag.find_all("p")`, `Tag.__setitem__` via `tag["class"] = "test"`, `Tag.prettify()` |
| M1 task8 | `BeautifulSoup(...)`, `PageElement.get_text(separator="\n", strip=True)` |
| M2 task2 | `SoupStrainer("a")`, `BeautifulSoup(..., parse_only=...)`, `Tag.find_all("a")` |
| M2 task3 | `SoupStrainer(True)`, `BeautifulSoup(..., parse_only=...)`, `Tag.find_all(True)` |
| M2 task4 | `SoupStrainer(id=True)`, `BeautifulSoup(..., parse_only=...)`, `Tag.find_all(id=True)` |

`Tag.name` is an instance attribute, not a method or property setter. Its original
initialization is `bs4/element.py:1648` (`self.name = name`). M1 task6 assigns
that attribute directly; there is no separate rename API definition.
Printing tags calls `Tag.__repr__`, defined at `bs4/element.py:2298`.
`Tag.__str__` is an alias assigned at `bs4/element.py:2302`.

SoupStrainer tests incoming start tags through `allow_tag_creation()`.
BeautifulSoup calls it in `handle_starttag()` at original `bs4/__init__.py:1024`.
Once a matching parent is accepted, its entire subtree is retained. Therefore
M2 task4 still uses `find_all(id=True)` to exclude retained children without IDs.
Likewise task2 uses `find_all("a")` to print anchors rather than their descendants.
