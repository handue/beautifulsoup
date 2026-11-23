import argparse
from collections import Counter
from pathlib import Path

from bs4 import BeautifulSoup
from bs4.element import Tag


def main():
    parser = argparse.ArgumentParser(
        description="Walk every node of a document with `for node in soup`."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=20,
        help="how many nodes to print before only counting (default: 20)",
    )
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"
    soup = BeautifulSoup(input_path.read_bytes(), parser_name)

    kinds = Counter()
    # the loop below is the whole point of M4: no find_all(), no list of nodes
    for position, node in enumerate(soup):
        kinds["tag" if isinstance(node, Tag) else type(node).__name__] += 1
        if position < args.limit:
            label = f"<{node.name}>" if isinstance(node, Tag) else repr(str(node)[:40])
            print(f"{position:5}  {type(node).__name__:<16} {label}")

    print()
    print(f"nodes visited: {sum(kinds.values())}")
    for kind, count in kinds.most_common():
        print(f"  {kind}: {count}")


if __name__ == "__main__":
    main()
