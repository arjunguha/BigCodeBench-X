import datasets
import ast
from typing import TypedDict, Generator


# This is the format of BigCodeBench problems. However, BigCodeBench-Hard has
# a few extra columns.
class _OriginalBigCodeBenchProblem(TypedDict):
    task_id: str
    complete_prompt: str
    instruct_prompt: str
    canonical_solution: str
    code_prompt: str
    test: str
    entry_point: str
    doc_struct: str
    libs: str


class BigCodeBenchProblem(TypedDict):
    task_id: str
    problem: str
    solution: str
    tests: str


_PROMPT_BOILERPLATE = "\nYou should write self-contained code starting with:\n```\n"
_PROMPT_SUFFIX = "```"


def _prepare_bcb_problem(item: _OriginalBigCodeBenchProblem) -> BigCodeBenchProblem:
    """
    Every BCB problem has a canonical solution, which is a completion expected
    from a base model. This function splits the prompt to get a complete
    solution."""
    instruct_prompt = item["instruct_prompt"]
    problem, solution_prefix = instruct_prompt.split(_PROMPT_BOILERPLATE, maxsplit=1)

    assert solution_prefix.endswith(
        _PROMPT_SUFFIX
    ), f"Prompt ends with {solution_prefix[-20:].__repr__()}"
    solution_prefix = solution_prefix[: -len(_PROMPT_SUFFIX)]
    solution = solution_prefix + item["canonical_solution"]

    tests = item["test"]

    # As a sanity check, parse. We get syntax warnings on standard error.
    ast.parse(solution, filename=item["task_id"])
    ast.parse(tests, filename="test_" + item["task_id"])

    return BigCodeBenchProblem(
        task_id=item["task_id"],
        problem=problem,
        solution=solution,
        tests=tests,
    )


def load_bigcodebench() -> Generator[BigCodeBenchProblem, None, None]:
    """ "
    Loads the BigCodeBench dataset in a format appropriate for translation.
    """
    bcb = datasets.load_dataset("bigcode/bigcodebench", split="v0.1.4")
    for item in bcb:
        yield _prepare_bcb_problem(item)
