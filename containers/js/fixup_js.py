import pandas as pd
import marko
from typing import List
from marko.block import FencedCode, BlockElement
import numpy as np
import argparse
def _extract_code_blocks(acc: List[str], node: BlockElement):
    if isinstance(node, FencedCode):
        code_str = node.children[0].children
        assert isinstance(code_str, str)
        assert len(node.children) == 1
        acc.append(code_str)
        return
    
    for child in node.children:
        if not isinstance(child, BlockElement):
            continue
        _extract_code_blocks(acc, child)

def extract_fenced_code_blocks(text: str):
    doc = marko.parse(text)
    code_blocks = [ ]
    _extract_code_blocks(code_blocks, doc)
    return code_blocks

def longest_code_block(texts):
    return texts[np.argmax([len(t) for t in texts])]

def main_with_args(src_file: str, out_file: str):
    raw_df = pd.read_json(src_file, lines=True, orient="records")
    code_blocks = raw_df["response"].apply(extract_fenced_code_blocks)
    code_block_lens = code_blocks.apply(len)
    likely_code = code_blocks.apply(longest_code_block)
    raw_df["program"] = likely_code

    raw_df.to_json(out_file, orient="records", lines=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_file", type=str)
    parser.add_argument("out_file", type=str)
    args = parser.parse_args()
    main_with_args(args.src_file, args.out_file)

if __name__ == "__main__":
    main()
