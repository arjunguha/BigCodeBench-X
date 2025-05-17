# BigCodeBench-MultiPL

[BigCodeBench] is an LLM programming benchmark with complex tasks that cover
several domains. However, every task can only be solved in Python. This project
is a new, programming language-neutral benchmark that is based on BigCodeBench.

A goal of this project is scalability: we believe it is *very easy* to test a
new programming language with BigCodeBench-MultiPL. All you need to do is build
a new container. Unlike [MultiPL-E], there is no need to adapt prompts or update
the test cases. The prompts in BigCodeBench-MultiPL are already language
neutral. Moreover, all interactions with model-generated code occurs via
standard I/O, so we can use the same tests for every language.

## Benchmarking a Model

[FILL]

## Adding Support for a New Programming Language

[FILL]


## Constructing the Benchmark

See the README in the `bigcodebench_multipl` directory. for instructions on
how to construct the benchmark.

## Acknowledgements



[BigCodeBench]: https://openreview.net/forum?id=YrycTjllL0
[MultiPL-E]: https://ieeexplore.ieee.org/document/10103177
