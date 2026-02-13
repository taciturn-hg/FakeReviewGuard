import pandas as pd
import json
import os
import time
import sys
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

def get_deepseek_client():
    if not API_KEY or API_KEY == "your-deepseek-api-key-here":
        logger.error("DEEPSEEK_API_KEY not found or default in settings.")
        logger.info("Please update .env file with your actual DEEPSEEK_API_KEY")
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
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt+1} failed: {e}. Retrying...")
                time.sleep(2)
                
    except Exception as e:
        logger.error(f"Error annotating: {e}")
        return {"label": "Error", "reasoning": str(e)}

def main():
    # 使用绝对路径以确保在任何目录运行都能找到文件
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', '..', 'data', 'processed')
    
    input_file = os.path.join(data_dir, 'sample_reviews_for_annotation.csv')
    output_file = os.path.join(data_dir, 'labeled_reviews.csv')
    
    if not os.path.exists(input_file):
        logger.error(f"File {input_file} not found. Run shared/utils/data_cleaner.py first to generate 'sample_reviews_for_annotation.csv'.")
        return

    df = pd.read_csv(input_file)
    client = get_deepseek_client()
    
    if not client:
        # Mocking the process for demonstration if no key is provided
        logger.warning("[DEMO MODE] No API Key provided. Generating Mock Labels...")
        logger.info("In a real scenario, DeepSeek would analyze each review.")
        
        # Simple heuristic for mock labels
        df['label'] = df['extract'].apply(lambda x: 'Fake' if len(str(x)) < 30 or 'great' in str(x).lower() else 'Real')
        df['reasoning'] = "Mock reasoning based on length/keywords."
    else:
        logger.info("Starting annotation with DeepSeek...")
        labels = []
        reasonings = []
        
        for index, row in df.iterrows():
            logger.info(f"Annotating review {index + 1}/{len(df)}...")
            result = annotate_review(client, row['extract'], row['score'], row['product'])
            labels.append(result.get('label', 'Unknown'))
            reasonings.append(result.get('reasoning', 'No reasoning'))
            time.sleep(0.5) # Rate limiting
            
        df['label'] = labels
        df['reasoning'] = reasonings

    # 过滤掉标注失败的数据
    valid_df = df[df['label'] != 'Error']
    error_df = df[df['label'] == 'Error']
    
    if not error_df.empty:
        logger.warning(f"Warning: {len(error_df)} reviews failed annotation.")
        error_file = os.path.join(data_dir, 'annotation_errors.csv')
        error_df.to_csv(error_file, index=False)
        logger.info(f"Errors saved to {error_file}")

    valid_df.to_csv(output_file, index=False)
    logger.info(f"Annotation complete. Saved {len(valid_df)} reviews to {output_file}")
    print(valid_df[['extract', 'label', 'reasoning']].head())

if __name__ == "__main__":
    main()
