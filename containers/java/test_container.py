import json
import subprocess

CONTAINER_NAME = "ghcr.io/aryawu0513/bcb_multipl-java"

FACTORIAL_PROGRAM = """
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        int n = scanner.nextInt();
        System.out.println(factorial(n));
    }
    
    public static String factorial(int n) {
        if (n < 0) {
            return "Error: negative input";
        } else if (n == 0) {
            return "1";
        } else {
            long result = 1;
            for (int i = 1; i <= n; i++) {
                result *= i;
            }
            return String.valueOf(result);
        }
    }
}
"""

INFINITE_LOOP_PROGRAM = """
public class Main {
    public static void main(String[] args) {
        infiniteLoop();
    }
    
    public static void infiniteLoop() {
        while (true) {
            // Infinite loop
        }
    }
}
"""

################################################################################
# The below is language-agnostic. You should not need to modify it. You just   #
# need to update the container name and the two test programs above.           #
################################################################################


def run_container(program, test_suite):
    """Run the container with the given program and test suite."""
    input_data = json.dumps({"task_id": "test", "program": program, "test_suite": test_suite})

    result = subprocess.run(
        ["podman", "run", "--rm", "-i", CONTAINER_NAME],
        input=input_data,
        capture_output=True,
        text=True,
    )
    
    print(f"Return code: {result.returncode}")
    print(f"Stdout: '{result.stdout}'")
    print(f"Stderr: '{result.stderr}'")
    
    if not result.stdout.strip():
        raise Exception(f"Empty stdout! Return code: {result.returncode}, Stderr: {result.stderr}")

    return json.loads(result.stdout)


def test_factorial():
    test_suite = """
def test_cases(runner):
    assert runner("0") == ("1\\n", 0)
    assert runner("5") == ("120\\n", 0)
    assert runner("-1") == ("Error: negative input\\n", 0)
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

if __name__ == "__main__":
    test_factorial()
    test_infinite_loop()
    print("All tests passed.")