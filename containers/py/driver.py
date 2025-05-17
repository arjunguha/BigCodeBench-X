import argparse
import importlib.util
import os
import subprocess
from pathlib import Path

WRITE_TIMEOUT_SECONDS = 5
READ_TIMEOUT_SECONDS = 30


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tests-path", type=Path, required=True)
    args = parser.parse_args()
    tests_path = args.tests_path / "tests.py"

    # Cursor says that this is the right way to dynamically import a module.
    spec = importlib.util.spec_from_file_location("tests", tests_path)
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)

    # TODO(arjun): Hardcoding /venv/bin/python3 means this will only work in the
    # container. But, just python3 does not work in the container. I don't know
    # why.
    def runner(stdin_text: str):
        p = subprocess.Popen(
            ["/venv/bin/python3", str(args.tests_path / "program.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        stdout_text, stderr_text = p.communicate(input=stdin_text)
        exit_code = p.wait()
        return (stdout_text, exit_code)

    tests.test_cases(runner)


if __name__ == "__main__":
    main()
