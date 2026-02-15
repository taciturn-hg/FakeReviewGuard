document.addEventListener('DOMContentLoaded', () => {
    // UI Elements
    const searchInput = document.getElementById('productSearch');
    const searchResults = document.getElementById('searchResults');
    const productInfo = document.getElementById('productInfo');
    const chartsArea = document.getElementById('chartsArea');
    const noDataAlert = document.getElementById('noDataAlert');
    
    // Info Elements
    const infoProductName = document.getElementById('infoProductName');
    const infoDate = document.getElementById('infoDate');
    const infoProductUrl = document.getElementById('infoProductUrl');
    const trustScoreEl = document.getElementById('trustScore');

    // Chart Instances
    let sentimentChart = null;
    let qualityChart = null;
    let scoreChart = null;
    let lastData = null;

    // 获取当前主题配置
    const getThemeConfig = () => {
        const styles = getComputedStyle(document.documentElement);
        return {
            textColor: styles.getPropertyValue('--text-main').trim(),
            cardBg: styles.getPropertyValue('--bg-card').trim(),
            borderColor: styles.getPropertyValue('--border-color').trim(),
            chartTooltipBg: styles.getPropertyValue('--chart-tooltip-bg').trim(),
            chartTooltipText: styles.getPropertyValue('--chart-tooltip-text').trim()
        };
    };

    // 1. 搜索建议逻辑 (Debounce)
    let debounceTimer;
    searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimer);
        const keyword = e.target.value.trim();
        
        if (!keyword) {
            searchResults.classList.add('d-none');
            return;
        }

        debounceTimer = setTimeout(async () => {
            try {
                const response = await fetch(`/api/v1/stats/search?keyword=${encodeURIComponent(keyword)}`);
                const data = await response.json();
                
                searchResults.innerHTML = '';
                if (data.length > 0) {
                    data.forEach(item => {
                        const a = document.createElement('a');
                        a.className = 'list-group-item list-group-item-action';
                        a.href = '#';
                        a.innerHTML = `
                            <div class="d-flex w-100 justify-content-between">
                                <h6 class="mb-1 text-truncate">${item.name}</h6>
                                <small class="text-muted">${item.date.split(' ')[0]}</small>
                            </div>
                        `;
                        a.onclick = (ev) => {
                            ev.preventDefault();
                            loadProductStats(item.id);
                            searchResults.classList.add('d-none');
                            searchInput.value = item.name;
                        };
                        searchResults.appendChild(a);
                    });
                    searchResults.classList.remove('d-none');
                } else {
                    searchResults.innerHTML = '<div class="list-group-item text-muted">无相关记录</div>';
                    searchResults.classList.remove('d-none');
                }
            } catch (err) {
                console.error('Search failed:', err);
            }
        }, 300);
    });

    // 点击外部关闭搜索建议
    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.classList.add('d-none');
        }
    });

    // 2. 加载商品详细统计
    async function loadProductStats(statsId) {
        try {
            const response = await fetch(`/api/v1/stats/detail/${statsId}`);
            if (!response.ok) throw new Error('Failed to load details');
            
            const data = await response.json();
            lastData = data;
            renderDashboard(data);
            
            productInfo.classList.remove('d-none');
            chartsArea.classList.remove('d-none');
            noDataAlert.classList.add('d-none');
        } catch (err) {
            console.error(err);
            productInfo.classList.add('d-none');
            chartsArea.classList.add('d-none');
            noDataAlert.classList.remove('d-none');
        }
    }

    // 监听主题切换
    window.addEventListener('themeChanged', () => {
        if (!lastData) return;

        // 立即获取最新的主题配置
        const theme = getThemeConfig();
        
        // 立即应用新配置，移除过渡动画，消除"慢一拍"的感觉
        renderDashboardWithConfig(lastData, theme);
    });

    // 3. 渲染大屏 (入口)
    function renderDashboard(data) {
        if (!data) return;
        const theme = getThemeConfig();
        renderDashboardWithConfig(data, theme);
    }

    // 内部渲染函数，接受特定的主题配置
    function renderDashboardWithConfig(data, theme) {
        // 更新基本信息
        infoProductName.textContent = data.product_name;
        infoDate.textContent = data.created_at;
        if (data.product_url) {
            infoProductUrl.href = data.product_url;
            infoProductUrl.textContent = data.product_url;
        } else {
            infoProductUrl.textContent = '暂无链接';
            infoProductUrl.removeAttribute('href');
        }
        trustScoreEl.textContent = data.trust_score;

        // 初始化图表
        if (!sentimentChart) sentimentChart = echarts.init(document.getElementById('sentimentChart'));
        if (!qualityChart) qualityChart = echarts.init(document.getElementById('qualityChart'));
        if (!scoreChart) scoreChart = echarts.init(document.getElementById('scoreChart'));

        // 关键修复：确保图表容器有正确的大小后再 resize
        setTimeout(() => {
            sentimentChart.resize();
            qualityChart.resize();
            scoreChart.resize();
        }, 0);

        // 准备数据
        const totalSentiment = (data.positive_count || 0) + (data.neutral_count || 0) + (data.negative_count || 0);
        const sentimentData = totalSentiment > 0 
            ? [
                { value: data.positive_count, name: '好评', itemStyle: { color: '#28a745' } },
                { value: data.neutral_count, name: '中评', itemStyle: { color: '#ffc107' } },
                { value: data.negative_count, name: '差评', itemStyle: { color: '#dc3545' } }
            ]
            : [{ value: 0, name: '无数据', itemStyle: { color: '#eee' }, label: { show: true, position: 'center', formatter: '无数据', fontSize: 20, color: '#999' } }];

        // 图表 1: 评论情绪分布 (Pie)
        sentimentChart.setOption({
            backgroundColor: 'transparent',
            tooltip: { 
                trigger: 'item',
                backgroundColor: theme.chartTooltipBg,
                textStyle: { color: theme.chartTooltipText }
            },
            legend: { 
                bottom: 0,
                textStyle: { color: theme.textColor },
                show: totalSentiment > 0 
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'],
                avoidLabelOverlap: false,
                startAngle: 90, // 起始角度
                clockwise: false, // 逆时针
                itemStyle: { borderRadius: 5, borderColor: theme.cardBg, borderWidth: 2 },
                label: { show: false },
                data: sentimentData
            }]
        });

        // 准备质量数据
        const totalQuality = data.real_count + data.fake_count;
        const qualityData = totalQuality > 0
            ? [
                { value: data.real_count, name: '真实评论', itemStyle: { color: '#238636' } },
                { value: data.fake_count, name: '疑似虚假', itemStyle: { color: '#da3633' } }
            ]
            : [{ value: 0, name: '无数据', itemStyle: { color: theme.borderColor }, label: { show: true, position: 'center', formatter: '无数据', fontSize: 20, color: theme.textColor } }];

        // 图表 2: 评论质量分布 (Pie)
        qualityChart.setOption({
            backgroundColor: 'transparent',
            tooltip: { 
                trigger: 'item',
                backgroundColor: theme.chartTooltipBg,
                textStyle: { color: theme.chartTooltipText }
            },
            legend: { 
                bottom: 0,
                textStyle: { color: theme.textColor },
                show: totalQuality > 0
            },
            series: [{
                type: 'pie',
                radius: ['40%', '70%'], // 统一风格为环形
                avoidLabelOverlap: false,
                startAngle: 90, // 起始角度
                clockwise: false, // 逆时针
                itemStyle: { borderRadius: 5, borderColor: theme.cardBg, borderWidth: 2 },
                label: { show: false },
                data: qualityData
            }]
        });

        // 图表 3: 平均情感分数 (Gauge)
        scoreChart.setOption({
            backgroundColor: 'transparent',
            series: [{
                type: 'gauge',
                min: -1,
                max: 1,
                axisLine: {
                    lineStyle: {
                        width: 15,
                        // 修改颜色区间：[-1, -0.2] 红, [-0.2, 0.2] 黄, [0.2, 1] 绿
                        color: [[0.4, '#da3633'], [0.6, '#d29922'], [1, '#238636']]
                    }
                },
                pointer: { itemStyle: { color: 'auto' } },
                axisTick: { distance: -15, length: 8, lineStyle: { color: theme.borderColor, width: 2 } },
                splitLine: { distance: -15, length: 15, lineStyle: { color: theme.cardBg, width: 4 } },
                axisLabel: { color: theme.textColor, distance: 20, fontSize: 12 },
                detail: {
                    valueAnimation: true,
                    formatter: '{value}',
                    color: theme.textColor,
                    fontSize: 20
                },
                data: [{ value: data.sentiment_score, name: '情感得分', title: { color: theme.textColor } }]
            }]
        });
    }

    // 窗口缩放适配
    window.addEventListener('resize', () => {
        sentimentChart && sentimentChart.resize();
        qualityChart && qualityChart.resize();
        scoreChart && scoreChart.resize();
    });
});