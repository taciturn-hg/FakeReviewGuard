document.addEventListener('DOMContentLoaded', () => {
    const searchBtn = document.getElementById('searchBtn');
    const productIdInput = document.getElementById('productIdInput');
    const productResult = document.getElementById('productResult');
    
    // UI Elements
    const trustScoreEl = document.getElementById('trustScore');
    const resProductIdEl = document.getElementById('resProductId');
    const totalReviewsEl = document.getElementById('totalReviews');
    const fakeRatioEl = document.getElementById('fakeRatio');
    const fakeCountEl = document.getElementById('fakeCount');
    const sentimentScoreEl = document.getElementById('sentimentScore');
    const productNameEl = document.getElementById('productName');
    const copyLinkBtn = document.getElementById('copyLinkBtn');
    let sentimentChartInstance = null;
    let lastResult = null;

    // 模态框元素
    const loginModalEl = document.getElementById('loginModal');
    const loginModal = new bootstrap.Modal(loginModalEl, { backdrop: 'static', keyboard: false });
    const existTaskModalEl = document.getElementById('existTaskModal');
    const existTaskModal = new bootstrap.Modal(existTaskModalEl, { backdrop: 'static', keyboard: false });
    const loggedInBtn = document.getElementById('loggedInBtn');
    const stopCrawlerBtn = document.getElementById('stopCrawlerBtn');
    const useExistingBtn = document.getElementById('useExistingBtn');
    const restartTaskBtn = document.getElementById('restartTaskBtn');
    let isWaitingForLogin = false;
    let pendingTaskId = null; // 用于存储待确认的任务ID
    let pendingProductUrl = null; // 用于存储待确认的商品链接

    // 绑定模态框按钮事件
    if (useExistingBtn) {
        useExistingBtn.addEventListener('click', async () => {
            if (!pendingTaskId) return;
            existTaskModal.hide();
            await fetchAndDisplayResult(pendingTaskId);
        });
    }

    if (restartTaskBtn) {
        restartTaskBtn.addEventListener('click', async () => {
            if (!pendingProductUrl) return;
            existTaskModal.hide();
            await startAnalysis(pendingProductUrl, true);
        });
    }

    if (loggedInBtn) {
        loggedInBtn.addEventListener('click', async () => {
            const taskId = parseInt(productResult.dataset.taskId);
            if (!taskId) return;
            
            try {
                loggedInBtn.disabled = true;
                loggedInBtn.textContent = '提交中...';
                
                await ReviewAPI.resumeCrawler(taskId);
                
                loginModal.hide();
                isWaitingForLogin = false;
                
                // 重置按钮状态
                loggedInBtn.disabled = false;
                loggedInBtn.textContent = '我已登录';
                
            } catch (error) {
                console.error("恢复任务失败:", error);
                alert("恢复任务失败，请稍后重试: " + error.message);
                loggedInBtn.disabled = false;
                loggedInBtn.textContent = '我已登录';
            }
        });
    }

    if (stopCrawlerBtn) {
        stopCrawlerBtn.addEventListener('click', async () => {
            const taskId = parseInt(productResult.dataset.taskId);
            if (!taskId) return;
            
            if (!confirm('确定要停止爬虫任务吗？')) {
                return;
            }

            try {
                stopCrawlerBtn.disabled = true;
                stopCrawlerBtn.textContent = '停止中...';
                
                await ReviewAPI.stopCrawler(taskId);
                
                loginModal.hide();
                isWaitingForLogin = false;
                
                // 重置按钮状态
                stopCrawlerBtn.disabled = false;
                stopCrawlerBtn.textContent = '停止爬虫';
                
            } catch (error) {
                console.error("停止任务失败:", error);
                alert("停止任务失败，请稍后重试: " + error.message);
                stopCrawlerBtn.disabled = false;
                stopCrawlerBtn.textContent = '停止爬虫';
            }
        });
    }

    // 获取当前主题配置
    const getThemeConfig = () => {
        const styles = getComputedStyle(document.documentElement);
        return {
            textColor: styles.getPropertyValue('--text-main').trim(),
            cardBg: styles.getPropertyValue('--bg-card').trim(),
            chartTooltipBg: styles.getPropertyValue('--chart-tooltip-bg').trim(),
            chartTooltipText: styles.getPropertyValue('--chart-tooltip-text').trim()
        };
    };

    // 复制链接功能
    const handleCopy = (text, element) => {
        if (!text) return;

        const copyToClipboard = (str) => {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(str);
            } else {
                // 兼容性方案
                let textArea = document.createElement("textarea");
                textArea.value = str;
                textArea.style.position = "fixed";
                textArea.style.left = "-9999px";
                textArea.style.top = "0";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                return new Promise((resolve, reject) => {
                    try {
                        const successful = document.execCommand('copy');
                        successful ? resolve() : reject(new Error('Copy failed'));
                    } catch (err) {
                        reject(err);
                    } finally {
                        document.body.removeChild(textArea);
                    }
                });
            }
        };

        copyToClipboard(text).then(() => {
            // 视觉反馈
            const originalContent = element.innerHTML;
            
            // 如果是按钮，改图标
            if (element.tagName === 'BUTTON') {
                element.innerHTML = '<i class="fas fa-check text-success"></i>';
            } 
            // 如果是徽章，改文字或加提示
            else {
                element.classList.remove('bg-secondary');
                element.classList.add('bg-success');
                const originalText = element.textContent;
                element.textContent = '已复制!';
                
                setTimeout(() => {
                    element.classList.remove('bg-success');
                    element.classList.add('bg-secondary');
                    element.textContent = originalText;
                }, 2000);
                return; // 徽章的逻辑单独处理恢复，直接返回
            }

            setTimeout(() => {
                element.innerHTML = originalContent;
            }, 2000);
        }).catch(err => {
            console.error('复制失败:', err);
            alert('复制失败，请手动复制');
        });
    };

    if (copyLinkBtn) {
        copyLinkBtn.addEventListener('click', () => {
            handleCopy(productIdInput.value.trim(), copyLinkBtn);
        });
    }
    
    if (resProductIdEl) {
        resProductIdEl.addEventListener('click', () => {
            handleCopy(productIdInput.value.trim(), resProductIdEl);
        });
    }

    // 初始化/更新 ECharts 饼图
    function renderSentimentChart(positive, negative, neutral) {
        const theme = getThemeConfig();
        renderSentimentChartWithConfig(positive, negative, neutral, theme);
    }

    // 内部渲染函数，接受特定的主题配置
    function renderSentimentChartWithConfig(positive, negative, neutral, theme) {
        const chartDom = document.getElementById('sentimentChart');
        if (!chartDom) return;
        
        if (sentimentChartInstance) {
            sentimentChartInstance.dispose();
        }
        
        sentimentChartInstance = echarts.init(chartDom);
        const option = {
            backgroundColor: 'transparent',
            tooltip: {
                trigger: 'item',
                backgroundColor: theme.chartTooltipBg,
                textStyle: { color: theme.chartTooltipText }
            },
            legend: {
                bottom: '0%',
                left: 'center',
                textStyle: { color: theme.textColor }
            },
            series: [
                {
                    name: '评论情感',
                    type: 'pie',
                    radius: ['40%', '70%'],
                    avoidLabelOverlap: false,
                    startAngle: 90, // 起始角度
                    clockwise: false, // 逆时针
                    itemStyle: {
                        borderRadius: 10,
                        borderColor: theme.cardBg,
                        borderWidth: 2
                    },
                    label: {
                        show: false,
                        position: 'center'
                    },
                    emphasis: {
                        label: {
                            show: true,
                            fontSize: 20,
                            fontWeight: 'bold',
                            color: theme.textColor
                        }
                    },
                    labelLine: {
                        show: false
                    },
                    data: [
                        { value: positive, name: '好评', itemStyle: { color: '#28a745' } }, // Success Green
                        { value: neutral, name: '中评', itemStyle: { color: '#d29922' } },  // Warning Yellow
                        { value: negative, name: '差评', itemStyle: { color: '#da3633' } }  // Danger Red
                    ]
                }
            ]
        };
        sentimentChartInstance.setOption(option);
        
        // 响应式调整
        window.addEventListener('resize', () => {
            sentimentChartInstance && sentimentChartInstance.resize();
        });
    }

    // 封装轮询逻辑
    async function pollTaskStatus(taskId) {
        let attempts = 0;
        const maxAttempts = 60; // 最多轮询 60 次 (约 2 分钟)
        
        return new Promise((resolve, reject) => {
            const interval = setInterval(async () => {
                attempts++;
                try {
                    const statusRes = await ReviewAPI.checkStatus(taskId);
                    
                    // 状态: 0-失败, 1-爬虫中, 2-分析中, 3-完成, 4-等待登录
                    if (statusRes.status === 0) {
                        clearInterval(interval);
                        reject(new Error(statusRes.message || '任务失败'));
                    } else if (statusRes.status === 3) {
                        clearInterval(interval);
                        resolve(statusRes);
                    } else if (statusRes.status === 4) {
                        searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>等待用户登录...';
                        if (!isWaitingForLogin) {
                            isWaitingForLogin = true;
                            productResult.dataset.taskId = taskId;
                            loginModal.show();
                        }
                    } else if (statusRes.status === 1) {
                        searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>正在抓取评论数据...';
                    } else if (statusRes.status === 2) {
                        searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>正在进行 AI 分析...';
                    }
                    
                    if (attempts >= maxAttempts) {
                        clearInterval(interval);
                        reject(new Error('任务超时'));
                    }
                } catch (err) {
                    clearInterval(interval);
                    reject(err);
                }
            }, 500); // 每 500 毫秒查一次
        });
    }

    // 监听主题切换
    window.addEventListener('themeChanged', () => {
        if (!lastResult) return;

        // 立即获取最新的主题配置
        const theme = getThemeConfig();
        
        // 立即应用新配置，移除过渡动画
        renderSentimentChartWithConfig(
            lastResult.positive_count, 
            lastResult.negative_count, 
            lastResult.neutral_count, 
            theme
        );
    });

    async function startAnalysis(productUrl, forceRestart = false) {
        searchBtn.disabled = true;
        searchBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>启动分析任务...';
        productResult.classList.add('d-none');

        try {
            // 1. 启动任务
            const startRes = await ReviewAPI.startTask(productUrl, forceRestart);
            
            // 检查是否已存在
            if (startRes.status === 'exists') {
                pendingTaskId = startRes.task_id;
                pendingProductUrl = productUrl;
                existTaskModal.show();
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>分析';
                return;
            }
            
            const taskId = startRes.task_id;
            console.log(`Task started: ${taskId}`);
            
            // 2. 轮询状态
            await pollTaskStatus(taskId);
            
            // 3. 获取并显示结果
            await fetchAndDisplayResult(taskId);
            
        } catch (error) {
            console.error('Analysis failed:', error);
            alert(`分析失败: ${error.message}`);
        } finally {
            if (!pendingTaskId) { // 如果不是等待确认状态，则恢复按钮
                searchBtn.disabled = false;
                searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>分析';
            }
        }
    }

    async function fetchAndDisplayResult(taskId) {
        try {
            const result = await ReviewAPI.getTaskResult(taskId);
            lastResult = result;
            
            // Show result
            productResult.classList.remove('d-none');
            productResult.dataset.taskId = taskId; // 保存当前任务ID
            
            // Update data
            trustScoreEl.textContent = result.trust_score;
            
            // 显示商品名称
            productNameEl.textContent = result.product_name || "未知商品";
            
            // 显示 URL (截断)
            const displayUrl = productIdInput.value.trim() || result.product_url || "";
            resProductIdEl.textContent = displayUrl.length > 30 ? displayUrl.substring(0, 30) + '...' : displayUrl;
            
            totalReviewsEl.textContent = result.total_reviews.toLocaleString();
            fakeCountEl.textContent = result.fake_count.toLocaleString();
            fakeRatioEl.textContent = `${(result.fake_ratio).toFixed(1)}%`;
            
            // Update Sentiment Score
            if (sentimentScoreEl) {
                const sentimentScore = result.sentiment_score !== undefined ? result.sentiment_score : 0;
                sentimentScoreEl.textContent = sentimentScore;
                
                if (sentimentScore > 0) {
                    sentimentScoreEl.className = 'fw-bold text-success';
                } else if (sentimentScore < 0) {
                    sentimentScoreEl.className = 'fw-bold text-danger';
                } else {
                    sentimentScoreEl.className = 'fw-bold text-secondary';
                }
            }

            // Update Trust Score Color
            if (result.trust_score >= 80) {
                trustScoreEl.className = 'fw-bold text-success';
            } else if (result.trust_score >= 60) {
                trustScoreEl.className = 'fw-bold text-warning';
            } else {
                trustScoreEl.className = 'fw-bold text-danger';
            }
            
            // 渲染图表
            renderSentimentChart(result.positive_count, result.negative_count, result.neutral_count);
            
        } catch (error) {
            console.error("获取结果失败:", error);
            alert("获取结果失败: " + error.message);
        } finally {
            searchBtn.disabled = false;
            searchBtn.innerHTML = '<i class="fas fa-search me-2"></i>分析';
        }
    }

    searchBtn.addEventListener('click', async () => {
        const productUrl = productIdInput.value.trim();
        if (!productUrl) {
            alert('请输入商品链接');
            return;
        }

        if (!productUrl.startsWith('http')) {
            alert('请输入有效的商品链接 (以 http 开头)');
            return;
        }

        await startAnalysis(productUrl);
    });
});