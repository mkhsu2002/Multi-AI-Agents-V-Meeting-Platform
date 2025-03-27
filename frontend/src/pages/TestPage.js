import React, { useState } from 'react';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TestPage = () => {
  const [message, setMessage] = useState('');
  const [topic, setTopic] = useState('美國關稅大戰');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResponse(null);
    
    try {
      console.log('正在送出測試請求...');
      const testData = {
        message: message,
        topic: topic
      };
      
      console.log('請求數據：', JSON.stringify(testData, null, 2));
      
      const response = await fetch(`${API_BASE_URL}/api/test/message`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testData),
      });
      
      const data = await response.json();
      console.log('收到回應：', data);
      
      if (!response.ok) {
        throw new Error(data.error || data.detail || '發送測試消息失敗');
      }
      
      setResponse(data);
    } catch (err) {
      console.error('測試時發生錯誤:', err);
      setError(err.message || '測試時發生錯誤');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold text-primary mb-6 text-center">API 測試頁面</h1>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block mb-2 font-medium">會議主題</label>
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              className="w-full p-3 border rounded-lg"
              placeholder="輸入會議主題..."
            />
          </div>
          
          <div>
            <label className="block mb-2 font-medium">測試訊息</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              className="w-full p-3 border rounded-lg h-32"
              placeholder="輸入想要發送給 ChatGPT 的訊息..."
            />
          </div>
          
          <div className="text-center">
            <button
              type="submit"
              disabled={loading || !message.trim()}
              className={`px-8 py-3 rounded-lg text-lg font-medium transition duration-200 ${
                loading || !message.trim() 
                  ? 'bg-gray-300 cursor-not-allowed' 
                  : 'bg-primary text-white hover:bg-opacity-90'
              }`}
            >
              {loading ? '發送中...' : '發送測試訊息'}
            </button>
          </div>
        </form>
        
        {error && (
          <div className="mt-6 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <p className="font-bold">錯誤</p>
            <p>{error}</p>
          </div>
        )}
        
        {response && (
          <div className="mt-6 bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded">
            <p className="font-bold">回應</p>
            <pre className="mt-2 whitespace-pre-wrap">
              {JSON.stringify(response, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

export default TestPage; 