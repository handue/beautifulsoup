# References:
# 1. "Making the soup": creating a parse tree with BeautifulSoup(markup, parser).
#    Used in: BeautifulSoup(input_path.read_bytes(), parser_name)
#    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#making-the-soup
#
# 2. "Pretty-printing": using prettify() to format the tree with indentation.
#    Used in: soup.prettify()
#    https://www.crummy.com/software/BeautifulSoup/bs4/doc/#pretty-printing

import argparse
from pathlib import Path

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(
        description="Parse an HTML/XML file and save a prettified version."
    )
    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"

    soup = BeautifulSoup(input_path.read_bytes(), parser_name)

    output_dir = Path(__file__).resolve().parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / (f"{input_path.stem}-prettified{input_path.suffix}")
    output_path.write_text(soup.prettify(), encoding="utf-8")

    print(f"Saved prettified document to: {output_path}")


if __name__ == "__main__":
    main()
