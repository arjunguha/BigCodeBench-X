from pathlib import Path
import litellm
import pandas as pd
import datasets
from typing import Iterable
import argparse
from tqdm.auto import tqdm
import json
from bcb_multipl_util import extract_code_from_markdown


def load_benchmark(benchmark: str):
    if Path(benchmark).exists():
        return pd.read_json(benchmark, lines=True).to_dict(orient="records")
    else:
        return list(datasets.load_dataset(benchmark, split="test"))


def batches(items: Iterable, batch_size: int):
    num_batches = len(items) // batch_size
    for i in tqdm(range(0, len(items), batch_size), total=num_batches, desc="Batches"):
        yield items[i : i + batch_size]


def make_prompt(item: dict, lang: str):
    return [
        {
            "role": "user",
            "content": item["prompt"] + f"\n\nSolve this problem using {lang}.",
        }
    ]


def main_with_args(
    *,
    model: str,
    benchmark: str,
    temperature: float,
    max_tokens: int,
    top_p: float,
    batch_size: int,
    lang: str,
    output_path: Path,
):

    items = load_benchmark(benchmark)

    with output_path.open("w") as f:
        for batch in batches(items, batch_size):
            requests = [make_prompt(item, lang) for item in batch]
            responses = litellm.batch_completion(
                model=model,
                messages=requests,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
            )
            for input_item, resp in zip(batch, responses):
                response_text = resp["choices"][0]["message"]["content"]
                response_code = extract_code_from_markdown(response_text)
                item = {
                    **input_item,
                    "response": response_text,
                    # Will overwrite the program in input_item, if it exists.
                    "program": response_code,
                }
                json.dump(item, f)
                f.write("\n")
            f.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--benchmark", type=str, required=True)
    parser.add_argument("--lang", type=str, required=True)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--max-tokens", type=int, default=5000)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()
    main_with_args(**vars(args))


if __name__ == "__main__":
    main()
