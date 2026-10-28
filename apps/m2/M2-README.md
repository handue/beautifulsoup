# Milestone 2

## Setup

This project uses the supplied BeautifulSoup 4.13.0 source. Tests were run on
macOS arm64 with Python 3.10.22 and lxml 6.1.3.

Run these commands from the project root with Python 3.10 installed.

```sh
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
python -m pip install -r apps/m2/requirements-tested.txt
```

## Part 1

```sh
python apps/m2/task2.py input.html
python apps/m2/task3.py input.html
python apps/m2/task4.py input.xml
```

Each program takes an input file. Files ending in `.xml` use the XML parser;
other files use `html.parser`.

| Program | Strainer | Output |
|---|---|---|
| task2.py | `SoupStrainer("a")` | All a tags |
| task3.py | `SoupStrainer(True)` | All tags |
| task4.py | `SoupStrainer(id=True)` | All tags with an id attribute |

A matching parent keeps its children too, so task2 and task4 still use
`find_all()` to select the output tags. Task3 must keep every tag and showed
no meaningful time or memory improvement. The programs still read the whole
input file; the savings come from creating fewer tree nodes.

## Part 2

These line numbers refer to the original source, preserved in
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

The same reference is kept in [API-LOCATIONS.md](API-LOCATIONS.md).

## Part 3

```python
from bs4 import BeautifulSoup, SoupReplacer

soup = BeautifulSoup(
    '<p><b id="example">one <b>two</b></b></p>',
    "html.parser",
    replacer=SoupReplacer("b", "blockquote"),
)
print(soup.prettify())
```

`SoupReplacer` stores the original and replacement names. BeautifulSoup accepts
it through the optional `replacer` argument.

The change happens in `popTag()` as each tag closes. The original name is kept
until closing-tag matching and stack bookkeeping finish, then the same Tag
object gets its new name. Contents, attributes, namespaces, and tree links stay
in place. Unclosed tags follow the same path when parsing ends. There is no
second traversal of the completed tree.

The added work is a name check for each closed tag, with constant extra space.
Without a replacer, parsing follows the existing behavior with one extra
optional-value check per closed tag.

The supported parsers are `html.parser`, `lxml`, and `xml`/`lxml-xml`.
The html5lib builder uses different hooks and raises `NotImplementedError`
when a replacer is supplied. Names match the parser's normalized local name;
XML namespace prefixes are preserved. When combined with `parse_only`, the
strainer matches the original names.

```sh
python apps/m2/task6.py input.html
python apps/m2/task6.py input.xml -o apps/m2/outputs/result.xml
```

Task6 saves the changed tree. Its default output is
`apps/m2/outputs/task6/<stem>-blockquote<suffix>`. It refuses to overwrite the
input file.

## Tests

```sh
python -m pytest -q bs4/tests/test_replacer.py
python -m pytest -q
```

The two new tests passed. They cover basic replacement and nested tags, with
checks for attributes, contents, unaffected tags, and tree links. A callback
checks that earlier tags have changed before a later tag starts parsing.

The original source had 823 passed, 6 failed, and 7 skipped. The modified source
had 825 passed, 6 failed, and 7 skipped. The six failures are the same in both
runs. Three concern malformed input accepted by the current Python parser;
three concern XHTML, processing instructions, and an out-of-range entity in
lxml. Full results are in `baseline-tests-python310.txt` and
`regression-tests.txt`. The new test output is in `replacer-tests.txt`.

The wheel and source distribution built successfully. The built wheel was also
imported and checked with a replacement example. No existing tests or parser
backends were changed.

## Build

After the setup steps, run this from the project root.

```sh
./build.sh
```

The script uses the active Python environment and the existing build settings
in `pyproject.toml`. It creates a wheel and source distribution in `dist/`.
It can also be run from another directory using its full path. Set `PYTHON`
to choose a different interpreter, or pass build options after the script name.
The script builds packages only; it does not publish them.

## Large-file checks

```sh
python apps/m2/create_samples.py
python apps/m2/check_apps.py /path/to/Milestone-1
```

`create_samples.py` writes an 8,142,300-byte HTML file and an XML file of the same
size under `apps/m2/work/`. Each has 60,801 tags, 400 links, 200 IDs, and 20,400
b tags, including nested matches.

`check_apps.py` compares the application output with the original M1 programs.
It expects the M1 task files and the samples `task-demo.html`, `xml-schema.xml`,
and `html-standard.html`. The existing HTML standard sample is 15,656,986 bytes.
The results are in `application-checks.txt`.

All generated-file outputs matched. On the HTML standard sample, task2, task3,
and task6 also matched. Task4 found the same 71,178 ID tags and attributes, but
lost two spaces inside `img-contain-size`. Its pre ancestor was excluded by
SoupStrainer, so a whitespace-only chunk was normalized. This is a limitation
of filtering out ancestors that provide parsing context.

## Performance

```sh
python apps/m2/create_samples.py
python apps/m2/benchmark.py apps/m2/work/large.html
python apps/m2/benchmark.py apps/m2/work/large.xml --output apps/m2/benchmark-results-xml.json
```

Both inputs are 8,142,300 bytes. Each case ran three times in a fresh process;
the tables show medians. Parse measures tree construction. Build also includes
the rename pass for the postparse case. Total includes file reading, selection,
serialization, and output hashing. Interpreter startup, imports, and actual
terminal or disk output are excluded. Memory is the process peak RSS.

The runner compares output hashes for equivalent cases. Baseline uses the
original source. Plain uses the modified source without a replacer. Postparse
uses the M1 rename loop, and replacer uses the new parsing hook. Baseline and
plain do not rename tags and are compared separately from the two rename cases.

### HTML

| Task | Mode | Parse (s) | Build (s) | Total (s) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|
| 2 | plain | 0.4876 | 0.4876 | 0.5053 | 104.2 |
| 2 | strained | 0.2625 | 0.2625 | 0.2662 | 48.2 |
| 3 | plain | 0.4640 | 0.4640 | 1.0042 | 122.7 |
| 3 | strained | 0.4541 | 0.4541 | 0.9926 | 122.8 |
| 4 | plain | 0.4596 | 0.4596 | 0.5051 | 104.2 |
| 4 | strained | 0.2845 | 0.2845 | 0.2904 | 48.7 |
| 6 | baseline | 0.4704 | 0.4704 | 0.6864 | 130.5 |
| 6 | plain | 0.4656 | 0.4656 | 0.6862 | 130.5 |
| 6 | postparse | 0.4640 | 0.4752 | 0.7103 | 130.1 |
| 6 | replacer | 0.4694 | 0.4694 | 0.6939 | 130.1 |

### XML

| Task | Mode | Parse (s) | Build (s) | Total (s) | Peak RSS (MiB) |
|---|---|---:|---:|---:|---:|
| 2 | plain | 0.3258 | 0.3258 | 0.3370 | 88.5 |
| 2 | strained | 0.1253 | 0.1253 | 0.1290 | 40.5 |
| 3 | plain | 0.3268 | 0.3268 | 0.9065 | 115.0 |
| 3 | strained | 0.3331 | 0.3331 | 0.9140 | 114.9 |
| 4 | plain | 0.3310 | 0.3310 | 0.3789 | 88.6 |
| 4 | strained | 0.1389 | 0.1389 | 0.1451 | 41.0 |
| 6 | baseline | 0.3268 | 0.3268 | 0.5529 | 114.8 |
| 6 | plain | 0.3365 | 0.3365 | 0.5602 | 114.9 |
| 6 | postparse | 0.3337 | 0.3433 | 0.5711 | 115.8 |
| 6 | replacer | 0.3348 | 0.3348 | 0.5667 | 115.7 |

SoupStrainer reduced time and memory for task2 and task4 on these inputs.
Task3 kept the whole tree and showed no meaningful improvement. SoupReplacer
removed the separate rename traversal, but the measured time and memory were
close to the postparse approach. These runs do not show a general speedup.

Raw measurements and environment details are in `benchmark-results.json` and
`benchmark-results-xml.json`. The programs were not tested on a GB-scale file
for M2.
