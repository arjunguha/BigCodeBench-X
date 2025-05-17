"""
This code is adapted from github.com/nuprl/prl_ml, which is an internal
repository.
"""

from typing import Iterable, Optional
import dspy
from tqdm.auto import tqdm


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
