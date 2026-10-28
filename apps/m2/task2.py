import argparse
from pathlib import Path

from bs4 import BeautifulSoup, SoupStrainer


def main():
    parser = argparse.ArgumentParser(
        description="Print all hyperlinks using SoupStrainer."
    )
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"
    strainer = SoupStrainer("a")
    soup = BeautifulSoup(input_path.read_bytes(), parser_name, parse_only=strainer)

    for tag in soup.find_all("a"):
        print(tag)


if __name__ == "__main__":
    main()
