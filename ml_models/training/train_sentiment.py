import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import classification_report, confusion_matrix, log_loss
from scipy.sparse import hstack
import joblib
import os
import sys

# 添加项目根目录到 sys.path 以便导入 shared 模块
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.utils.feature_extraction import jieba_tokenizer, get_sentiment_features
from shared.utils import logger

import time

def train_fake_review_detector():
    # Setup paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', '..', 'data', 'processed')
    models_dir = os.path.join(base_dir, '..', 'models')
    results_dir = os.path.join(base_dir, '..', 'evaluation')
    
    # Create directories if they don't exist
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(results_dir, exist_ok=True)

    input_file = os.path.join(data_dir, 'labeled_reviews.csv')
    
    if not os.path.exists(input_file):
        logger.error(f"未找到文件 {input_file}。请确保数据可用。")
        # Fallback to current directory for backward compatibility or testing
        if os.path.exists('labeled_reviews.csv'):
            input_file = 'labeled_reviews.csv'
            logger.info(f"在当前目录找到 {input_file}，正在使用它。")
        else:
            return

    logger.info(f"正在从 {input_file} 加载数据...")
    try:
        df = pd.read_csv(input_file)
    except Exception as e:
        logger.error(f"读取 CSV 错误: {e}")
        return

    logger.info(f"已加载 {len(df)} 条已标注评论。")
    
    # Check if we have both classes
    if 'label' not in df.columns:
        logger.error("错误: 数据中缺少 'label' 列。")
        return

    logger.info("标签分布:")
    print(df['label'].value_counts())
    
    if len(df['label'].unique()) < 2:
        logger.error("错误: 需要同时包含 'Real' 和 'Fake' 标签才能训练分类器。")
        return

    # Text Preprocessing (Simple)
    X = df['extract'].fillna('')
    y = df['label']

    # Split (stratified to preserve label distribution)
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    # Feature Extraction (TF-IDF with Jieba)
    logger.info("正在提取 TF-IDF 特征 (使用 Jieba)...")
    # Note: explicit tokenizer overrides stop_words, but we can filter inside tokenizer if needed.
    # Here we rely on TF-IDF to filter rare words.
    vectorizer = TfidfVectorizer(tokenizer=jieba_tokenizer, max_features=5000, token_pattern=None)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    # Feature Extraction (Sentiment)
    logger.info("正在提取情感特征 (使用 SnowNLP)...")
    X_train_sent = np.array([get_sentiment_features(t) for t in X_train])
    X_test_sent = np.array([get_sentiment_features(t) for t in X_test])

    # Combine Features
    logger.info("正在组合特征...")
    X_train_final = hstack([X_train_tfidf, X_train_sent])
    X_test_final = hstack([X_test_tfidf, X_test_sent])

    # Model Training with Loss Tracking
    logger.info("正在使用 SGD 训练模型 (监控损失)...")
    # SGDClassifier with loss='log_loss' is equivalent to Logistic Regression solved via SGD
    model = SGDClassifier(loss='log_loss', max_iter=1, warm_start=True, random_state=42, learning_rate='optimal')
    
    train_losses = []
    val_losses = []
    classes = np.unique(y)
    
    epochs = 50
    for epoch in range(epochs):
        model.partial_fit(X_train_final, y_train, classes=classes)
        
        # Calculate training loss
        y_train_prob = model.predict_proba(X_train_final)
        train_loss = log_loss(y_train, y_train_prob, labels=classes)
        train_losses.append(train_loss)
        
        # Calculate validation loss
        y_test_prob = model.predict_proba(X_test_final)
        val_loss = log_loss(y_test, y_test_prob, labels=classes)
        val_losses.append(val_loss)
        
        if (epoch + 1) % 5 == 0:
            logger.info(f"轮次 {epoch+1}/{epochs} - 训练损失: {train_loss:.4f} - 验证损失: {val_loss:.4f}")

    # Plot Loss Curve
    plt.figure(figsize=(10, 6))
    plt.plot(train_losses, label='Training Loss')
    plt.plot(val_losses, label='Validation Loss')
    plt.xlabel('Epochs')
    plt.ylabel('Log Loss')
    plt.title('Training and Validation Loss Curve')
    plt.legend()
    plt.grid(True)
    
    loss_curve_path = os.path.join(results_dir, 'loss_curve.png')
    plt.savefig(loss_curve_path)
    plt.close()
    logger.info(f"损失曲线已保存至 {loss_curve_path}")

    # Evaluation
    logger.info("正在评估模型...")
    y_pred = model.predict(X_test_final)
    
    logger.info("分类报告:")
    print(classification_report(y_test, y_pred))
    
    logger.info("混淆矩阵:")
    print(confusion_matrix(y_test, y_pred))

    # Save Model with Timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    model_filename = f'fake_review_model_{timestamp}.pkl'
    vectorizer_filename = f'tfidf_vectorizer_{timestamp}.pkl'
    
    model_path = os.path.join(models_dir, model_filename)
    vectorizer_path = os.path.join(models_dir, vectorizer_filename)
    
    # Also save as 'latest' for easy loading
    latest_model_path = os.path.join(models_dir, 'fake_review_model_latest.pkl')
    latest_vectorizer_path = os.path.join(models_dir, 'tfidf_vectorizer_latest.pkl')
    
    joblib.dump(model, model_path)
    joblib.dump(vectorizer, vectorizer_path)
    
    joblib.dump(model, latest_model_path)
    joblib.dump(vectorizer, latest_vectorizer_path)
    
    logger.info(f"模型已保存至 {model_path}")
    logger.info(f"向量化器已保存至 {vectorizer_path}")
    logger.info(f"最新模型也已保存至 {latest_model_path}")

    # Clean up old models (keep only last 3 timestamped versions)
    # Filter for timestamped model files (e.g., fake_review_model_20240101_120000.pkl)
    # Excluding 'latest' and potentially other files
    try:
        model_files = []
        for f in os.listdir(models_dir):
            if f.startswith('fake_review_model_') and f.endswith('.pkl') and 'latest' not in f:
                model_files.append(os.path.join(models_dir, f))
        
        # Sort by modification time (oldest first)
        model_files.sort(key=os.path.getmtime)
        
        # If more than 3, delete the oldest ones
        max_models = 3
        if len(model_files) > max_models:
            files_to_delete = model_files[:-max_models]
            logger.info(f"发现超过 {max_models} 个历史模型，正在清理旧模型...")
            for f_path in files_to_delete:
                try:
                    os.remove(f_path)
                    logger.info(f"已删除旧模型文件: {f_path}")
                    
                    # Also try to delete corresponding vectorizer
                    # Assuming naming convention: fake_review_model_TIMESTAMP.pkl -> tfidf_vectorizer_TIMESTAMP.pkl
                    base_name = os.path.basename(f_path)
                    timestamp_part = base_name.replace('fake_review_model_', '').replace('.pkl', '')
                    vec_name = f'tfidf_vectorizer_{timestamp_part}.pkl'
                    vec_path = os.path.join(models_dir, vec_name)
                    
                    if os.path.exists(vec_path):
                        os.remove(vec_path)
                        logger.info(f"已删除旧向量化器文件: {vec_path}")
                        
                except Exception as e:
                    logger.warning(f"删除文件 {f_path} 失败: {e}")
            logger.info("旧模型清理完成。")
            
    except Exception as e:
        logger.warning(f"清理旧模型时发生错误: {e}")

    # Inference Example
    logger.info("--- 推理测试 (中文) ---")
    test_review = "这个手机真是太好用了！我买了10个。强烈推荐！"
    
    # Process single sample
    vec_tfidf = vectorizer.transform([test_review])
    vec_sent = np.array([get_sentiment_features(test_review)])
    vec_final = hstack([vec_tfidf, vec_sent])
    
    prediction = model.predict(vec_final)[0]
    logger.info(f"评论: {test_review}")
    logger.info(f"预测结果: {prediction}")

if __name__ == "__main__":
    train_fake_review_detector()
