import argparse
from pathlib import Path

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(
        description="Replace all <b> tags with <blockquote> tags and save the document."
    )

    parser.add_argument("input_file", type=Path)
    args = parser.parse_args()

    input_path = args.input_file
    parser_name = "xml" if input_path.suffix.lower() == ".xml" else "html.parser"

    soup = BeautifulSoup(input_path.read_bytes(), parser_name)

    for tag in soup.find_all("b"):
        tag.name = "blockquote"

    output_dir = Path(__file__).resolve().parent / "outputs" / "task6"

    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / (f"{input_path.stem}-blockquote{input_path.suffix}")
    output_path.write_text(soup.prettify(), encoding="utf-8")

    print(f"Saved modified document to: {output_path}")


if __name__ == "__main__":
    main()
