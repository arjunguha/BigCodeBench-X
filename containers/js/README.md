# JavaScript Container for BigCodeBench-MultiPL

See the Julia container for more information on the protocol that this container
uses.

In addition, we have some helpful scripts:

- `fixup_js.py` temporary script to address model output where the first
  fenced code block is not the JavaScript program. We instead use the longest
  fenced code block.

- `inspect_erorrs.py` to help debug spurious execution errors.
