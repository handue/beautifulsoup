import argparse
import hashlib
import json
from pathlib import Path
import platform
import resource
import subprocess
import sys
import tarfile
import time


def measure(args):
    if args.mode == "baseline":
        sys.path.insert(0, str(Path(__file__).resolve().parent / "work/original"))
    from bs4 import BeautifulSoup, SoupStrainer
    import bs4

    started = time.perf_counter()
    markup = args.input_file.read_bytes()
    parser = "xml" if args.input_file.suffix.lower() == ".xml" else "html.parser"
    options = {}
    if args.mode == "strained":
        options["parse_only"] = {
            "2": SoupStrainer("a"),
            "3": SoupStrainer(True),
            "4": SoupStrainer(id=True),
        }[args.task]
    elif args.mode == "replacer":
        from bs4 import SoupReplacer

        options["replacer"] = SoupReplacer("b", "blockquote")
    parse_started = time.perf_counter()
    soup = BeautifulSoup(markup, parser, **options)
    parsed = time.perf_counter()
    if args.mode == "postparse":
        for tag in soup.find_all("b"):
            tag.name = "blockquote"
    transformed = time.perf_counter()
    digest = hashlib.sha256()
    if args.task == "6":
        output = soup.prettify().encode("utf-8")
        digest.update(output)
        count = len(soup.find_all("blockquote"))
    else:
        tags = {
            "2": lambda: soup.find_all("a"),
            "3": lambda: soup.find_all(True),
            "4": lambda: soup.find_all(id=True),
        }[args.task]()
        count = len(tags)
        for tag in tags:
            digest.update((str(tag) + "\n").encode("utf-8"))
    finished = time.perf_counter()
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    rss_mib = rss / (1024 * 1024 if sys.platform == "darwin" else 1024)
    print(
        json.dumps(
            {
                "task": args.task,
                "mode": args.mode,
                "parse_s": parsed - parse_started,
                "transform_s": transformed - parsed,
                "build_s": transformed - parse_started,
                "total_s": finished - started,
                "peak_mib": rss_mib,
                "count": count,
                "sha256": digest.hexdigest(),
                "bs4": bs4.__file__,
            }
        )
    )


def main():
    parser = argparse.ArgumentParser(
        description="Compare equivalent Milestone 2 workloads."
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("benchmark-results.json"),
    )
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--task", choices=["2", "3", "4", "6"])
    parser.add_argument(
        "--mode", choices=["baseline", "plain", "strained", "postparse", "replacer"]
    )
    args = parser.parse_args()
    if args.worker:
        measure(args)
        return
    if args.repeats < 1:
        parser.error("--repeats must be positive")
    original = Path(__file__).resolve().parent / "work/original"
    if not (original / "bs4/__init__.py").exists():
        original.mkdir(parents=True, exist_ok=True)
        with tarfile.open(
            Path(__file__).resolve().parent / "baseline/original-bs4.tar.gz"
        ) as archive:
            members = [
                m for m in archive.getmembers() if not m.name.startswith("bs4/tests/")
            ]
            archive.extractall(original, members=members, filter="data")
    rows = []
    cases = [(task, mode) for task in ["2", "3", "4"] for mode in ["plain", "strained"]]
    cases += [("6", mode) for mode in ["baseline", "plain", "postparse", "replacer"]]
    for repeat in range(args.repeats):
        for task, mode in cases[repeat % 2 :] + cases[: repeat % 2]:
            command = [
                sys.executable,
                str(Path(__file__).resolve()),
                str(args.input_file.resolve()),
                "--worker",
                "--task",
                task,
                "--mode",
                mode,
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=True)
            row = json.loads(result.stdout)
            row["repeat"] = repeat + 1
            rows.append(row)
            print(
                f"task{task} {mode}: {row['total_s']:.3f}s, {row['peak_mib']:.1f} MiB",
                flush=True,
            )
    for task in ["2", "3", "4"]:
        assert len({r["sha256"] for r in rows if r["task"] == task}) == 1
    assert (
        len({r["sha256"] for r in rows if r["mode"] in ["postparse", "replacer"]}) == 1
    )
    assert (
        len(
            {
                r["sha256"]
                for r in rows
                if r["task"] == "6" and r["mode"] in ["baseline", "plain"]
            }
        )
        == 1
    )
    result = {
        "python": sys.version,
        "platform": platform.platform(),
        "input": str(args.input_file.resolve()),
        "bytes": args.input_file.stat().st_size,
        "repeats": args.repeats,
        "measurements": rows,
    }
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("All equivalent outputs have matching SHA-256 hashes.")


if __name__ == "__main__":
    main()
