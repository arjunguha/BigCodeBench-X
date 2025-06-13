import dspy
from typing import Iterable, List, Optional
from bcb_reader import BigCodeBenchProblem, load_bigcodebench
from bcb_multipl_util import extract_code_from_markdown
from dspy_util import incremental_parallel
import argparse
import json
from pathlib import Path
import datasets

class ExampleIO(dspy.Signature):
    """
    You will be given a problem statement, a standalone reference (gold) Python solution that communicates via standard input/output, and a corresponding test suite.

    Your task is to generate an example input-output pair that illustrates the expected behavior of the program. This example will be added to the problem statement as a demonstration of the input and output format.

    Guidelines:
    - Your example input and output must strictly follow the input/output format described in the problem prompt.
    - Your example must be compatible with the provided solution — running the solution on your example input should produce the exact example output.
    - If possible, base your example on one of the provided test cases, and make any necessary adjustments to synthesize a valid input and its corresponding correct output.
    - For programs that use the random library with a fixed seed, the output should reflect the result of using that seed. For programs that use random without setting a seed, assume random.seed(0) to ensure reproducibility.
    
    Format your example as it would appear in an interactive terminal session: place each input line on its own line, and do the same for each output line.
    """

    original_problem_statement: str = dspy.InputField()
    original_program: str = dspy.InputField()
    original_test_suite: str = dspy.InputField()

    example_input: str = dspy.OutputField()
    example_output: str = dspy.OutputField()


def prepare_dataset(
    original_dataset: Iterable[BigCodeBenchProblem],
) -> List[dspy.Example]:
    results = []
    for problem in original_dataset:
        ex = dspy.Example(
            original_problem_statement=problem["prompt"],
            original_program=problem["program"],
            original_test_suite=problem["test_suite"],
        )
        results.append(ex.with_inputs(*ex.toDict().keys()))
    return results

def generate_test_case(example_input: str, example_output: str) -> str:
    # Escape backslashes and quotes for safety
    escaped_input = repr(example_input)
    example_output_without_newline = example_output.rstrip()
    escaped_output = repr(example_output_without_newline)
    
    return f"""def test_cases(prog):
    stdin = {escaped_input}
    stdout, exit_code = prog(stdin)
    stdout = stdout.rstrip()
    assert stdout == {escaped_output}, f"Got {{repr(stdout)}}"
    assert exit_code == 0
"""

# from transformers import AutoModelForCausalLM
def main_with_args(
    *,
    limit: Optional[int],
    model_name: str,
    temperature: float,
    max_tokens: int,
    batch_size: int,
    output_path: Path,
):  
    lm = dspy.LM("openai/qwen3_8b_awq",
                 api_base="http://10.200.111.102:4000/v1",
                 api_key="dummy",cache=False)
    # lm = dspy.LM(model=model)
    # lm = dspy.LM(
    #     model_name, model_type="chat", temperature=temperature, max_tokens=max_tokens
    # )
    dspy.configure(lm=lm)

    translator = dspy.ChainOfThought(ExampleIO)
    problems = datasets.load_dataset("nuprl-staging/BigCodeBench-MultiPL")['test'].to_list()
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
                    "program": problem["program"],
                }
                the_dict["reasoning"] = prediction.reasoning
                the_dict["example_input"] = prediction.example_input
                the_dict["example_output"] = prediction.example_output
                the_dict["test_suite"] = generate_test_case(prediction.example_input, prediction.example_output)
                json.dump(the_dict, f)
            f.write("\n")
            f.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-name",
        type=str,
        default="openai/qwen3_8b_awq",
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
