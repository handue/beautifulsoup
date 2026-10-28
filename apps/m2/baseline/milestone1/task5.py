import argparse
from pathlib import Path

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(
        description="Find the paragraph containing the first hyperlink."
    )
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"

    soup = BeautifulSoup(input_path.read_bytes(), parser_name)

    link = soup.find("a", href=True)

    if link is None:
        print("No hyperlink found.")
        return

    parent = link.find_parent()

    print("First hyperlink:")
    print(link)

    if parent is None:
        print("No parent tag found.")
    else:
        print(f"Containing element: <{parent.name}>")
        print(parent)


if __name__ == "__main__":
    main()
