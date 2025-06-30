"""
This script evaluates a model on BigCodeBench-X. The main arguments to the
script are:

1. The model, which must be compatible with LiteLLM. LiteLLM supports any
   OpenAI-compatible endpont, as well as several others.

2. Instructions to the model on the programming language to use. For some
   languages, it helps to describe the execution environment as well. For
   example, for JavaScript, it helps to state that the execution environment is
   Node.js and not the browser.

3. The temperature to use for generation.

4. The number of concurrent requests to the model.

5. (Optional) the name of the execution container.

A peculiarity of this script is that we ask the model to return the list of
libraries that it needs to solve the problem. Our intent is that you will
use this information to build up the libraries in the execution container.
"""

import datasets
import dspy
from bcb_multipl_util import extract_code_from_markdown
from typing import List, TypedDict, Awaitable, Optional
import json
import argparse
import asyncio
from pathlib import Path
from tqdm.auto import tqdm
import pandas as pd


class SolveProblem(dspy.Signature):
    """
    Solve the following programming problem using the programming
    language that I have specified. In addition, return the list of libraries
    that the solution uses. I will take care of installing them.

    Use ONLY the programming language given below!
    """

    programming_language: str = dspy.InputField(
        description="The programming language to use."
    )
    problem_statement: str = dspy.InputField()
    program: str = dspy.OutputField()
    libraries: List[str] = dspy.OutputField()


class SolveProblemWithExample(dspy.Signature):
    """
    Solve the following programming problem using the programming
    language that I have specified. In addition, return the list of libraries
    that the solution uses. I will take care of installing them. I have provided
    an example input and output that the program must support.

    Use ONLY the programming language given below!
    """

    programming_language: str = dspy.InputField(
        description="The programming language to use."
    )
    problem_statement: str = dspy.InputField()
    example_input: str = dspy.InputField()
    example_output: str = dspy.InputField()
    program: str = dspy.OutputField()
    libraries: List[str] = dspy.OutputField()


class Problem(TypedDict):
    task_id: str
    prompt: str
    test_suite: str


class SolveProblemFixup(dspy.Module):
    """
    Wrapper around SolveProblem that maps dataset field names to the field names
    that SolveProblem expects.
    """

    def __init__(self):
        self.solve_problem = dspy.ChainOfThought(SolveProblem)

    # We ignore a couple of arguments:
    # - program: the Python reference solution
    # - task_id: the task ID
    # - test_suite: the test suite
    async def aforward(
        self, lang: str, prompt: str, program: str, task_id: str, test_suite: str
    ) -> SolveProblem:
        try:
            result = await self.solve_problem.aforward(
                programming_language=lang,
                problem_statement=prompt,
            )
        except Exception as e:
            return {
                "program": "",
                "libraries": [],
                "reasoning": f"Generation failed\n\n{str(e)}",
            }
        return {
            "program": extract_code_from_markdown(result.program),
            "libraries": result.libraries,
            # The chain-of-thought from the model. This may help analyze
            # model errors.
            "reasoning": result.reasoning,
        }


solve_problem = SolveProblemFixup()


class SolveProblemWithExampleFixup(dspy.Module):
    """
    Wrapper that optionally uses SolveProblemWithExample when the
    example_input and example_output are not None.
    """

    def __init__(self):
        self.solve_problem_with_example = dspy.ChainOfThought(SolveProblemWithExample)

    async def aforward(
        self,
        lang: str,
        prompt: str,
        example_input: Optional[str],
        example_output: Optional[str],
        program: str,
        task_id: str,
        test_suite: str,
    ) -> SolveProblem:
        if example_input is None or example_output is None:
            return await solve_problem.aforward(
                lang=lang,
                prompt=prompt,
                program=program,
                task_id=task_id,
                test_suite=test_suite,
            )

        try:
            result = await self.solve_problem_with_example.aforward(
                programming_language=lang,
                problem_statement=prompt,
                example_input=example_input,
                example_output=example_output,
            )
        except Exception as e:
            return {
                "program": "",
                "libraries": [],
                "reasoning": f"Generation failed\n\n{str(e)}",
            }
        return {
            "program": extract_code_from_markdown(result.program),
            "libraries": result.libraries,
            # The chain-of-thought from the model. This may help analyze
            # model errors.
            "reasoning": result.reasoning,
        }


solve_problem_with_example = SolveProblemWithExampleFixup()


def prepare_dataset(variation: str):
    if variation == "no-examples":
        return list(
            datasets.load_dataset(
                "nuprl-staging/BigCodeBench-MultiPL", "default", split="test"
            )
        )
    elif variation == "with-examples":
        examples = datasets.load_dataset(
            "nuprl-staging/BigCodeBench-MultiPL", "io_examples", split="test"
        )
        problems = datasets.load_dataset(
            "nuprl-staging/BigCodeBench-MultiPL", "default", split="test"
        )
        examples_df = examples.to_pandas()
        examples_df = examples_df.drop_duplicates(subset="task_id", keep="first")
        examples_df = examples_df[examples_df["exit_code"] == 0]
        examples_df = examples_df[["task_id", "example_input", "example_output"]]
        problems_df = problems.to_pandas()
        merged_df = problems_df.merge(examples_df, on="task_id", how="left")
        merged_df = merged_df.where(pd.notnull(merged_df), None)
        return merged_df.to_dict(orient="records")
    else:
        raise ValueError(f"Invalid variation: {variation}")


async def save_output(output_path: Path, generations: List[Awaitable[dict]]):
    with output_path.open("w") as f:
        for generation in generations:
            json.dump(await generation, f)
            f.write("\n")
            f.flush()


def run_executions(
    container_name: str,
    num_concurrent_requests: int,
    generations: List[Awaitable[dict]],
):
    container_semaphore = asyncio.Semaphore(num_concurrent_requests)

    async def execute(generation_future: Awaitable[dict]):
        async with container_semaphore:
            generation = await generation_future

            input_text = json.dumps(
                {
                    "task_id": generation["task_id"],
                    "program": generation["program"],
                    "test_suite": generation["test_suite"],
                }
            )

            proc = await asyncio.create_subprocess_exec(
                "docker",
                "run",
                "--rm",
                "-i",
                container_name,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate(input_text.encode(errors="ignore"))
            stdout = stdout.decode(errors="ignore")
            stderr = stderr.decode(errors="ignore")
            if proc.returncode != 0:
                return {
                    **generation,
                    "exit_code": -1,
                    "stdout": stdout,
                    "stderr": f"Container error\n\n{stderr}",
                }
            try:
                result_json = json.loads(stdout)
            except json.JSONDecodeError:
                return {
                    **generation,
                    "exit_code": -1,
                    "stdout": stdout,
                    "stderr": f"JSONDecodeError\n\n{stderr}",
                }
            return {
                **generation,
                **result_json,
            }

    return [asyncio.create_task(execute(generation)) for generation in generations]


# This allows us to have a consistent interface for execution after
# generate and execution after loading.
def immediate_future(value) -> Awaitable:
    f = asyncio.Future()
    f.set_result(value)
    return f


async def execute_with_args(
    *,
    container_name: str,
    input_path: Path,
    output_path: Path,
    num_concurrent_requests: int,
):
    generations = []
    with input_path.open("r") as f:
        for line in f:
            generations.append(immediate_future(json.loads(line)))
    execution_tasks = run_executions(
        container_name, num_concurrent_requests, generations
    )
    await save_output(output_path, asyncio.as_completed(execution_tasks))


async def generate_with_args(
    *,
    model_name: str,
    temperature: float,
    max_tokens: int,
    num_concurrent_requests: int,
    lang: str,
    container_name: Optional[str],
    output_path: Path,
    variation: str,
):
    lm = dspy.LM(
        model_name,
        model_type="chat",
        temperature=temperature,
        top_p=0.95,
        max_tokens=max_tokens,
    )
    dspy.configure(lm=lm)
    # Test the model. If this crashes, no point trying to run the benchmark.
    lm("Say this is a test!", temperature=0.7)

    model_semaphore = asyncio.Semaphore(num_concurrent_requests)

    # We add this metadata to every row of output. It is repetitive, but helps
    # avoid mistakes.
    metadata = {
        "model_name": model_name,
        "lang": lang,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "container_name": container_name,
    }

    problems = prepare_dataset(variation)

    pbar = tqdm(total=len(problems), desc="Generating")

    async def generate(problem: Problem):
        async with model_semaphore:
            pbar.update(1)
            if variation == "no-examples":
                result = await solve_problem.aforward(lang=lang, **problem)
            elif variation == "with-examples":
                result = await solve_problem_with_example.aforward(lang=lang, **problem)
            else:
                raise ValueError(f"Invalid variation: {variation}")
            return {**problem, **metadata, **result}

    # All generations run in parallel, but the semaphore ensures that we do not
    # exceed the number of concurrent requests.
    generation_tasks = [asyncio.create_task(generate(p)) for p in problems]

    # Progress bar is on generation, and not execution. We are assuming that
    # generation time exceeds execution time.
    generations = asyncio.as_completed(generation_tasks)

    # If no container is provided, save generations and exit.
    if container_name is None:
        await save_output(output_path, generations)
        return

    execution_tasks = run_executions(
        container_name, num_concurrent_requests, generations
    )
    await save_output(output_path, asyncio.as_completed(execution_tasks))


async def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate subcommand
    generate_parser = subparsers.add_parser(
        "generate", help="Generate solutions for BigCodeBench-X problems"
    )
    generate_parser.add_argument(
        "--model-name",
        type=str,
        required=True,
        help="The model name in LiteLLM format.",
    )
    generate_parser.add_argument("--temperature", type=float, default=0.6)
    generate_parser.add_argument("--max-tokens", type=int, default=5000)
    generate_parser.add_argument("--num-concurrent-requests", type=int, default=20)
    generate_parser.add_argument(
        "--lang",
        type=str,
        required=True,
        help="The programming language to use.",
    )
    generate_parser.add_argument(
        "--container-name", type=str, required=False, default=None
    )
    generate_parser.add_argument("--output-path", type=Path, required=True)

    # Execute subcommand
    execute_parser = subparsers.add_parser(
        "execute", help="Execute solutions for BigCodeBench-X problems"
    )
    execute_parser.add_argument("--container-name", type=str, required=True)
    execute_parser.add_argument("--num-concurrent-requests", type=int, default=20)
    execute_parser.add_argument("--input-path", type=Path, required=True)
    execute_parser.add_argument("--output-path", type=Path, required=True)
    generate_parser.add_argument(
        "--variation",
        choices=["no-examples", "with-examples"],
        required=False,
        default="no-examples",
    )

    args = parser.parse_args()

    args_dict = {k: v for k, v in vars(args).items() if k != "command"}

    if args.command == "generate":
        await generate_with_args(**args_dict)
    elif args.command == "execute":
        await execute_with_args(**args_dict)
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
