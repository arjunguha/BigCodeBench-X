"""
Usage: python3 driver.py TESTS_PATH
This script will load the module TESTS_PATH/tests.py, which must have
a function with this signature:
def test_cases(runner: Callable):
    assert runner(input_text) == (output_text, exit_code)
    ...
It will apply test_cases to a runner that runs Go. So, each test,
written in Python, is testing a Go program.
"""
import argparse
import importlib.util
import subprocess
import sys
from pathlib import Path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("tests_path", type=Path)
    args = parser.parse_args()
    
    tests_path = args.tests_path / "tests.py"
    
    # Dynamically import the test module
    spec = importlib.util.spec_from_file_location("tests", tests_path)
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    
    def runner(stdin_text: str):
        # Use 'go run' directly - no separate compilation needed
        p = subprocess.Popen(
            ####################################################################
            # Change the line below for a different language.                  #
            # Nothing else should need to change.                              #
            ####################################################################
            ["go", "run", str(args.tests_path / "program.go")],
            cwd=str(args.tests_path),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout_text, stderr_text = p.communicate(input=stdin_text)
        print(stderr_text, file=sys.stderr, flush=True)
        exit_code = p.wait()
        return (stdout_text, exit_code)
    
    tests.test_cases(runner)

if __name__ == "__main__":
    main()