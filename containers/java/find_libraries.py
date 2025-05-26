"""
This is a hack to guess the libraries that we need to install.

Our approach is to see what libraries are used in generated code from
some model, and then package those in a container.

Note: Maven needs the format `group:artifact:version`, thus manual lookup is needed for now.
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
    if not isinstance(code, str):
        return set()
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

from typing import Optional
import re
def extract_missing_packages(error_text: Optional[str]) -> set[str]:
    if not isinstance(error_text, str):
        print("Skipping non-string error_text:", error_text)
        return set()
    pattern = re.compile(r"error: package ([\w\.]+) does not exist")
    found = set(match.group(1) for match in pattern.finditer(error_text))
    print(f"Extracted libraries from error text: {found}")
    return found


def main_with_args(generations_jsonl: Path, output_txt: Path):
    # Read existing libraries if the file already exists
    if output_txt.exists():
        existing_libs = set(output_txt.read_text().splitlines())
    else:
        existing_libs = set()

    # Load generated code and extract libraries
    df = pd.read_json(generations_jsonl, lines=True)
    #print out the rows where df["program"] is None
    df["libs"] = df["program"].apply(find_libraries)
    # df["libs"] = df["stderr"].apply(extract_missing_packages)

    # Collect all newly found libraries
    new_libs = set()
    for libs in df["libs"]:
        new_libs.update(libs)

    # Merge with existing, avoiding duplicates
    combined_libs = existing_libs.union(new_libs)

    # Write back to the file (sorted for consistency)
    output_txt.write_text("\n".join(sorted(combined_libs)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("generations_jsonl", type=Path)
    parser.add_argument("output_txt", type=Path)
    args = parser.parse_args()
    main_with_args(args.generations_jsonl, args.output_txt)


if __name__ == "__main__":
    main()
