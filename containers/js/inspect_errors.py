import pandas as pd
import argparse

def main_with_args(src_file: str): 
    raw_df = pd.read_json(src_file, lines=True, orient="records")
    df = raw_df[raw_df["exit_code"] != 0]
    df = df[~df["stderr"].isna()]
    df = df[df["stderr"].str.contains("Node.js")]
    for item in df.iloc:
        print(item["stderr"])
        print("-" * 100)

    print(f"Found {len(df)} errors that are from Node.js")

    missing_module_errors = df[df["stderr"].str.contains("Cannot find module")]
    missing_modules = missing_module_errors["stderr"].str.extract(r"Cannot find module '(.*)'")
    print("\n".join(missing_modules[0].unique()))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("src_file", type=str)
    args = parser.parse_args()
    main_with_args(args.src_file)

if __name__ == "__main__":
    main()
