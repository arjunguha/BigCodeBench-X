import dspy
from typing import Iterable, List, Optional
from bcb_reader import BigCodeBenchProblem, load_bigcodebench
from bcb_multipl_util import incremental_parallel, extract_code_from_markdown
import argparse
import json
from pathlib import Path


class TranslateProblem(dspy.Signature):
    """
    I will give you a problem statement, a Python function (task_func), and its
    test suite. You will see that the solution defines a function called
    task_func. You must:

    1. Update the solution to be a standalone Python program that communicates
       using standard I/O. Try to use the existing text of the problem as much
       as possible.
    2. Update the problem statement to clearly ask for this program instead. Try
       to use the existing code from task_func as much as possible.
    3. Update the test suite to be a function in the following format:

       ```python
       def test_cases(prog: Callable[[str], Tuple[str, int]]):
          # Run the program by running prog(stdin_text) == (stdout_text, exit_code)
          # Test cases go here.
       ```

       The tests should use assertions and be based on the existing tests.
    """

    original_problem_statement: str = dspy.InputField()
    original_program: str = dspy.InputField()
    original_test_suite: str = dspy.InputField()

    result_problem_statement: str = dspy.OutputField()
    result_program: str = dspy.OutputField()
    result_test_suite: str = dspy.OutputField()


def prepare_dataset(
    original_dataset: Iterable[BigCodeBenchProblem],
) -> List[dspy.Example]:
    results = []
    for problem in original_dataset:
        ex = dspy.Example(
            original_problem_statement=problem["problem"],
            original_program=problem["solution"],
            original_test_suite=problem["tests"],
        )
        results.append(ex.with_inputs(*ex.toDict().keys()))
    return results


def main_with_args(
    *,
    limit: Optional[int],
    model_name: str,
    temperature: float,
    max_tokens: int,
    batch_size: int,
    output_path: Path,
):
    lm = dspy.LM(
        model_name, model_type="chat", temperature=temperature, max_tokens=max_tokens
    )
    dspy.configure(lm=lm)

    translator = dspy.ChainOfThought(TranslateProblem)
    problems = list(load_bigcodebench())
    if limit is not None:
        problems = problems[:limit]
    input_examples = prepare_dataset(problems)

    with output_path.open("w") as f:
        for problem, prediction in zip(
            problems, incremental_parallel(translator, input_examples, batch_size)
        ):
            if prediction is None:
                json.dump({"task_id": problem["task_id"], "error": "No prediction"}, f)
            else:
                the_dict = {
                    "task_id": problem["task_id"],
                    "reasoning": prediction.reasoning,
                }
                the_dict["prompt"] = prediction.result_problem_statement
                the_dict["program"] = (
                    extract_code_from_markdown(prediction.result_program)
                    or prediction.result_program
                )
                the_dict["test_suite"] = (
                    extract_code_from_markdown(prediction.result_test_suite)
                    or prediction.result_test_suite
                )
                json.dump(the_dict, f)
            f.write("\n")
            f.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-name",
        type=str,
        default="openai/o4-mini",
        help="The model name in DSPy format",
    )
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit the number of problems to process (debugging)",
    )
    parser.add_argument("--max-tokens", type=int, default=20_000)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()
    main_with_args(**vars(args))


if __name__ == "__main__":
    main()
