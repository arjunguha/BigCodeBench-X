"""
You do not need to run this program yourself. It is hosted on Hugging Face
Spaces at:

https://huggingface.co/spaces/nuprl/BigCodeBench-MultiPL-Stdio-Problem-Inspector

If you want to run it yourself, you can do the following:

We use this program to help inspect our synthesized problems. These are the
steps to run it end-to-end:

1. Create a jsonl file that joins synthesized problems with their execution
   results.

   uv run python3 -m bigcodebench_multipl.stdio_problem_inspector upload \
       --problems-path unfiltered_stdio.jsonl \
       --results-path unfiltered_stdio.results.jsonl \
       --output-path unfiltered_stdio.joined.jsonl

2. Upload the dataset to the Hugging Face Hub for the next steps.

       mkdir python_stdio
       mv unfiltered_stdio.joined.jsonl python_stdio/test.jsonl

    Now, drag and drop the *folder* above to a Hugging Face dataset.

3. Run the inspector:

       uv run python3 -m bigcodebench_multipl.stdio_problem_inspector dataset-inspector

"""
import argparse
import pandas as pd
import gradio as gr
import datasets
from pathlib import Path
import datasets
import ast
from typing import TypedDict, Generator

################################################################################
# Copy-pasted from bcb_reader.py.                                              #
################################################################################

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

################################################################################

def upload(problems_path: Path, results_path: Path, output_path: Path):
    problems = pd.read_json(problems_path, lines=True)
    results = pd.read_json(results_path, lines=True)

    joined = problems.merge(results, on="task_id", how="left")

    assert list(joined.columns) == [
        "reasoning",
        "prompt",
        "program",
        "test_suite",
        "task_id",
        "timeout",
        "exit_code",
        "stdout",
        "stderr",
    ], "Unexpected columns after the join. Are you sure you are merging the right files?"

    joined.to_json(output_path, orient="records", lines=True)

    
def dataset_inspector(dataset_name: str, data_dir: str):
    dataset = datasets.load_dataset(dataset_name, data_dir=data_dir, split="test")
    
    original_dataset = pd.DataFrame(load_bigcodebench())
    original_dataset = original_dataset.rename(columns={
        "problem": "original_prompt",
        "solution": "original_program",
        "tests": "original_test_suite",
    })
    
    # Convert to pandas DataFrame for easier manipulation
    df = dataset.to_pandas()
    df = df.merge(original_dataset, on="task_id", how="left")
    
    def get_filtered_data(predicate):
        """Filter the dataset based on predicate"""
        filtered_df = df.copy()

        selector = False
        if predicate.get('filter_timeout', False):
            selector = selector | (filtered_df['timeout'] == True)
        
        if predicate.get('filter_successes', False):
            selector = selector | (filtered_df['exit_code'] == 0)
        
        if predicate.get('filter_errors', False):
            # We use exit_code < 0 for timeout.
            selector = selector | (filtered_df['exit_code'] > 0)
        
        return filtered_df[selector]
    
    def format_problem_display(row, predicate):
        """Format a single problem for display - returns (generated_content, original_content)"""
        generated_content = []
        original_content = []
        
        # Add reasoning to generated side if checkbox is checked
        if predicate.get('show_reasoning', False):
            generated_content.append("## Reasoning")
            generated_content.append(str(row['reasoning']))
            generated_content.append("")
        
        # Generated content
        generated_content.append("# Generated")
        generated_content.append("")
        generated_content.append("## Prompt")
        generated_content.append(str(row['prompt']))
        generated_content.append("")
        
        generated_content.append("## Program")
        generated_content.append("```python")
        generated_content.append(str(row['program']))
        generated_content.append("```")
        generated_content.append("")
        
        generated_content.append("## Test Suite")
        generated_content.append("```python")
        generated_content.append(str(row['test_suite']))
        generated_content.append("```")
        generated_content.append("")
        
        # Add execution results to generated side
        if str(row['stdout']).strip():
            generated_content.append("## Standard Output")
            generated_content.append("```")
            generated_content.append(str(row['stdout']))
            generated_content.append("```")
            generated_content.append("")
        
        if str(row['stderr']).strip():
            generated_content.append("## Standard Error")
            generated_content.append("```")
            generated_content.append(str(row['stderr']))
            generated_content.append("```")
            generated_content.append("")
        
        generated_content.append("## Metadata")
        generated_content.append(f"**Task ID:** {row['task_id']}")
        generated_content.append(f"**Timeout:** {row['timeout']}")
        generated_content.append(f"**Exit Code:** {row['exit_code']}")
        
        # Original content
        original_content.append("# Original")
        original_content.append("")
        original_content.append("## Prompt")
        original_content.append(str(row['original_prompt']))
        original_content.append("")
        
        original_content.append("## Program")
        original_content.append("```python")
        original_content.append(str(row['original_program']))
        original_content.append("```")
        original_content.append("")
        
        original_content.append("## Test Suite")
        original_content.append("```python")
        original_content.append(str(row['original_test_suite']))
        original_content.append("```")
        
        return "\n".join(generated_content), "\n".join(original_content)
    
    def update_display(current_index, predicate):
        """Update the display based on current predicate and index"""
        filtered_df = get_filtered_data(predicate)
        
        if len(filtered_df) == 0:
            return "No problems match the current filters.", "No problems match the current filters.", f"0 / 0", gr.update(interactive=False), gr.update(interactive=False)
        
        # Ensure index is within bounds
        current_index = max(0, min(current_index, len(filtered_df) - 1))
        
        row = filtered_df.iloc[current_index]
        generated_content, original_content = format_problem_display(row, predicate)
        status = f"{current_index + 1} / {len(filtered_df)}"
        
        # Update button states
        prev_enabled = current_index > 0
        next_enabled = current_index < len(filtered_df) - 1
        
        return generated_content, original_content, status, gr.update(interactive=prev_enabled), gr.update(interactive=next_enabled)
    
    def go_prev(current_index, predicate):
        """Go to previous problem"""
        new_index = max(0, current_index - 1)
        generated_content, original_content, status, prev_btn, next_btn = update_display(new_index, predicate)
        return generated_content, original_content, status, new_index, prev_btn, next_btn
    
    def go_next(current_index, predicate):
        """Go to next problem"""
        filtered_df = get_filtered_data(predicate)
        new_index = min(len(filtered_df) - 1, current_index + 1)
        generated_content, original_content, status, prev_btn, next_btn = update_display(new_index, predicate)
        return generated_content, original_content, status, new_index, prev_btn, next_btn
    
    def on_filter_change(current_index, predicate):
        """Handle filter changes - reset to first item"""
        generated_content, original_content, status, prev_btn, next_btn = update_display(0, predicate)
        return generated_content, original_content, status, 0, prev_btn, next_btn
    
    def update_predicate(predicate, key, value):
        """Update a single key in the predicate"""
        new_predicate = predicate.copy()
        new_predicate[key] = value
        return new_predicate
    
    # Create Gradio interface
    with gr.Blocks(title="BigCodeBench Problem Inspector") as demo:
        gr.Markdown("# BigCodeBench-MultiPL Problem Inspector")
        
        # State to track current index and predicate
        current_index = gr.State(0)
        predicate = gr.State({
            'filter_timeout': False,
            'filter_successes': True,
            'filter_errors': False,
            'show_reasoning': False
        })
        
        # Top controls row
        with gr.Row():
            prev_btn = gr.Button("← Previous", size="sm")
            status_text = gr.Textbox(value="1 / 1", interactive=False, container=False, show_label=False)
            next_btn = gr.Button("Next →", size="sm")
        
        # Filter controls
        with gr.Row():
            filter_timeout = gr.Checkbox(label="Filter by timeout = True", value=False)
            filter_successes = gr.Checkbox(label="Show successes (exit_code == 0)", value=True)
            filter_errors = gr.Checkbox(label="Show errors (exit_code != 0)", value=False)
            show_reasoning = gr.Checkbox(label="Show reasoning", value=False)
        
        # Main content area - two columns
        with gr.Row():
            with gr.Column():
                generated_display = gr.Markdown(value="Loading generated content...", height=600)
            with gr.Column():
                original_display = gr.Markdown(value="Loading original content...", height=600)
        
        # Initialize display
        demo.load(
            fn=lambda: update_display(0, {'filter_timeout': False, 'filter_successes': True, 'filter_errors': False, 'show_reasoning': False}),
            outputs=[generated_display, original_display, status_text, prev_btn, next_btn]
        )
        
        # Event handlers
        prev_btn.click(
            fn=go_prev,
            inputs=[current_index, predicate],
            outputs=[generated_display, original_display, status_text, current_index, prev_btn, next_btn]
        )
        
        next_btn.click(
            fn=go_next,
            inputs=[current_index, predicate],
            outputs=[generated_display, original_display, status_text, current_index, prev_btn, next_btn]
        )
        
        # Filter change handlers
        filter_timeout.change(
            fn=lambda current_idx, pred, value: (
                *on_filter_change(current_idx, update_predicate(pred, 'filter_timeout', value)),
                update_predicate(pred, 'filter_timeout', value)
            ),
            inputs=[current_index, predicate, filter_timeout],
            outputs=[generated_display, original_display, status_text, current_index, prev_btn, next_btn, predicate]
        )
        
        filter_errors.change(
            fn=lambda current_idx, pred, value: (
                *on_filter_change(current_idx, update_predicate(pred, 'filter_errors', value)),
                update_predicate(pred, 'filter_errors', value)
            ),
            inputs=[current_index, predicate, filter_errors],
            outputs=[generated_display, original_display, status_text, current_index, prev_btn, next_btn, predicate]
        )
        
        filter_successes.change(
            fn=lambda current_idx, pred, value: (
                    *on_filter_change(current_idx, update_predicate(pred, 'filter_successes', value)),
                update_predicate(pred, 'filter_successes', value)
            ),
            inputs=[current_index, predicate, filter_successes],
            outputs=[generated_display, original_display, status_text, current_index, prev_btn, next_btn, predicate]
        )
        
        show_reasoning.change(
            fn=lambda current_idx, pred, value: (
                *update_display(current_idx, update_predicate(pred, 'show_reasoning', value)),
                update_predicate(pred, 'show_reasoning', value)
            ),
            inputs=[current_index, predicate, show_reasoning],
            outputs=[generated_display, original_display, status_text, prev_btn, next_btn, predicate]
        )
        
    demo.launch(share=True)


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="subcommand")

    upload_command = subparsers.add_parser("upload", help="Prepare the dataset")
    upload_command.add_argument(
        "--problems-path",
        type=Path,
        required=True,
        help="Output from make_stdio_problem.py",
    )
    upload_command.add_argument(
        "--results-path",
        type=Path,
        required=True,
        help="Execution results from --problems-path",
    )
    upload_command.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Output path to save the joined dataset",
    )


    dataset_inspector_command = subparsers.add_parser("dataset-inspector", help="Inspect a dataset")
    dataset_inspector_command.add_argument(
        "--dataset-name",
        type=str,
        default="nuprl/BigCodeBench-MultiPL-Results",
        help="Name of the dataset on the Hugging Face Hub",
    )
    dataset_inspector_command.add_argument(
        "--data-dir",
        type=str,
        default="python_stdio",
        help="Name of the directory on the Hugging Face Hub",
    )

    args = parser.parse_args()

    args_dict = dict(vars(args))
    del args_dict["subcommand"]

    if args.subcommand == "upload":
        upload(**args_dict)
    elif args.subcommand == "dataset-inspector":
        dataset_inspector(**args_dict)
    elif args.subcommand is None:
        dataset_inspector(dataset_name="nuprl/BigCodeBench-MultiPL-Results", data_dir="python_stdio")
    else:
        raise ValueError(f"Unknown subcommand: {args.subcommand}")


if __name__ == "__main__":
    main()
