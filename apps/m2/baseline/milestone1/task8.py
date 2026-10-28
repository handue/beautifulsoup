import argparse
from pathlib import Path

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(
        description="Extract and print document text using get_text()."
    )
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"

    soup = BeautifulSoup(input_path.read_bytes(), parser_name)

    print(soup.get_text(separator="\n", strip=True))


if __name__ == "__main__":
    main()
