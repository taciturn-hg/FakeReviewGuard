from ml_models.inference.predict import FakeReviewPredictor
import json

predictor = FakeReviewPredictor()

# 1. 准备数据列表（而不是一段长文本）
reviews = [
    {"id": 101, "text": "这东西太棒了，非常好用，推荐大家购买！"},
    {"id": 102, "text": "刚收到货，包装破损，差评。"},
    {"id": 103, "text": "加微信号 abcd 返现 5 元。"}
]

results = []

print("--- 开始批量分析 ---")
for item in reviews:
    # 2. 对每条评论单独调用 predict
    prediction = predictor.predict(item["text"])
    
    # 3. 组合结果
    result_entry = {
        "id": item["id"],
        "text": item["text"],
        "label": prediction["label"],
        "is_fake": prediction["is_fake"],
        "confidence": prediction["confidence"],
        "sentiment_score": prediction["sentiment_score"]
    }
    results.append(result_entry)

# 4. 输出 JSON
print(json.dumps(results, indent=4, ensure_ascii=False))