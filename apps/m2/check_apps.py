import argparse
import hashlib
from pathlib import Path
import subprocess
import sys

from bs4 import BeautifulSoup, SoupStrainer


def output_digest(script, sample):
    process = subprocess.Popen(
        [sys.executable, str(script), str(sample)], stdout=subprocess.PIPE
    )
    digest = hashlib.sha256()
    size = 0
    while chunk := process.stdout.read(1024 * 1024):
        digest.update(chunk)
        size += len(chunk)
    assert process.wait() == 0
    return digest.hexdigest(), size


def main():
    arguments = argparse.ArgumentParser(description="Compare M2 applications with M1.")
    arguments.add_argument("milestone1", type=Path)
    args = arguments.parse_args()
    milestone1 = args.milestone1.resolve()
    apps = Path(__file__).resolve().parent
    samples = [
        milestone1 / "samples/task-demo.html",
        milestone1 / "samples/xml-schema.xml",
        apps / "work/large.html",
        apps / "work/large.xml",
        milestone1 / "samples/html-standard.html",
    ]
    with (apps / "application-checks.txt").open("w", encoding="utf-8") as log:
        for sample in samples:
            parser = "xml" if sample.suffix == ".xml" else "html.parser"
            for task in (2, 3, 4):
                original = output_digest(milestone1 / f"task{task}.py", sample)
                current = output_digest(apps / f"task{task}.py", sample)
                if original != current:
                    assert sample.name == "html-standard.html" and task == 4
                    full = BeautifulSoup(sample.read_bytes(), parser).find_all(id=True)
                    partial = BeautifulSoup(
                        sample.read_bytes(), parser, parse_only=SoupStrainer(id=True)
                    ).find_all(id=True)
                    assert [(t.name, dict(t.attrs)) for t in full] == [
                        (t.name, dict(t.attrs)) for t in partial
                    ]
                    differences = [
                        x.get("id") for x, y in zip(full, partial) if str(x) != str(y)
                    ]
                    assert differences == ["img-contain-size"]
                    message = (
                        f"{sample.name}: task{task}: {len(full)} identical tag names/attributes; "
                        f"whitespace differs only in img-contain-size; bytes={original[1]}/{current[1]}"
                    )
                else:
                    message = (
                        f"{sample.name}: task{task}: identical output; "
                        f"bytes={current[1]}; sha256={current[0]}"
                    )
                print(message, flush=True)
                log.write(message + "\n")
                log.flush()

            output = apps / "work" / f"{sample.stem}-task6{sample.suffix}"
            subprocess.run(
                [
                    sys.executable,
                    str(apps / "task6.py"),
                    str(sample),
                    "-o",
                    str(output),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
            )
            expected = BeautifulSoup(sample.read_bytes(), parser)
            for tag in expected.find_all("b"):
                tag.name = "blockquote"
            assert output.read_text(encoding="utf-8") == expected.prettify()
            message = (
                f"{sample.name}: task6: identical prettified output to M1 replacement"
            )
            print(message, flush=True)
            log.write(message + "\n")
            log.flush()


if __name__ == "__main__":
    main()
