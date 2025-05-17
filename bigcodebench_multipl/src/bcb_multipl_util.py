"""
This code is adapted from github.com/nuprl/prl_ml, which is an internal
repository.
"""
from typing import Iterable, Optional
import dspy
from tqdm.auto import tqdm


def extract_code_from_markdown(markdown: str) -> Optional[str]:
    """
    Extracts the first markdown block of code from markdown.

    Strips away the language tag on the first line if present. Supports markdown
    that has several code blocks (just returns the first).
    """
    # Find the first code block
    code_block_start = markdown.find("```")
    if code_block_start == -1:
        return None
    
    # Skip past the opening ```
    code_start = code_block_start + 3
    
    # Find the end of this code block
    code_block_end = markdown.find("```", code_start)
    if code_block_end == -1:
        return None
        
    # Extract the code between the markers
    code = markdown[code_start:code_block_end].strip()

    if "# Example usage:" in code:
        code = code.split("# Example usage:")[0]
    
    # Remove language tag if present on first line
    first_newline = code.find('\n')
    if first_newline > 0:
        # Consider the case where the block begins with "```python\n...". In this
        # case, code would already be "python\n..." and first_newline would be 7.
        # Thus first_newline + 1 is the index of "...".
        code = code[first_newline + 1:]
            
    return code.strip()


def incremental_parallel(
    module: dspy.Module,
    examples: Iterable[dspy.Example],
    batch_size: int,
    use_tqdm: bool = True,
) -> Iterable[Optional[dspy.Prediction]]:
    """
    Applies module to the list of examples in batches, but returns the results
    incrementally. I am a little surprised that this does not seem to be
    built-in to DSPy.
    """
    # Create an instance of Parallel
    parallel_executor = dspy.Parallel(
        num_threads=batch_size,
        max_errors=batch_size,
        return_failed_examples=False,
        provide_traceback=False,
        disable_progress_bar=True,
    )

    the_range = range(0, len(examples), batch_size)
    if use_tqdm:
        the_range = tqdm(the_range, desc="Batches", total=len(examples) // batch_size)

    for start_index in the_range:
        exec_pairs = [
            (module, example.inputs())
            for example in examples[start_index : start_index + batch_size]
        ]
        for result in parallel_executor.forward(exec_pairs):
            yield result
