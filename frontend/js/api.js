// js/api.js
class ReviewAPI {
    static async analyzeComment(content) {
        const response = await fetch('/api/v1/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content })
        });
        return response.json();
    }
    
    // --- 新增：异步任务相关接口 ---
    
    // 辅助方法：处理响应
    static async _handleResponse(response) {
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            const data = await response.json();
            if (!response.ok) {
                // 如果是 JSON 格式的错误响应，抛出包含 detail 的错误
                throw new Error(data.detail || data.message || '请求失败');
            }
            return data;
        } else {
            // 如果不是 JSON (比如 500 Internal Server Error 的纯文本)
            const text = await response.text();
            console.error("API Error (Non-JSON):", text);
            throw new Error(`服务器错误: ${response.status} ${response.statusText}`);
        }
    }

    // 1. 启动任务
    static async startTask(productUrl, forceRestart = false) {
        const response = await fetch('/api/v1/task/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                product_url: productUrl,
                force_restart: forceRestart
            })
        });
        return this._handleResponse(response);
    }

    // 2. 检查状态
    static async checkStatus(taskId) {
        const response = await fetch(`/api/v1/task/status/${taskId}`);
        return this._handleResponse(response);
    }

    // 3. 获取结果
    static async getTaskResult(taskId) {
        const response = await fetch(`/api/v1/task/result/${taskId}`);
        return this._handleResponse(response);
    }
    
    // 4. 恢复任务 (已登录)
    static async resumeCrawler(taskId) {
        const response = await fetch(`/api/v1/task/resume/${taskId}`, {
            method: 'POST'
        });
        return this._handleResponse(response);
    }
    
    // 5. 停止任务
    static async stopCrawler(taskId) {
        const response = await fetch(`/api/v1/task/stop/${taskId}`, {
            method: 'POST'
        });
        return this._handleResponse(response);
    }
    
    static async getStats(productId, chartType = 'all') {
        const response = await fetch(`/api/v1/stats?product_id=${productId}&chart_type=${chartType}`);
        return response.json();
    }

    // --- 新增：颜色工具 ---
    static ColorUtils = {
        parseColor: (color) => {
            // Check for hex
            if (color.startsWith('#')) {
                const hex = color.substring(1);
                const r = parseInt(hex.substring(0, 2), 16);
                const g = parseInt(hex.substring(2, 4), 16);
                const b = parseInt(hex.substring(4, 6), 16);
                return { r, g, b };
            }
            // Check for rgb
            const match = color.match(/^rgb\((\d+),\s*(\d+),\s*(\d+)\)$/);
            if (match) {
                return { r: parseInt(match[1]), g: parseInt(match[2]), b: parseInt(match[3]) };
            }
            // Check for rgba (ignore alpha for now)
            const rgbaMatch = color.match(/^rgba\((\d+),\s*(\d+),\s*(\d+),\s*([\d.]+)\)$/);
            if (rgbaMatch) {
                return { r: parseInt(rgbaMatch[1]), g: parseInt(rgbaMatch[2]), b: parseInt(rgbaMatch[3]) };
            }
            return { r: 0, g: 0, b: 0 };
        }
    };
}