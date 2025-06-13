import dspy
import json
import asyncio
import argparse
from pathlib import Path
from typing import Optional, Callable, Iterable, List
from bcb_reader import BigCodeBenchProblem
from dspy_util import incremental_parallel
from datasets import load_dataset
from bounded_subprocess.interactive_async import Interactive
from tqdm import tqdm

# DSPy Signature
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

# Prepare DSPy Examples
def prepare_dataset(dataset: Iterable[BigCodeBenchProblem]) -> List[dspy.Example]:
    results = []
    for problem in dataset:
        ex = dspy.Example(
            task_id=problem["task_id"],
            original_problem_statement=problem["prompt"],
            original_program=problem["program"],
            original_test_suite=problem["test_suite"],
        )
        results.append(ex.with_inputs(*ex.toDict().keys()))
    return results

# Generate Test Suite
def generate_test_case(example_input: str, example_output: str) -> str:
    escaped_input = repr(example_input)
    escaped_output = repr(example_output.rstrip())
    return f"""def test_cases(prog):
    stdin = {escaped_input}
    stdout, exit_code = prog(stdin)
    stdout = stdout.rstrip()
    assert stdout == {escaped_output}, f"Got {{repr(stdout)}}"
    assert exit_code == 0
"""

# Wrapper DSPy module
class ExampleWithVerification(dspy.Module):
    def __init__(self):
        self.translator = dspy.ChainOfThought(ExampleIO)

    async def aforward(self, *, task_id, original_problem_statement, original_program, original_test_suite, **kwargs):
        try: 
            prediction = await self.translator.aforward(
                original_problem_statement=original_problem_statement,
                original_program=original_program,
                original_test_suite=original_test_suite
            )
            test_suite = generate_test_case(prediction.example_input, prediction.example_output)
            result = await self._run_in_container(task_id,original_program, test_suite)
            # print("got result", result['exit_code'], " for task_id", task_id)
            return dspy.Prediction(
                **prediction.toDict(),
                test_suite=test_suite,
                **result
            )
        except Exception as e:
            print(f"Error processing task {task_id}: {e}")
            return dspy.Prediction(
                task_id=task_id,
                example_input="",
                example_output="",
                test_suite="",
                exit_code=1,
                stdout="",
                stderr=str(e),
                timeout=True,
                reasoning=""
            )

    async def _run_in_container(self, task_id:str, program: str, test_suite: str) -> dict:
        proc = Interactive([
            "podman", "run", "-i", "--rm", "--network", "none", "--cpus", "2",
            "ghcr.io/arjunguha/bcb_multipl-py"],read_buffer_size=10 * 1024
        )
        stdin_text = json.dumps({"task_id":task_id,"program": program, "test_suite": test_suite})
        await proc.write(stdin_text.encode("utf-8"), timeout_seconds=10)
        await proc.write(b"\n", timeout_seconds=2)
        stdout_bytes = await proc.read_line(timeout_seconds=10)
        exit_code = await proc.close(nice_timeout_seconds=5)
        try:
            return json.loads(stdout_bytes.decode("utf-8"))
        except Exception as e:
            return {
                "exit_code": 1,
                "timeout": True,
                "stdout": "",
                "stderr": f"Failed to decode: {e}"
            }

# Retry wrapper
class Retries(dspy.Module):
    def __init__(self, module: dspy.Module, max_retries: int, reward_fn: Callable[[dspy.Prediction], float], threshold: float):
        self._module = module
        self._max_retries = max_retries
        self._reward_fn = reward_fn
        self._threshold = threshold
    
    async def aforward(self, **kwargs) -> dspy.Prediction:
        for i in range(self._max_retries):
            result = await self._module.acall(**kwargs)
            reward = self._reward_fn(result)
            if reward >= self._threshold:
                if i > 0:
                    print("succeed on attempt", i + 1)
                return result
        return result

def reward(pred: dspy.Prediction) -> float:
    return 1.0 if pred.exit_code == 0 else 0.0

def load_completed_task_ids(output_path: Path) -> set:
    if not output_path.exists():
        return set()
    completed = set()
    with output_path.open("r") as f:
        for line in f:
            try:
                obj = json.loads(line)
                if "task_id" in obj:
                    completed.add(obj["task_id"])
            except json.JSONDecodeError:
                continue
    return completed


# Main driver
async def main_async(args):
    lm = dspy.LM("openai/qwen3_8b_awq",
                 api_base="http://10.200.111.102:4000/v1",
                 api_key="dummy",cache=False, temperature=args.temperature,max_tokens=args.max_tokens)
    dspy.configure(lm=lm)

    problems = load_dataset("nuprl-staging/BigCodeBench-MultiPL")["test"].to_list()
    problems = problems[:args.limit] if args.limit else problems
    completed_ids = load_completed_task_ids(args.output_path)

    # Filter dataset
    filtered_problems = [p for p in problems if p["task_id"] not in completed_ids]
    print(f"Total problems: {len(problems)} | Skipping {len(completed_ids)} already completed | Remaining: {len(filtered_problems)}")

    if not filtered_problems:
        print("No new problems to process.")
        return
    
    inputs = prepare_dataset(filtered_problems)

    module = Retries(
        module=ExampleWithVerification(),
        max_retries=5,
        reward_fn=reward,
        threshold=1.0
    )

    sema = asyncio.Semaphore(args.num_concurrent)

    async def do_task(problem, example):
        async with sema:
            pred = await module.acall(**example.toDict())
            if pred is None:
                return {"task_id": problem["task_id"], "error": "No prediction"}
            return {
                "task_id": problem["task_id"],
                "program": problem["program"],
                "example_input": pred.example_input,
                "example_output": pred.example_output,
                "test_suite": pred.test_suite,
                "exit_code": pred.exit_code,
                "stdout": pred.stdout,
                "stderr": pred.stderr,
                "timeout": pred.timeout,
                "reasoning": pred.reasoning,
            }
        
    tasks = [asyncio.create_task(do_task(problem, example)) for problem, example in zip(problems, inputs)]
    with args.output_path.open("a") as f:
        for task in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Generating"):
            record = await task
            json.dump(record, f)
            f.write("\n")
            f.flush()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num-concurrent", type=int, default=50)
    parser.add_argument("--model-name", type=str, default="openai/qwen3_8b_awq")
    parser.add_argument("--temperature", type=float, default=1.0)
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of problems to process")
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(main_async(args))

if __name__ == "__main__":
    main()
