import argparse
from pathlib import Path

from bs4 import BeautifulSoup, SoupReplacer


def add_test_class(tag):
    # non-p tags keep their attributes as they are
    if tag.name != "p":
        return tag.attrs
    return {**tag.attrs, "class": "test"}


def main():
    parser = argparse.ArgumentParser(
        description="Set every <p> tag's class to test during parsing and save the tree."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"

    # no find_all("p") loop like in M1, the replacer does it while parsing
    soup = BeautifulSoup(
        input_path.read_bytes(),
        parser_name,
        replacer=SoupReplacer(attrs_xformer=add_test_class),
    )

    output_path = args.output
    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent
            / "outputs"
            / "task7"
            / f"{input_path.stem}-test-class{input_path.suffix}"
        )
    if output_path.resolve() == input_path.resolve():
        parser.error("Output must be different from the input file.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(soup.prettify(), encoding="utf-8")
    print(f"Saved modified document to: {output_path}")


if __name__ == "__main__":
    main()
