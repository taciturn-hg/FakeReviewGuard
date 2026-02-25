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
    const specSelect = document.getElementById('dashboardSpecSelect'); // 新增规格选择器

    // Chart Instances
    let sentimentChart = null;
    let qualityChart = null;
    let scoreChart = null;
    let lastData = null;
    let currentSpecsData = []; // 存储当前的规格数据列表

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
            
            // 关键：先显示区域，确保 ECharts 初始化时能获取容器尺寸
            productInfo.classList.remove('d-none');
            chartsArea.classList.remove('d-none');
            noDataAlert.classList.add('d-none');
            
            renderDashboard(data);
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

    // 初始化规格下拉框
    function initSpecDropdown(specs) {
        if (!specSelect) return;

        specSelect.innerHTML = '<option value="all" selected>全部规格</option>';
        if (specs && specs.length > 0) {
            specs.forEach(spec => {
                const option = document.createElement('option');
                option.value = spec.product_spec;
                // 截断过长的规格名称
                const displayName = spec.product_spec.length > 25
                    ? spec.product_spec.substring(0, 25) + '...'
                    : spec.product_spec;
                option.textContent = displayName;
                specSelect.appendChild(option);
            });
            specSelect.disabled = false;
            specSelect.value = 'all'; // 重置为全部
        } else {
            specSelect.disabled = true;
        }
    }

    // 3. 渲染大屏 (入口)
    function renderDashboard(data) {
        if (!data) return;
        lastData = data; // 保存原始数据
        currentSpecsData = data.specs || []; // 保存规格数据

        // 使用统一的初始化函数填充规格下拉框
        initSpecDropdown(currentSpecsData);

        const theme = getThemeConfig();
        renderDashboardWithConfig(data, theme);
    }

    // 监听规格选择变化
    if (specSelect) {
        specSelect.addEventListener('change', (e) => {
            const selectedSpec = e.target.value;
            const theme = getThemeConfig();
            
            if (selectedSpec === 'all') {
                // 恢复总体数据
                if (lastData) {
                    renderDashboardWithConfig(lastData, theme);
                }
            } else {
                // 查找对应规格的数据
                const specData = currentSpecsData.find(s => s.product_spec === selectedSpec);
                if (specData) {
                    // 合并基本信息，因为 specData 可能缺少部分总体信息（如 product_name）
                    // 但根据后端逻辑，specData 应该包含所有必要字段
                    renderDashboardWithConfig(specData, theme);
                } else {
                    console.warn('未找到对应规格的大屏统计数据:', selectedSpec, currentSpecsData);
                    alert('未找到该规格的大屏统计数据，已恢复为总体数据。');
                    if (lastData) {
                        renderDashboardWithConfig(lastData, theme);
                    }
                    // 重置下拉框为全部规格
                    specSelect.value = 'all';
                }
            }
        });
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

        // 准备数据
        const totalSentiment = (data.positive_count || 0) + (data.neutral_count || 0) + (data.negative_count || 0);
        const sentimentData = totalSentiment > 0 
            ? [
                { value: data.positive_count, name: '好评', itemStyle: { color: '#28a745' } },
                { value: data.neutral_count, name: '中评', itemStyle: { color: '#ffc107' } },
                { value: data.negative_count, name: '差评', itemStyle: { color: '#dc3545' } }
            ]
            : [{ value: 0, name: '无数据', itemStyle: { color: '#eee' }, label: { show: true, position: 'center', formatter: '无数据', fontSize: 20, color: '#999' } }];

        const sentimentOption = {
            backgroundColor: 'transparent',
            animation: true,
            animationDuration: 1000,
            animationEasing: 'cubicOut',
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
        };

        // 准备质量数据
        const totalQuality = data.real_count + data.fake_count;
        const qualityData = totalQuality > 0
            ? [
                { value: data.real_count, name: '真实评论', itemStyle: { color: '#238636' } },
                { value: data.fake_count, name: '疑似虚假', itemStyle: { color: '#da3633' } }
            ]
            : [{ value: 0, name: '无数据', itemStyle: { color: theme.borderColor }, label: { show: true, position: 'center', formatter: '无数据', fontSize: 20, color: theme.textColor } }];

        const qualityOption = {
            backgroundColor: 'transparent',
            animation: true,
            animationDuration: 1000,
            animationEasing: 'cubicOut',
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
        };

        const scoreOption = {
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
        };

        const renderCharts = () => {
            const sentimentEl = document.getElementById('sentimentChart');
            const qualityEl = document.getElementById('qualityChart');
            const scoreEl = document.getElementById('scoreChart');
            if (!sentimentEl || !qualityEl || !scoreEl) return;

            // 初始化图表 (仅在首次初始化)
            if (!sentimentChart) sentimentChart = echarts.init(sentimentEl);
            if (!qualityChart) qualityChart = echarts.init(qualityEl);
            if (!scoreChart) scoreChart = echarts.init(scoreEl);

            // 先 resize 再 setOption，避免首次布局未稳定导致动画跳过
            sentimentChart.resize();
            qualityChart.resize();
            scoreChart.resize();

            sentimentChart.setOption(sentimentOption, true);
            qualityChart.setOption(qualityOption, true);
            scoreChart.setOption(scoreOption, true);
        };

        // 等两帧，确保 remove('d-none') 后容器尺寸稳定再渲染
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                renderCharts();
            });
        });
    }

    // 窗口缩放适配
    window.addEventListener('resize', () => {
        sentimentChart && sentimentChart.resize();
        qualityChart && qualityChart.resize();
        scoreChart && scoreChart.resize();
    });
});