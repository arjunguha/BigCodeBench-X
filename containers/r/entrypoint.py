"""
This program performs the following steps in a loop:

1. Read a program and test suite from a JSON line on standard input.

2. Create a temporary directory with the code and test suite written to
   program.jl and tests.py. Yes, that is correct: the test suite is in
   Python, since it just interacts with the Julia program using standard I/O.

3. Start driver.py, which will dynamically load and run tests.py. Why this
   driver instead of loading tests.py directly? This is the simplest way to
   avoid a hanging test from hanging the entire container.

4. Print test execution results to standard output.
"""

from pathlib import Path
import json
import tempfile
import argparse
from bounded_subprocess import run
import json
import sys


def error(key: str, problem, message: str):
    json.dump({ key: problem[key], "error": "JSONDecodeError", "message": message}, sys.stdout)
    print("\n", flush=True)


def main_with_args(*, timeout_seconds: int, key: str):
    while True:
        try:
            problem_line = input()
        except EOFError:
            break

        try:
            problem = json.loads(problem_line)
        except json.JSONDecodeError as exn:
            error(key, problem, str(exn))
            continue

        if "program" not in problem:
            error(key, problem, "program field is missing")
            continue
        if "test_suite" not in problem:
            error(key, problem, "test_suite field is missing")
            continue

        program = problem["program"]
        if type(program) != str:
            error(key, problem, "program must a string")
            continue

        test_suite = problem["test_suite"]
        if type(test_suite) != str:
            error(key, problem, "test_suite must be a string")
            continue

        with tempfile.TemporaryDirectory() as dir_name:
            dir = Path(dir_name)
            ####################################################################
            # Change the line below for a different language.                  #
            # Nothing else should need to change.                              #
            ####################################################################
            (dir / "program.R").write_text(program)
            (dir / "tests.py").write_text(test_suite)

            result = run(
                ["/usr/bin/python3", "/driver.py", dir_name],
                timeout_seconds=timeout_seconds,
            )
            json.dump({ key: problem[key], **vars(result) }, sys.stdout)
            print(flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=int, default=15)
    parser.add_argument("--key", type=str, default="task_id")
    args = parser.parse_args()
    main_with_args(**vars(args))


if __name__ == "__main__":
    main()
