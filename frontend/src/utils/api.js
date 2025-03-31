// API 配置
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * 通用 API 請求函數
 * @param {string} endpoint - API 端點
 * @param {Object} options - 請求選項
 * @returns {Promise<any>} - 回傳 API 響應
 */
async function apiRequest(endpoint, options = {}) {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API 請求失敗: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API 請求錯誤 (${endpoint}):`, error);
    throw error;
  }
}

/**
 * 獲取可用的研討情境模組列表
 * @returns {Promise<Object>} - 情境模組數據
 */
export async function fetchScenarios() {
  return apiRequest('/api/scenarios');
}

/**
 * 開始新會議
 * @param {Object} config - 會議配置
 * @returns {Promise<Object>} - 會議創建結果
 */
export async function startConference(config) {
  return apiRequest('/api/conference/start', {
    method: 'POST',
    body: JSON.stringify(config),
  });
}

/**
 * 獲取會議信息
 * @param {string} conferenceId - 會議ID
 * @returns {Promise<Object>} - 會議信息
 */
export async function getConference(conferenceId) {
  return apiRequest(`/api/conference/${conferenceId}`);
}

/**
 * 獲取會議消息
 * @param {string} conferenceId - 會議ID
 * @param {number} limit - 消息數量限制
 * @param {number} offset - 消息偏移量
 * @returns {Promise<Object>} - 會議消息列表
 */
export async function getConferenceMessages(conferenceId, limit = 50, offset = 0) {
  return apiRequest(`/api/conference/${conferenceId}/messages?limit=${limit}&offset=${offset}`);
}

/**
 * 創建WebSocket連接
 * @param {string} conferenceId - 會議ID
 * @returns {WebSocket} - WebSocket連接實例
 */
export function createWebSocketConnection(conferenceId) {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsHost = API_BASE_URL.replace(/^https?:\/\//, '');
  const wsUrl = `${wsProtocol}//${wsHost}/ws/conference/${conferenceId}`;
  
  return new WebSocket(wsUrl);
}

/**
 * 測試API連接
 * @returns {Promise<Object>} - API測試結果
 */
export async function testApiConnection() {
  return apiRequest('/api/test');
}

/**
 * 發送測試消息
 * @param {string} message - 測試消息文本
 * @param {string} topic - 測試主題
 * @returns {Promise<Object>} - 測試結果
 */
export async function sendTestMessage(message, topic = "測試主題") {
  return apiRequest('/api/test/message', {
    method: 'POST',
    body: JSON.stringify({ message, topic }),
  });
}

/**
 * 更新OpenAI API密鑰
 * @param {string} apiKey - OpenAI API密鑰
 * @returns {Promise<Object>} - 更新結果
 */
export async function updateApiKey(apiKey) {
  return apiRequest('/api/update-api-key', {
    method: 'POST',
    body: JSON.stringify({ api_key: apiKey }),
  });
} 