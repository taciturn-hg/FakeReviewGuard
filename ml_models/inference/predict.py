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

from shared.utils.feature_extraction import get_sentiment_features, jieba_tokenizer
from shared.utils import logger

# 修复 joblib 加载时的 pickle 路径问题
# 训练时 jieba_tokenizer 可能被保存为 __main__.jieba_tokenizer
# 这里将其注入到 __main__ 命名空间中
try:
    # 如果 __main__ 中没有 jieba_tokenizer，则注入
    if not hasattr(sys.modules['__main__'], 'jieba_tokenizer'):
        sys.modules['__main__'].jieba_tokenizer = jieba_tokenizer
except Exception as e:
    logger.warning(f"无法将 jieba_tokenizer 注入到 __main__: {e}")

class FakeReviewPredictor:
    def __init__(self, model_dir=None):
        if model_dir is None:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            model_dir = os.path.join(base_dir, '..', 'models')
        
        self.model_dir = model_dir
        self._load_model()

    def _load_model(self):
        """
        加载模型和向量化器，优先加载最新模型 (latest)，失败则回退到默认模型
        """
        # 尝试加载最新模型 (latest)，如果不存在则加载默认模型
        model_path_latest = os.path.join(self.model_dir, 'fake_review_model_latest.pkl')
        vec_path_latest = os.path.join(self.model_dir, 'tfidf_vectorizer_latest.pkl')
        
        model_path_default = os.path.join(self.model_dir, 'fake_review_model.pkl')
        vec_path_default = os.path.join(self.model_dir, 'tfidf_vectorizer.pkl')

        # 避免使用 os.path.exists 造成 TOCTOU 问题，直接尝试加载
        try:
            logger.info(f"正在从 {model_path_latest} 加载最新模型...")
            self.model = joblib.load(model_path_latest)
            self.vectorizer = joblib.load(vec_path_latest)
        except Exception as latest_exc:
            logger.warning(
                f"无法从 {self.model_dir} 加载最新模型，回退到默认模型。原因: {latest_exc}"
            )
            try:
                logger.info(f"正在从 {model_path_default} 加载默认模型...")
                self.model = joblib.load(model_path_default)
                self.vectorizer = joblib.load(vec_path_default)
            except Exception as default_exc:
                logger.error(f"加载默认模型失败: {default_exc}")
                raise FileNotFoundError(
                    f"在 {self.model_dir} 中未找到模型。请先运行训练。"
                ) from default_exc

        # Validate loaded objects to ensure they provide expected methods
        if not hasattr(self.model, "predict"):
            logger.error("加载的模型对象缺少必要的 'predict' 方法。")
            raise TypeError("加载的虚假评论模型不兼容: 缺少 'predict' 方法。")

        if not hasattr(self.vectorizer, "transform"):
            logger.error("加载的向量化器对象缺少必要的 'transform' 方法。")
            raise TypeError("加载的 TF-IDF 向量化器不兼容: 缺少 'transform' 方法。")

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
            return {
                "text": text if text is not None else "",
                "label": "Unknown",
                "is_fake": False,
                "confidence": 0.0,
                "sentiment_score": 0.5,
                "error": "Empty text"
            }

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

def _run_self_tests(predictor: FakeReviewPredictor) -> None:
    """
    Basic self-tests for FakeReviewPredictor.predict to exercise common and edge-case inputs.

    This is not a replacement for a proper test suite, but it provides a minimal
    automated check when this module is executed as a script.
    """
    test_cases = {
        "normal_positive": "这个手机真是太好用了！我买了10个。强烈推荐！",
        "normal_negative": "垃圾手机，开机就发烫，退货！",
        "empty_string": "",
        "whitespace_only": "    ",
        "very_long_text": "很好用！" * 1000,
    }

    for name, text in test_cases.items():
        logger.info(f"[自检] 正在运行测试用例 '{name}'")
        result = predictor.predict(text)

        # Basic structural checks
        assert isinstance(result, dict), "predict() should return a dict"
        for key in ("text", "label", "is_fake", "confidence", "sentiment_score"):
            assert key in result, f"Missing key '{key}' in prediction result"

        assert isinstance(result["label"], str), "label should be a string"
        assert isinstance(result["is_fake"], bool), "is_fake should be a bool"
        assert isinstance(result["confidence"], float), "confidence should be a float"
        assert isinstance(result["sentiment_score"], float), "sentiment_score should be a float"

    logger.info("[自检] FakeReviewPredictor.predict() 所有基本检查通过。")


if __name__ == "__main__":
    # 使用示例和简单自检
    try:
        predictor = FakeReviewPredictor()

        # 运行简单自检用例，验证常见输入和边界情况
        _run_self_tests(predictor)

        # 手动示例
        test_reviews = [
            "这个手机真是太好用了！我买了10个。强烈推荐！",
            "屏幕分辨率很高，运行速度快，电池也很耐用，非常满意的一次购物。",
            "垃圾手机，开机就发烫，退货！",
            "好评返现5元，截图给客服。"
        ]

        logger.info("\n--- 评论分析结果 ---")
        for review in test_reviews:
            result = predictor.predict(review)
            logger.info(f"数据: {result}")
    except Exception as e:
        logger.error(f"错误: {e}")
