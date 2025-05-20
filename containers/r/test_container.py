import json
import subprocess

CONTAINER_NAME = "ghcr.io/canders1/bcb_multipl-r"

FACTORIAL_PROGRAM = """

factorial_r <- function(n) {
  if (n < 0) {
    return("Error: negative input")
  } else if (n == 0) {
    return(1)
  } else {
    return(prod(1:n))
  }
}

n = as.integer(readLines(con="stdin",n=1))

cat(paste0(factorial_r(n),"\n"))
"""

INFINITE_LOOP_PROGRAM = """
infinite_loop <- function() {
    while(TRUE){
    }
  }

infinite_loop()
"""

################################################################################
# The below is language-agnostic. You should not need to modify it. You just   #
# need to update the container name and the two test programs above.           #
################################################################################


def run_container(program, test_suite):
    """Run the container with the given program and test suite."""
    input_data = json.dumps({"program": program, "test_suite": test_suite, "task_id":"0"})

    result = subprocess.run(
        ["podman", "run", "--rm", "-i", CONTAINER_NAME],
        input=input_data,
        capture_output=True,
        text=True,
    )

    return json.loads(result.stdout)


def test_factorial():
    test_suite = """
def test_cases(runner):
    zero_case = runner("0\\n")
    print(zero_case)
    assert zero_case == ("1\\n", 0)
    assert runner("5\\n") == ("120\\n", 0)
    assert runner("-1\\n") == ("Error: negative input\\n", 0)
"""

    result = run_container(FACTORIAL_PROGRAM, test_suite)
    print(result)
    assert result["exit_code"] == 0
    assert not result["timeout"]
    assert result["stderr"].strip() == ""


def test_infinite_loop():
    test_suite = """
def test_cases(runner):
    # This should timeout
    result = runner("")
    assert result[1] != 0  # Should have non-zero exit code
"""

    result = run_container(INFINITE_LOOP_PROGRAM, test_suite)
    print(result)
    assert result["timeout"]  # Should timeout
    assert result["exit_code"] != 0  # Should have non-zero exit code
