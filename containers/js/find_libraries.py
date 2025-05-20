"""
This is a hack to guess the Julia libraries that we need to install.

Our approach is to see what libraries are used in generated Julia code from
some model, and then package those in a container.
"""

import argparse
from pathlib import Path
import pandas as pd
from typing import Set
import warnings

IGNORED = ["nothing"]


def find_libraries(code: str) -> Set[str]:
    # Instead of trying to be clever with a Regex, we are going to do this
    # in naively splitting into lines, stripping, and looking for lines that
    # start with "using" or "import". We will also split on commas, because I
    # think Julia supports "using A, B" and "import A, B".
    lines = code.split("\n")
    libraries = set()
    for line in lines:
        line = line.lstrip()
        if not (line.startswith("using ") or line.startswith("import")):
            continue
        line = line.split(" ", maxsplit=1)[1]
        for lib in line.split(","):
            lib = lib.strip()
            if lib.startswith("Base"):
                continue
            if " " in lib or lib in IGNORED:
                warnings.warn(f"Ignoring {lib}")
                continue
            libraries.add(lib)
    return libraries


def main_with_args(generations_jsonl: Path, output_txt: Path):
    df = pd.read_json(generations_jsonl, lines=True)
    df["libs"] = df["result_program"].apply(find_libraries)
    all_libs = set()
    for libs in df["libs"]:
        all_libs.update(libs)
    output_txt.write_text("\n".join(sorted(all_libs)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("generations_jsonl", type=Path)
    parser.add_argument("output_txt", type=Path)
    args = parser.parse_args()
    main_with_args(args.generations_jsonl, args.output_txt)


if __name__ == "__main__":
    main()
