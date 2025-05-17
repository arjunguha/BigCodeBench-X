"""
See the signature for PythonStdioToAgnostic. That is what this script does, with
a little extra code to map between field names in the signature and field names
in the dataset. The code supports any dataset format, as long as the prompt is
within a single field. The output dataset transforms that field and keeps the
other fields unchanged.
"""

import dspy
from bcb_multipl_util import incremental_parallel
import json
import warnings
import argparse
import pandas as pd
from pathlib import Path
import os


class PythonStdioToAgnostic(dspy.Signature):
    """
    I will give you a problem statement for a Python programming problem, but I
    want to solve this problem in any programming language. Update the problem
    statement to remove references to Python, Python libraries, Python concepts,
    and Python implementation details. However, keep the description of the input
    and output identical. If the I/O description refers to reading or printing
    Python values, leave those unchanged. I have test-cases that rely on
    the I/O behavior being identical and I do not want to change them.
    """

    python_problem: str = dspy.InputField()
    neutral_problem: str = dspy.OutputField()


python_stdio_to_agnostic = dspy.ChainOfThought(PythonStdioToAgnostic)


def main_loop(
    batch_size: int,
    input_field: str,
    output_field: str,
    input_dataset,
):
    input_examples = [
        dspy.Example(python_problem=item[input_field]).with_inputs("python_problem")
        for item in input_dataset
    ]

    for input_item, prediction in zip(
        input_dataset,
        incremental_parallel(python_stdio_to_agnostic, input_examples, batch_size),
    ):
        if prediction is None:
            warnings.warn(f"No prediction for {input_item['task_id']}")
            continue
        yield {**input_item, output_field: prediction.neutral_problem}


def main_with_args(
    *,
    model_name: str,
    temperature: float,
    max_tokens: int,
    batch_size: int,
    input_field: str,
    output_field: str,
    input_path: str,
    output_path: Path,
):

    lm = dspy.LM(
        model_name,
        model_type="chat",
        temperature=temperature,
        max_tokens=max_tokens,
    )
    dspy.configure(lm=lm)

    input_df = pd.read_json(input_path, lines=True).to_dict(orient="records")
    with output_path.open("w") as f:
        for output_item in main_loop(batch_size, input_field, output_field, input_df):
            json.dump(output_item, f)
            f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model-name",
        type=str,
        default="openai/gpt-4.1-mini",
        help="The model name in DSPy format.",
    )
    parser.add_argument("--temperature", type=float, default=0.6)
    parser.add_argument("--max-tokens", type=int, default=1000)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument(
        "--input-field",
        type=str,
        default="prompt",
        help="The field in the input dataset that contains the problem statement.",
    )
    parser.add_argument(
        "--output-field",
        type=str,
        default="prompt",
        help="The field in the output dataset that will contain the neutral problem statement.",
    )
    parser.add_argument("input_path", type=str)
    parser.add_argument("output_path", type=Path)
    args = parser.parse_args()

    if os.environ.get("OPENAI_API_KEY") is None:
        warnings.warn(
            "OPENAI_API_KEY is not set. If you are not using a custom endpoint, this will cause errors."
        )

    main_with_args(**vars(args))


if __name__ == "__main__":
    main()
