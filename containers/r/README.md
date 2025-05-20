# Julia Container for BigCodeBench-MultiPL

This is a container that runs Julia programs. It receives a program and its test
suite over standard input, runs it, and prints the result of execution to
standard output. For example, an input line must have the following fields:

```javascript
{"task_id": str,"program": str, "test_suite": str }
```

And an output line will have the following fields:

```javascript
{ "task_id": str"exit_code": int, "timeout": bool "stdout": str, "stderr": str }
```

But, here is what is peculiar: **the test suite must be written in Python**,
even though the program is written in Julia.

What's going on? We expect that the Julia program receives input over standard
input and responds with its result over standard output. But, this means that
the test harness need not be in Julia itself.

We expect the test harness to be a Python module that has a single function
called `test_cases` with the following signature:

```python
def test_cases(runner) -> None:
    ...
```

The `runner` argument will itself be a function that calls the Julia program: it
will take a string input (for standard input), and return a tuple with the
program's output and exit code.

For example, suppose the Julia program computes factorials, but exits with exit
code 1 if the input is negative. Here is a test suite that tests this behavior:

```python
def test_cases(runner):
    assert runner("0") == ("1", 0)
    assert runner("5") == ("120", 0)
    assert runner("-1")[1] == 1
```


