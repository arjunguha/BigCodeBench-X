import argparse
import pandas as pd
import json
from pathlib import Path


def load_jsonl_ignoring_errors(path: str):
    """
    We seem to get JSON decode errors on some lines from the container, which
    is why
    """
    with Path(path).open("r") as f:
        for line_num, line in enumerate(f):
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                print(f"Error decoding line {line_num}: {line}")
                pass


def main_with_args(file1: str, file2: str, include_failed: bool, output_file: str):
    df1 = pd.read_json(file1, lines=True)
    df2 = pd.DataFrame(load_jsonl_ignoring_errors(file2))
    df = df1.merge(df2, on="task_id", how="inner")

    if not include_failed:
        df = df[df["exit_code"] == 0]
        df = df.drop(columns=["exit_code", "stderr", "stdout", "timeout"])
        df = df.drop(columns=["reasoning"])

    df.to_json(output_file, lines=True, orient="records")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file1", type=str)
    parser.add_argument("file2", type=str)
    parser.add_argument("--include-failed", action="store_true")
    parser.add_argument("--output-file", type=str)
    args = parser.parse_args()
    main_with_args(**vars(args))


if __name__ == "__main__":
    main()
