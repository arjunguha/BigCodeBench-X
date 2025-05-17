from pathlib import Path
import json
import tempfile
import argparse
from typing import Optional
from typeguard import typechecked
from bounded_subprocess import run
import shutil


@typechecked
def read_line(path: Path, line_number: int) -> str:
    with open(path, "r") as f:
        for i, line in enumerate(f):
            if i == line_number:
                return line
    raise ValueError(f"Line number {line_number} not found in file {path}")


DRIVER_PATH = Path(__file__).parent / "driver.py"


@typechecked
def write_and_run_problem(
    task_id: str, result_program: str, result_test_suite: str, output_dir: Path
):
    (output_dir / "program.py").write_text(result_program)
    (output_dir / "tests.py").write_text(result_test_suite)

    # TODO(arjun): Hardcoding /venv/bin/python3 means this will only work in the
    # container. But, just python3 does not work in the container. I don't know
    # why.
    result = run(
        ["/venv/bin/python3", str(DRIVER_PATH), "--tests-path", output_dir],
        timeout_seconds=30,
    )
    print(
        json.dumps(
            {
                "task_id": task_id,
                "exit_code": result.exit_code,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
    )


@typechecked
def main_with_args(problems_path: Path, problem_index: int, output_dir: Optional[Path]):
    problem_line = read_line(problems_path, problem_index)
    problem = json.loads(problem_line)

    task_id = problem["task_id"]
    result_program = problem["result_program"]
    result_test_suite = problem["result_test_suite"]

    if output_dir is None:
        with tempfile.TemporaryDirectory() as temp_dir:
            write_and_run_problem(
                task_id, result_program, result_test_suite, Path(temp_dir)
            )
    else:
        write_and_run_problem(task_id, result_program, result_test_suite, output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--problems-path", type=Path, required=True)
    parser.add_argument("--problem-index", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=False)
    args = parser.parse_args()
    main_with_args(args.problems_path, args.problem_index, args.output_dir)


if __name__ == "__main__":
    main()
