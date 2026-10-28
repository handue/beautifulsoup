import argparse
from pathlib import Path

from bs4 import BeautifulSoup, SoupReplacer


def main():
    parser = argparse.ArgumentParser(
        description="Replace <b> tags during parsing and save the tree."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("-o", "--output", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"
    soup = BeautifulSoup(
        input_path.read_bytes(), parser_name, replacer=SoupReplacer("b", "blockquote")
    )

    output_path = args.output
    if output_path is None:
        output_path = (
            Path(__file__).resolve().parent
            / "outputs"
            / "task6"
            / (f"{input_path.stem}-blockquote{input_path.suffix}")
        )
    if output_path.resolve() == input_path.resolve():
        parser.error("Output must be different from the input file.")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(soup.prettify(), encoding="utf-8")
    print(f"Saved modified document to: {output_path}")


if __name__ == "__main__":
    main()
