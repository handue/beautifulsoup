from pathlib import Path


def main():
    output = Path(__file__).resolve().parent / "work"
    output.mkdir(exist_ok=True)
    for suffix in ("html", "xml"):
        path = output / f"large.{suffix}"
        with path.open("w", encoding="utf-8") as document:
            document.write("<root>")
            for i in range(20000):
                attrs = f' id="item-{i}"' if i % 100 == 0 else ""
                document.write(f'<section{attrs}><p>{"sample text " * 30}</p>')
                if i % 50 == 0:
                    document.write(f'<a href="/{i}"><b>link {i}</b></a>')
                if i % 2 == 0:
                    document.write(f'<b data-row="{i}">bold <b>inner</b></b>')
                document.write("</section>")
            document.write("</root>")
        print(f"Created {path}: {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
