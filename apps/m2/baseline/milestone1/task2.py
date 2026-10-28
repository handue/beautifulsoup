import argparse
from pathlib import Path

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(
        description="Parse an HTML/XML file and print all <a> tags"
    )

    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"

    soup = BeautifulSoup(input_path.read_bytes(), parser_name)

    for link in soup.find_all("a"):
        print(link)


if __name__ == "__main__":
    main()
