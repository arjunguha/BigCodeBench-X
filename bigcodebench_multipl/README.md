This purpose of this project is to turn the BigCodeBench problems into
problems that receive input and output using standard I/O. This is intended to
be an intermediate step before making BigCodeBench language agnostic.

## Step 0: Installation and Configuration

1. [FILL] dependencies, etc. Uv or not.

2. You must also configure the LLM that you intend to **Before you begin, you
   must configure the LLM that you will use. By default, the scripts are setup
   to use OpenAI models, and you will need to set the `OPENAI_API_KEY`
   environment variable. However, it is also possible to use other models. Use
   `--help` with any script to see how to configure the model.

## Step 1: Transform Problems To Use Standard I/O

1. Use a language model to modify the problems to use standard I/O.

   ```bash
   python3 src/make_stdio_problem.py \
       --batch-size 50 \
       --output-path unfiltered_stdio.jsonl
   ```

   This will produce a JSONL file where each line has the following fields:

   - `task_id`: The original Task ID from BigCodeBench
   - `reasoning`: The model's chain of thought, which may help debug.
   - `prompt`: The modified problem statement.
   - `program`: The modified program.
   - `test_suite`: The modified test suite.

   **Manual verification:**: You should now manually review a sample of the 
   edits that the model has made.

   *TODO(arjun):* We should build an application to support this. This
   code is a good starting point: https://gist.github.com/arjunguha/92e7d0aebbc9b61acb37ef019c97e851.

2. Filter the output to remove problems that failed by running the test suites.
   First, determine how many problems there are:

   ```
   wc -l unfiltered_stdio.jsonl
   ```

   Then, run each problem in the Python container with the code below.
   Use the number of lines above for `NUM_PROBLEMS`. The flag `-j16` means
   that we are running 16 containers concurrently. You probably want ~32GB of
   memory and 32 cores to run that many safely. You can adjust the `-j` flag as
   needed.

   ```bash
   parallel --bar -j16 ../containers/py/job.sh unfiltered_stdio.jsonl --program-field  ::: $(seq NUM_PROBLEMS) > unfiltered_stdio.results.jsonl
   ```

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