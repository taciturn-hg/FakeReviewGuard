import pandas as pd
import json
import os
import time
from openai import OpenAI

# NOTE: You need to install the openai library: pip install openai
# NOTE: Replace 'YOUR_DEEPSEEK_API_KEY' with your actual API key
API_KEY = "sk-afc7316c31784ae5b7db844c482410be"
BASE_URL = "https://api.deepseek.com" # Verify the correct DeepSeek API endpoint

def get_deepseek_client():
    if API_KEY == "YOUR_DEEPSEEK_API_KEY":
        print("Please set your DeepSeek API Key in the script.")
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
        "sentiment": "Positive/Negative/Neutral",
        "sentiment_score_match": true/false,
        "label": "Real" or "Fake",
        "reasoning": "Brief explanation including sentiment analysis"
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # or deepseek-reasoner
            messages=[
                {"role": "system", "content": "You are a helpful data annotation assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format={ "type": "json_object" },
            temperature=0.1
        )
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error annotating: {e}")
        return {"label": "Error", "reasoning": str(e)}

def main():
    input_file = 'sample_reviews_for_annotation.csv'
    output_file = 'labeled_reviews.csv'
    
    if not os.path.exists(input_file):
        print(f"File {input_file} not found. Run preprocess.py first.")
        return

    df = pd.read_csv(input_file)
    client = get_deepseek_client()
    
    if not client:
        # Mocking the process for demonstration if no key is provided
        print("\n[DEMO MODE] No API Key provided. Generating Mock Labels...")
        print("In a real scenario, DeepSeek would analyze each review.")
        
        # Simple heuristic for mock labels
        df['label'] = df['extract'].apply(lambda x: 'Fake' if len(str(x)) < 30 or 'great' in str(x).lower() else 'Real')
        df['reasoning'] = "Mock reasoning based on length/keywords."
    else:
        print("Starting annotation with DeepSeek...")
        labels = []
        reasonings = []
        
        for index, row in df.iterrows():
            print(f"Annotating review {index + 1}/{len(df)}...")
            result = annotate_review(client, row['extract'], row['score'], row['product'])
            labels.append(result.get('label', 'Unknown'))
            reasonings.append(result.get('reasoning', 'No reasoning'))
            time.sleep(0.5) # Rate limiting
            
        df['label'] = labels
        df['reasoning'] = reasonings

    df.to_csv(output_file, index=False)
    print(f"\nAnnotation complete. Saved to {output_file}")
    print(df[['extract', 'label', 'reasoning']].head())

if __name__ == "__main__":
    main()
