import pandas as pd
import glob
import os

def analyze_files():
    # 使用绝对路径定位数据目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_data_dir = os.path.join(base_dir, '..', '..', 'data', 'raw')
    
    # 搜索 raw 目录下的 csv 文件
    search_pattern = os.path.join(raw_data_dir, '*.csv')
    files = glob.glob(search_pattern)
    print(f"正在搜索目录: {search_pattern}")
    print(f"找到文件: {files}")
    
    total_rows = 0
    dfs = []
    
    for f in files:
        df = None
        for encoding in ['utf-8', 'latin-1', 'cp1252', 'ISO-8859-1']:
            try:
                df = pd.read_csv(f, encoding=encoding)
                print(f"\n成功读取文件 {f}，使用编码: {encoding}")
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"读取文件 {f} 失败 (编码 {encoding}): {e}")
                break
        
        if df is None:
            print(f"无法使用常见编码读取文件 {f}")
            continue

        print(f"文件 {f} 分析结果:")
        print(f"列名: {df.columns.tolist()}")
        print(f"行数: {len(df)}")
        print(f"评分分布:\n{df['score'].describe()}")
        print(f"唯一来源数: {df['source'].nunique()}")
        dfs.append(df)
        total_rows += len(df)


    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)
        print(f"\n总行数: {total_rows}")
        print("评论样本:")
        print(full_df[['extract', 'score']].head())

if __name__ == "__main__":
    analyze_files()
