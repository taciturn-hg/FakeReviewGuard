import pandas as pd
import glob
import os

def analyze_files():
    files = glob.glob('*.csv')
    print(f"Found files: {files}")
    
    total_rows = 0
    dfs = []
    
    for f in files:
        df = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'ISO-8859-1']:
            try:
                df = pd.read_csv(f, encoding=encoding)
                print(f"\nSuccessfully read {f} with encoding {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading {f} with {encoding}: {e}")
                break
        
        if df is None:
            print(f"Failed to read {f} with any common encoding")
            continue

        print(f"Analysis of {f}:")
        print(f"Columns: {df.columns.tolist()}")
        print(f"Rows: {len(df)}")
        print(f"Score distribution:\n{df['score'].describe()}")
        print(f"Unique sources: {df['source'].nunique()}")
        dfs.append(df)
        total_rows += len(df)


    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)
        print(f"\nTotal Rows: {total_rows}")
        print("Sample Reviews:")
        print(full_df[['extract', 'score']].head())

if __name__ == "__main__":
    analyze_files()
