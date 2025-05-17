# BigCodeBench-MultiPL

[BigCodeBench] is an LLM programming benchmark with complex tasks that cover
several domains. However, every task can only be solved in Python.
BigCodeBench-MultiPL is aprogramming language-neutral benchmark that is based on
BigCodeBench.

A goal of this project is scalability: we believe it is *very easy* to test a
new programming language with BigCodeBench-MultiPL. All you need to do is build
a new container. Unlike [MultiPL-E], there is no need to adapt prompts or update
the test cases. The prompts in BigCodeBench-MultiPL are already language
neutral. Moreover, all interactions with model-generated code occurs via
standard I/O, so we can use the same tests for every language.

## Benchmarking a Model

1. **Generate Completions**: We have a very simple script to generate
   completions. All it  does is add "Solve this problem using *L*" to the prompt
   and then queries an LLM. For example, the following command generates
   completions for Julia using GPT-4.1-nano:

   ```bash
   python3 bigcodebench_multipl/src/completions.py \
       --batch-size 50 \
       --model openai/gpt-4.1-nano \
       --benchmark nuprl-staging/BigCodeBench-MultiPL \
       --lang "Julia" \
       --output-path julia.jsonl
   ```
   
   The output JSONL file has a field called `program` with model-generated
   Julia code. There is also a field called `response` with the complete response
   from the model, from which we extract the program.

   *NOTE*: If you want to use your own code to generate completions, each output
   line must have the fields `task_id` and `test_suite` from the benchmark,
   and a new field called `program`  with the model-generated code.

2. **Test Generated Code:** The next step is to test the model-generated code
   using the language-specific container. First, check how many programs you have:

   ```bash
   wc -l julia.jsonl
   ```

   Then run all tehse programs in parallel with the Julia container. Use the
   number of lines above for `NUM_PROBLEMS`. The flag `-j16` means that we are
   running 16 containers concurrently. You probably want ~32GB of memory and 32
   cores to run that many safely. You can adjust the `-j` flag as needed.

   ```bash
   parallel --bar -j16 \
       ./containers/py/job.sh julia.jsonl \
       ::: $(seq $NUM_PROBLEMS) > julia.results.jsonl
   ```

   If you generated programs for a different language, do ensure you use the
   appropriate container.

3. **Compute Pass@1:**: This is just the fraction of programs that pass all
   tests.

   ```bash
   jq -s '([.[] | select(.exit_code == 0)] | length) as $success | ($success * 100 / length) | "pass@1: \(.)%"' \
       julia.results.jsonl
   ```

## Adding Support for a New Programming Language

You should start by modifying an existing container. Look at the Julia
container in `containers/jl` for an example that is well-documented.

## Constructing the Benchmark

See the README in the `bigcodebench_multipl` directory. for instructions on
how to construct the benchmark.

## Acknowledgements

This work is supported by grants from the U.S. National Science Foundation
(SES-2326173) and U.S. Department of Energy, Office of Science (DE-SC0025613).



[BigCodeBench]: https://openreview.net/forum?id=YrycTjllL0
[MultiPL-E]: https://ieeexplore.ieee.org/document/10103177
