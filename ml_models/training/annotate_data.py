import pandas as pd
import json
import os
import time
import sys
import concurrent.futures
from openai import OpenAI
from dotenv import load_dotenv

# 添加项目根目录到 sys.path 以便导入 shared 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.config.settings import settings
from shared.utils import logger

# 加载 .env 文件中的环境变量
load_dotenv()

API_KEY = settings.DEEPSEEK_API_KEY
BASE_URL = "https://api.deepseek.com"

def _is_invalid_api_key(api_key) -> bool:
    """
    Return True if the provided API key is missing, empty, or looks like a placeholder.
    This helps avoid accidentally using default/placeholder values in production.
    """
    if not api_key:
        return True

    api_key_str = str(api_key).strip()
    if not api_key_str:
        return True

    lower_key = api_key_str.lower()

    # Exact known placeholder value
    if lower_key == "your-deepseek-api-key-here":
        return True

    # Generic placeholder-like patterns
    if "your-" in lower_key or "-here" in lower_key:
        return True

    return False

def get_deepseek_client():
    if _is_invalid_api_key(API_KEY):
        logger.error("设置中未找到 DEEPSEEK_API_KEY 或为默认/占位符。")
        logger.info("请在 .env 文件中更新您的实际 DEEPSEEK_API_KEY")
        return None
    return OpenAI(api_key=API_KEY, base_url=BASE_URL)

def annotate_review(client, text, score, product):
    prompt = f"""
    You are an expert in detecting fake e-commerce reviews. 
    Analyze the following review for a mobile phone.
    
    Product: {product}
    Score: {score}
    Review: "{text}"
    
    Task: 
    1. Analyze the sentiment of the review (Positive, Negative, Neutral).
    2. Determine if the sentiment matches the score (e.g., High score with negative text is suspicious).
    3. Determine if this review is likely 'Real' or 'Fake'.
    
    Consider factors like:
    - Generic or repetitive language (Fake)
    - Lack of specific details about usage (Fake)
    - Overly enthusiastic or promotional tone (Fake)
    - Mismatches between score and text (Fake)
    - Natural language, specific pros/cons (Real)
    
    Return ONLY a JSON object with the following format:
    {{
        "sentiment": "Positive",
        "sentiment_score_match": true,
        "label": "Real",
        "reasoning": "Brief explanation including sentiment analysis"
    }}
    
    Where:
    - "sentiment" must be one of: "Positive", "Negative", or "Neutral".
    - "sentiment_score_match" must be a boolean indicating whether the sentiment matches the score.
    - "label" must be either "Real" or "Fake".
    """
    
    try:
        # 简单的重试机制
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=settings.LLM_MODEL_NAME, # 使用 settings 中的模型名
                    messages=[
                        {"role": "system", "content": "You are a helpful data annotation assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" },
                    temperature=0.1
                )
                content = response.choices[0].message.content
                # 清洗可能存在的 Markdown 标记
                content = content.replace('```json', '').replace('```', '').strip()
                return json.loads(content)
            except Exception as e:
                error_msg = str(e)
                # 区分错误类型
                if "401" in error_msg or "authentication" in error_msg.lower():
                    logger.error(f"API 认证错误: {e}。请检查您的 API Key。")
                    raise e # 认证错误不需要重试
                elif "429" in error_msg or "rate limit" in error_msg.lower():
                    wait_time = (attempt + 1) * 5
                    logger.warning(f"超出速率限制。等待 {wait_time} 秒后重试...")
                    time.sleep(wait_time)
                elif "500" in error_msg or "502" in error_msg or "503" in error_msg:
                    logger.warning(f"服务器错误 ({e})。正在重试...")
                    time.sleep(2)
                else:
                    logger.warning(f"第 {attempt+1} 次尝试失败: {e}。正在重试...")
                    time.sleep(2)
                
                if attempt == max_retries - 1:
                    raise e
                
    except Exception as e:
        logger.error(f"标注错误: {e}")
        return {"label": "Error", "reasoning": str(e)}

def process_single_review(client, row, index, total, request_delay):
    # This helper function handles single review annotation logic
    try:
        result = annotate_review(client, row['extract'], row['score'], row['product'])
        return {
            'index': index,
            'label': result.get('label', 'Unknown'),
            'reasoning': result.get('reasoning', 'No reasoning')
        }
    except Exception as e:
        logger.error(f"Error processing review {index}: {e}")
        return {
            'index': index,
            'label': 'Error',
            'reasoning': str(e)
        }

def main():
    # 使用绝对路径以确保在任何目录运行都能找到文件
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', '..', 'data', 'processed')
    
    input_file = os.path.join(data_dir, 'sample_reviews_for_annotation.csv')
    output_file = os.path.join(data_dir, 'labeled_reviews.csv')
    
    if not os.path.exists(input_file):
        logger.error(f"未找到文件 {input_file}。请先运行 shared/utils/data_cleaner.py 生成 'sample_reviews_for_annotation.csv'。")
        return

    # Load existing labels if available to avoid re-annotating
    existing_labels_map = {}
    if os.path.exists(output_file):
        try:
            existing_df = pd.read_csv(output_file)
            # Create a lookup key based on extract and product (or just extract if unique enough)
            # Using tuple of (extract, product) as key
            for _, row in existing_df.iterrows():
                key = (str(row.get('extract', '')).strip(), str(row.get('product', '')).strip())
                existing_labels_map[key] = {
                    'label': row.get('label'),
                    'reasoning': row.get('reasoning')
                }
            logger.info(f"已加载 {len(existing_labels_map)} 条现有标注数据，将跳过重复项。")
        except Exception as e:
            logger.warning(f"读取现有标注文件失败，将重新标注所有数据: {e}")

    df = pd.read_csv(input_file)
    client = get_deepseek_client()
    
    if not client:
        # Mocking the process for demonstration if no key is provided
        logger.warning("[演示模式] 未提供 API Key。正在生成模拟标签...")
        logger.info("在真实场景中，DeepSeek 将分析每条评论。")
        
        # Simple heuristic for mock labels
        df['label'] = df['extract'].apply(lambda x: 'Fake' if len(str(x)) < 30 or 'great' in str(x).lower() else 'Real')
        df['reasoning'] = "Mock reasoning based on length/keywords."
    else:
        logger.info("开始使用 DeepSeek 进行标注 (并发模式)...")
        
        # Initialize lists with placeholders to maintain order or use index mapping
        labels = [''] * len(df)
        reasonings = [''] * len(df)
        
        # Prepare tasks
        new_indices = []
        
        # Identify which rows need annotation
        for index, row in df.iterrows():
            # 使用 pandas.isna 判断缺失值，避免 NaN 被统一转换为字符串 "nan" 导致缓存键冲突
            raw_extract = row['extract']
            raw_product = row['product']

            if pd.isna(raw_extract):
                # 为缺失 extract 生成包含行索引的唯一占位符，确保不同 NaN 记录不会共享同一键
                extract_val = f"__NA_EXTRACT_{index}__"
            else:
                extract_val = str(raw_extract).strip()

            if pd.isna(raw_product):
                # 为缺失 product 生成包含行索引的唯一占位符，确保不同 NaN 记录不会共享同一键
                product_val = f"__NA_PRODUCT_{index}__"
            else:
                product_val = str(raw_product).strip()
            key = (extract_val, product_val)
            
            if key in existing_labels_map:
                cached = existing_labels_map[key]
                labels[index] = cached['label']
                reasonings[index] = cached['reasoning']
            else:
                new_indices.append(index)

        logger.info(f"需要新标注 {len(new_indices)} 条评论，复用 {len(df) - len(new_indices)} 条。")

        if new_indices:
            # 默认请求延迟设置为 0.3 秒，以在无额外限流的情况下降低触发 DeepSeek 速率限制风险
            request_delay = getattr(settings, "deepseek_request_delay_seconds", 0.3)
            # 使用较小的并发线程数，进一步控制整体 QPS，避免触发 DeepSeek API 速率限制
            max_workers = 4
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_index = {
                    executor.submit(process_single_review, client, df.iloc[idx], idx, len(df), request_delay): idx 
                    for idx in new_indices
                }
                
                completed_count = 0
                for future in concurrent.futures.as_completed(future_to_index):
                    idx = future_to_index[future]
                    try:
                        res = future.result()
                        labels[idx] = res['label']
                        reasonings[idx] = res['reasoning']
                        completed_count += 1
                        if completed_count % 10 == 0:
                            logger.info(f"进度: {completed_count}/{len(new_indices)} 新评论已标注")
                    except Exception as exc:
                        logger.error(f"Review {idx} generated an exception: {exc}")
                        labels[idx] = 'Error'
                        reasonings[idx] = str(exc)

        df['label'] = labels
        df['reasoning'] = reasonings
        logger.info(f"标注过程结束。")

    # 过滤掉标注失败的数据
    valid_df = df[df['label'] != 'Error']
    error_df = df[df['label'] == 'Error']
    
    if not error_df.empty:
        logger.warning(f"警告: {len(error_df)} 条评论标注失败。")
        error_file = os.path.join(data_dir, 'annotation_errors.csv')
        error_df.to_csv(error_file, index=False)
        logger.info(f"错误已保存至 {error_file}")

    valid_df.to_csv(output_file, index=False)
    logger.info(f"标注完成。已保存 {len(valid_df)} 条评论至 {output_file}")
    print(valid_df[['extract', 'label', 'reasoning']].head())

if __name__ == "__main__":
    main()
