// 1. 系统概览饼图 - 整体评论质量分布
const overviewChart = echarts.init(document.getElementById('overview'));
const option = {
  title: { text: '平台评论质量概览' },
  tooltip: { trigger: 'item' },
  legend: { orient: 'vertical', left: 'left' },
  series: [{
    name: '评论类型',
    type: 'pie',
    radius: '50%',
    data: [
      { value: 78, name: '真实评论' },
      { value: 22, name: '疑似虚假' }
    ]
  }]
};

// 2. 实时检测趋势折线图
const trendChart = echarts.init(document.getElementById('trend'));
const trendOption = {
  title: { text: '近7天检测趋势' },
  xAxis: { type: 'category', data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'] },
  yAxis: { type: 'value' },
  series: [{
    name: '检测数量',
    type: 'line',
    data: [120, 132, 101, 134, 90, 230, 210],
    smooth: true
  }]
};