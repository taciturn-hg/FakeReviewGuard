document.addEventListener('DOMContentLoaded', () => {
    const analyzeBtn = document.getElementById('analyzeBtn');
    const reviewContent = document.getElementById('reviewContent');
    const resultCard = document.getElementById('resultCard');
    const resultIcon = document.getElementById('resultIcon');
    const resultLabel = document.getElementById('resultLabel');
    const confidenceBar = document.getElementById('confidenceBar');
    const analysisText = document.getElementById('analysisText');
    const sentimentBar = document.getElementById('sentimentBar');
    const sentimentLabel = document.getElementById('sentimentLabel');

    analyzeBtn.addEventListener('click', async () => {
        const content = reviewContent.value.trim();
        if (!content) {
            alert('请输入评论内容');
            return;
        }

        // Loading state
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>检测中...';
        resultCard.classList.add('d-none');

        try {
            const result = await ReviewAPI.analyzeComment(content);
            
            // Show result
            resultCard.classList.remove('d-none');
            
            // Update UI based on result
            // result structure based on main.py mock: { is_fake: bool, label: str, confidence: float, analysis: str }
            
            if (result.is_fake) {
                resultIcon.className = 'display-1 text-danger';
                resultIcon.innerHTML = '<i class="fas fa-exclamation-triangle"></i>';
                confidenceBar.className = 'progress-bar bg-danger';
            } else {
                resultIcon.className = 'display-1 text-success';
                resultIcon.innerHTML = '<i class="fas fa-check-circle"></i>';
                confidenceBar.className = 'progress-bar bg-success';
            }

            console.log("Analysis Result:", result); // Debug log

            resultLabel.textContent = result.label;
            
            const percent = Math.round(result.confidence * 100);
            confidenceBar.style.width = `${percent}%`;
            confidenceBar.textContent = `${percent}%`;
            
            // 更新情感倾向条
            // 注意：如果 score 为 0，result.sentiment_score || 0 也是 0，没问题
            // 但如果 result.sentiment_score 也是 0，我们要确保它能正确显示
            const score = (result.sentiment_score !== undefined) ? result.sentiment_score : 0;
            
            let left = 50;
            let width = 0;
            
            if (score > 0.2) {
                left = 50;
                width = score * 50; // 0~1 映射到 0~50%
                sentimentBar.className = 'progress-bar bg-success';
            } else if (score < -0.2) {
                width = Math.abs(score) * 50;
                left = 50 - width;
                sentimentBar.className = 'progress-bar bg-danger';
            } else {
                // 中性 (-0.2 ~ 0.2)
                if (score >= 0) {
                    left = 50;
                    width = score * 50;
                } else {
                    width = Math.abs(score) * 50;
                    left = 50 - width;
                }
                sentimentBar.className = 'progress-bar bg-warning';
            }
            
            sentimentBar.style.left = `${left}%`;
            sentimentBar.style.width = `${width}%`;
            sentimentLabel.textContent = score.toFixed(2);
            
            analysisText.textContent = result.analysis;

        } catch (error) {
            console.error('Analysis failed:', error);
            alert('检测失败，请稍后重试');
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<i class="fas fa-play me-2"></i>开始检测';
        }
    });
});