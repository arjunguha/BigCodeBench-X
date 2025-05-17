This purpose of this project is to turn the BigCodeBench problems into
problems that receive input and output using standard I/O. This is intended to
be an intermediate step before making BigCodeBench language agnostic.

## Step 1: Transform Problems To Use Standard I/O

1. Use a language model to modify the problems to use standard I/O.

   ```bash
   python3 src/make_stdio_problem.py \
       --batch-size 50 \
       --output-path unfiltered_stdio.jsonl
   ```

   By default, the script uses o4-mini. You must have the `OPENAI_API_KEY`
   environment variable set.

   This will produce a JSONL file with the following fields:

   - `task_id`: The original Task ID from BigCodeBench
   - `reasoning`: The model's chain of thought, which may help debug.
   - `prompt`: The modified problem statement.
   - `program`: The modified program.
   - `test_suite`: The modified test suite.

   **Manual verification:**: You should now manually review a sample of the 
   edits that the model has made.

2. Filter the output to remove problems that failed by running the test suites:

   ```bash
   LINES=$(wc -l < unfiltered_stdio.jsonl)
   parallel --bar -j16 ../containers/py/job.sh unfiltered_stdio.jsonl --program-field  ::: $(seq $LINES) > unfiltered_stdio.results.jsonl
   ```

   Notice I'm using 16 concurrent processes. You probably want ~32GB of memory
   and 32 cores to run that many safely. You can adjust the `-j` flag as needed.


3. Filter out problems that fail to translate:

   ```bash
   python3 src/apply_exec_filter.py unfiltered_stdio.jsonl unfiltered_stdio.results.jsonl --output-file filtered_stdio.jsonl
   wc -l filtered_stdio_bcb.jsonl
   ```

   You can include failed problems by adding the `--include-failed` flag.

    **Manual verification:** You should check to see that how many problems are
    in the filtered dataset versus the original dataset (e.g., using `wc -l`).
    You should also check the distribution of problems by type.
   

At this point, `filtered_stdio.jsonl` is a new benchmark of problems that
use standard I/O instead for input and output instead of Python values. However,
they are still Python programming tasks.

## Step 2: Make Problems Language Agnostic


1. Use a language model to modify the problems to be language agnostic.

   ```bash
   python3 src/make_pl_agnostic_problem.py \
       --batch-size 50 \
       --input-problems filtered_stdio.jsonl \
       --output-problems unfiltered_agnostic.jsonl \
   ```

   By default, the script uses o4-mini. You must have the `OPENAI_API_KEY`
   environment variable set.

   This will produce a JSONL file with the following fields:

   - `task_id`: The original Task ID from BigCodeBench
   - `reasoning`: The model's chain of thought, which may help debug.
   - `program`: The Python solution to the problem
   - `test_suite`: The Python test suite for the problem.
   - `prompt`: The modified, language-neutral problem statement.

   **Manual verification:**: You should now manually review a sample of the 
   edits that the model has made to the prompts. Ask yourself if the
   program and test suite still make sense with the edited prompt.

At this point, the file `unfiltered_agnostic.jsonl` is a benchmark.
All you need to do at this point is run the prompts through an LLM with a
prefix/suffix that effectively says "solve the problem in language *L*".

You probably want to upload this dataset to the Hugging Face Hub to benchmark
models on various languages. 


## Step 3: