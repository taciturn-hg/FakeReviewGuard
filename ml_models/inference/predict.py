import os
import sys
import joblib
import numpy as np
from scipy.sparse import hstack

# 添加项目根目录到 sys.path 以便导入 shared 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.utils.feature_extraction import jieba_tokenizer, get_sentiment_features
from shared.utils import logger

# 修复 joblib 加载时的 pickle 路径问题
# 训练时 jieba_tokenizer 可能被保存为 __main__.jieba_tokenizer
# 这里将其注入到 __main__ 命名空间中
if __name__ != "__main__":
    import sys
    import shared.utils.feature_extraction
    sys.modules['__main__'].jieba_tokenizer = shared.utils.feature_extraction.jieba_tokenizer

class FakeReviewPredictor:
    def __init__(self, model_dir=None):
        if model_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(base_dir, '..', 'models')
        
        # 尝试加载最新模型 (latest)，如果不存在则加载默认模型
        model_path_latest = os.path.join(model_dir, 'fake_review_model_latest.pkl')
        vec_path_latest = os.path.join(model_dir, 'tfidf_vectorizer_latest.pkl')
        
        model_path_default = os.path.join(model_dir, 'fake_review_model.pkl')
        vec_path_default = os.path.join(model_dir, 'tfidf_vectorizer.pkl')

        if os.path.exists(model_path_latest) and os.path.exists(vec_path_latest):
            logger.info(f"Loading latest model from {model_path_latest}...")
            try:
                self.model = joblib.load(model_path_latest)
                self.vectorizer = joblib.load(vec_path_latest)
            except Exception as e:
                logger.error(f"Failed to load latest model or vectorizer from '{model_dir}': {e}")
                raise RuntimeError(f"Failed to load latest fake review model from '{model_dir}'. "
                                   f"Please verify the model files are not corrupted and are compatible.") from e
        elif os.path.exists(model_path_default) and os.path.exists(vec_path_default):
            logger.info(f"Loading default model from {model_path_default}...")
            try:
                self.model = joblib.load(model_path_default)
                self.vectorizer = joblib.load(vec_path_default)
            except Exception as e:
                logger.error(f"Failed to load default model or vectorizer from '{model_dir}': {e}")
                raise RuntimeError(f"Failed to load default fake review model from '{model_dir}'. "
                                   f"Please verify the model files are not corrupted and are compatible.") from e
        else:
            raise FileNotFoundError(f"No model found in {model_dir}. Please run training first.")

        # Validate loaded objects to ensure they provide expected methods
        if not hasattr(self.model, "predict"):
            logger.error("Loaded model object is missing required 'predict' method.")
            raise TypeError("Loaded fake review model is incompatible: missing 'predict' method.")

        if not hasattr(self.vectorizer, "transform"):
            logger.error("Loaded vectorizer object is missing required 'transform' method.")
            raise TypeError("Loaded TF-IDF vectorizer is incompatible: missing 'transform' method.")
    def predict(self, text):
        """
        分析单条评论
        Returns:
            # dict: {
            #     "text": str,
            #     "is_fake": bool,
            #     "confidence": float,
            #     "label": str,
            #     "sentiment_score": float
            # }
        """
        if not text:
            return {"error": "Empty text"}

        # 1. 特征提取
        # TF-IDF
        vec_tfidf = self.vectorizer.transform([text])
        
        # 情感特征
        sentiment_score = get_sentiment_features(text)[0]
        vec_sent = np.array([[sentiment_score]])
        
        # 组合特征
        vec_final = hstack([vec_tfidf, vec_sent])
        
        # 2. 预测
        # 获取预测概率 (假设模型支持 predict_proba)
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(vec_final)[0]
            # 假设 classes_ 是 ['Fake', 'Real'] 或类似的排序，需要确认
            # 通常 SGDClassifier(loss='log_loss') 输出概率
            # 找到预测类别的索引
            pred_label = self.model.predict(vec_final)[0]
            confidence = np.max(probs)
        else:
            # 如果模型不支持概率 (如 SVM hinge loss)，只有 label
            pred_label = self.model.predict(vec_final)[0]
            confidence = 1.0 # 无法获取置信度

        is_fake = (pred_label == 'Fake')
        
        # 返回基础分析数据，具体API格式由后端处理
        return {
            "text": text,
            "label": str(pred_label),
            "is_fake": bool(is_fake),
            "confidence": round(confidence, 4),
            "sentiment_score": round(sentiment_score, 4)
        }

if __name__ == "__main__":
    # 使用示例
    try:
        predictor = FakeReviewPredictor()
        
        test_reviews = [
            "这个手机真是太好用了！我买了10个。强烈推荐！",
            "屏幕分辨率很高，运行速度快，电池也很耐用，非常满意的一次购物。",
            "垃圾手机，开机就发烫，退货！",
            "好评返现5元，截图给客服。"
        ]
        
        logger.info("\n--- 评论分析结果 ---")
        for review in test_reviews:
            result = predictor.predict(review)
            logger.info(f"Data: {result}")
            
    except Exception as e:
        logger.error(f"Error: {e}")
