import jieba
from snownlp import SnowNLP

def jieba_tokenizer(text):
    """
    使用结巴分词对文本进行分词
    """
    # 限制文本长度，防止过长文本导致性能问题
    text = str(text)[:1000]
    return jieba.lcut(text)

def get_sentiment_features(text):
    """
    使用 SnowNLP 提取情感特征 (针对中文文本)
    Returns [sentiment_score]
    """
    try:
        # 限制文本长度
        text = str(text)[:1000]
        s = SnowNLP(text)
        return [s.sentiments]
    except Exception:
        # 针对空文本或无效文本的回退处理
        return [0.5]
