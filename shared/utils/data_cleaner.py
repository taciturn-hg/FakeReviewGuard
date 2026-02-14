import pandas as pd
import glob
import os

def load_and_sample(sample_size=2000, output_file='sample_reviews_for_annotation.csv'):
    # Adjust paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_dir = os.path.join(base_dir, '..', '..', 'data', 'raw')
    processed_data_dir = os.path.join(base_dir, '..', '..', 'data', 'processed')
    
    # Create directories if needed
    os.makedirs(processed_data_dir, exist_ok=True)
    
    # Update search path for CSVs
    search_pattern = os.path.join(raw_data_dir, 'phone_user_review_file_*.csv')
    files = glob.glob(search_pattern)
    
    dfs = []
    
    for f in files:
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'ISO-8859-1']:
            try:
                df = pd.read_csv(f, encoding=encoding)
                # Keep only relevant columns
                if 'extract' in df.columns and 'score' in df.columns:
                    # 确保所有需要的列都存在；对缺失列使用缺失值标记而不是合成字符串，避免掩盖数据质量问题
                    required_cols = ['extract', 'score', 'source', 'date', 'product']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        print(f"Warning: file {os.path.basename(f)} is missing columns {missing_cols}; filling with NaN.")
                        for col in missing_cols:
                            df[col] = pd.NA
                    df = df[required_cols]
                    dfs.append(df)
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Skipping {f}: {e}")
                break
    
    if not dfs:
        print("No data loaded.")
        return

    full_df = pd.concat(dfs, ignore_index=True)
    
    # Basic cleaning
    full_df = full_df.dropna(subset=['extract'])
    # 改进去重逻辑：结合评论内容、产品名、来源和日期进行去重，避免误删不同时间的有效评论
    full_df = full_df.drop_duplicates(subset=['extract', 'product', 'source', 'date'])
    
    # Sample
    sample_df = full_df.sample(n=min(sample_size, len(full_df)), random_state=42)
    
    # Save
    output_path = os.path.join(processed_data_dir, output_file)
    sample_df.to_csv(output_path, index=False)
    print(f"Saved {len(sample_df)} reviews to {output_path}")
    print(sample_df.head())

if __name__ == "__main__":
    load_and_sample()
