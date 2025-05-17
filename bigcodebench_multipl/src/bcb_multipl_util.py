"""
This code is adapted from github.com/nuprl/prl_ml, which is an internal
repository.
"""

from typing import Optional


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
    first_newline = code.find("\n")
    if first_newline > 0:
        # Consider the case where the block begins with "```python\n...". In this
        # case, code would already be "python\n..." and first_newline would be 7.
        # Thus first_newline + 1 is the index of "...".
        code = code[first_newline + 1 :]

    return code.strip()
