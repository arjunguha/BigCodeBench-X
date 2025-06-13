# BigCodeBench-MultiPL

This is a new programming benchmark for LLMs with two goals:

1. Support as many niche ("low-resource") programming languages as possible, such as Julia, Fortran, R, and others.

   Although LLMs are remarkably good at Python and other high-resource languages, they are much worse at low-resource
   programming languages. A high-quality benchmark is necessary to both to measure LLM capabilities and to make LLMs better.

2. Make it easy to support new programming languages a wide variety of programming tasks.

   Writing a good benchmark is hard, and we don't to duplicate effort for each language. Prior work,
   such as [MultiPL-E], reduce the effort needed, but only support a small sliver of programming
   tasks. Our goal is to reduce effort even further and support a much broader range of programming
   tasks than MultiPL-E.

## Approach

We start with [BigCodeBench], which is an LLM programming benchmark with complex Python programming 
tasks. Each task is accompanied with a reference solution and a comprehensive test suite, both in Python
of course. We proceed in three steps:

1. We prompt a reasoning model to reformulate the task, including the reference solution and test suite, to [use standard I/O and re-use as much of the existing code as possible](https://github.com/arjunguha/BigCodeBench-MultiPL/blob/main/bigcodebench_multipl/src/make_stdio_problem.py#L13). The result is a new benchmark -- still for Python -- that uses standard I/O. We can partially-validate this translation step by running the updated code. With just one attempt, using o4-mini, ~75% of the ~1,000 updated problems pass their own test suite. 

2. We prompt a model to update the task description to [remove references to Python and Python terminology](https://github.com/arjunguha/BigCodeBench-MultiPL/blob/main/bigcodebench_multipl/src/make_pl_agnostic_problem.py#L22). This requires human validation, but our [preliminary work](https://gist.github.com/arjunguha/92e7d0aebbc9b61acb37ef019c97e851) indicates that gpt-4.1-mini does this task well. Notice that we do not need to update the test suite to be language specific. Since the task uses standard I/O, the tests can be in Python even if the program is in another language.

3. We build containers for each niche language. We have a few already in the [containers](https://github.com/arjunguha/BigCodeBench-MultiPL/tree/main/containers) directory. The Julia container is well documented and should be a template for building other containers.

## Benchmarking a Model

To follow these directions, you will need:

- Docker or Podman to run containers.
- A Python environment with `tqdm`, `datasets`, and `litellm` installed.
- The `jq` tool, which will be available from your Linux package
  manager.

1. **Generate and Execute Completions:** Our benchmark execution script
   will generate completions with the LLM and execute the generated code in
   a container. For example, the following command benchmarks JavaScript:

   ```
   python3 -m bigcodebench_multipl.run_benchmark generate \
       --model-name openai/gpt-4.1-nano \
       --temperature 0.2 \
       --num-concurrent-requests 50 \
       --max-tokens 2000 \
       --lang "JavaScript using Node 24" \
       --container-name "ghcr.io/arjunguha/bcb_multipl-js" \
       --output-path js.jsonl
   ```

   This assumes that you can run 50 containers concurrently. If you have
   fewer cores, you can reduce the number of concurrent requests.

   Notice that we use *JavaScript using Node 24* as the language. This is the
   version of Node that is installed in the container. It is important to convey
   this information to the model, since JavaScript on the web is quite different
   from server-side JavaScript.
   
   The output JSONL file has a field called `program` with model-generated
   JavaScript code.

2. **Compute Pass@1:** This is just the fraction of programs that pass all
   tests.

   ```bash
   ./bin/pass1.sh js.jsonl
   ```

## Adding Support for a New Programming Language

To support a new programming language, you will need to write a container that
can run its code. However, you also need to decide what libraries should be
available in the container. The best way to do this is to first generate
completions for your language with some model. It may make the most sense to
use what you think is the best model for your language. Use your text processing
skills to extract the list of libraries that the model is trying to use. With
that list, you can build a container that has those libraries installed.

We recommend modifying an existing container. Look at the Julia container in
`containers/jl` for an example that is well-documented.

## Constructing the Benchmark

See the README in the `bigcodebench_multipl` directory. for instructions on
how to construct the benchmark.

## Preliminary Results

- A preliminary version of the benchmark is in this 
  [Hugging Face Dataset](https://huggingface.co/datasets/nuprl-staging/BigCodeBench-MultiPL).

- We are putting generations from models in this [Hugging Face Dataset](https://huggingface.co/datasets/nuprl/BigCodeBench-MultiPL-Results).

- See this [Google Sheet](https://docs.google.com/spreadsheets/d/1KMcZ_sFjM5N6XoUntgIip9ZkSu-htKthlx8DUD-AG90/edit?usp=sharing)
  for model evaluations.

## Acknowledgements

This work is supported by grants from the U.S. National Science Foundation
(SES-2326173) and the U.S. Department of Energy, Office of Science (DE-SC0025613).

[BigCodeBench]: https://openreview.net/forum?id=YrycTjllL0
[MultiPL-E]: https://ieeexplore.ieee.org/document/10103177
