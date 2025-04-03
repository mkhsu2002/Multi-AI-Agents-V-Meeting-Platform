import React, { useState, useEffect } from 'react';
import { fetchScenarios } from '../utils/api';

const SetupPanel = ({ initialConfig, onStart }) => {
  const [config, setConfig] = useState(initialConfig);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [scenarios, setScenarios] = useState({});
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(false);

  // 在組件加載時獲取情境模組列表
  useEffect(() => {
    const loadScenarios = async () => {
      setIsLoadingScenarios(true);
      try {
        const data = await fetchScenarios();
        setScenarios(data);
        // 如果初始配置中沒有指定情境，設置為預設情境
        if (!config.scenario && data.default) {
          setConfig({ ...config, scenario: data.default });
        }
      } catch (error) {
        console.error('獲取情境模組失敗:', error);
      } finally {
        setIsLoadingScenarios(false);
      }
    };

    loadScenarios();
  }, []);

  // 處理主題變更
  const handleTopicChange = (e) => {
    setConfig({ ...config, topic: e.target.value });
  };

  // 處理附註補充資料變更
  const handleAdditionalNotesChange = (e) => {
    setConfig({ ...config, additional_notes: e.target.value });
  };

  // 處理回合數量變更
  const handleRoundsChange = (e) => {
    const rounds = parseInt(e.target.value);
    if (rounds >= 1 && rounds <= 20) {
      setConfig({ ...config, rounds });
    }
  };

  // 處理主席變更
  const handleChairChange = (e) => {
    setConfig({ ...config, chair: e.target.value });
  };

  // 處理情境模組變更
  const handleScenarioChange = (e) => {
    setConfig({ ...config, scenario: e.target.value });
  };

  // 處理參與者活躍狀態變更
  const handleParticipantActiveChange = (id, isActive) => {
    const updatedParticipants = config.participants.map(p => 
      p.id === id ? { ...p, isActive } : p
    );
    setConfig({ ...config, participants: updatedParticipants });
  };

  // 啟動會議
  const handleStartConference = () => {
    if (!config.topic.trim()) {
      alert('請輸入會議主題');
      return;
    }

    const activeParticipants = config.participants.filter(p => p.isActive);
    if (activeParticipants.length < 3) {
      alert('至少需要3位有效參與者才能開始會議');
      return;
    }

    setIsSubmitting(true);
    // 模擬API請求延遲
    setTimeout(() => {
      onStart(config);
      setIsSubmitting(false);
    }, 500);
  };

  // 預設主題提示
  const defaultTopics = [
    '智能家居市場拓展策略',
    '新產品開發計劃',
    '年度預算分配',
    '品牌重塑與定位',
    '人才招募與培養方案',
    '遠程辦公政策實施',
    '數字化轉型戰略'
  ];

  // 隨機選擇一個預設主題
  const selectRandomTopic = () => {
    const randomTopic = defaultTopics[Math.floor(Math.random() * defaultTopics.length)];
    setConfig({ ...config, topic: randomTopic });
  };

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold text-primary mb-6 text-center">飛豬隊友 AI 虛擬會議</h1>
        
        {/* 會議主題設置 */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">會議主題</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={config.topic}
              onChange={handleTopicChange}
              placeholder="輸入會議討論主題..."
              className="flex-grow p-3 border rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
            />
            <button
              onClick={selectRandomTopic}
              className="px-4 py-2 bg-secondary text-white rounded-lg hover:bg-opacity-90 transition duration-200"
            >
              隨機主題
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-2">
            請輸入具體的討論主題，例如「新產品研發方向」或「市場拓展戰略」等。
          </p>
        </div>
        
        {/* 附註補充資料 */}
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-3">附註補充資料</h2>
          <textarea
            value={config.additional_notes || ''}
            onChange={handleAdditionalNotesChange}
            placeholder="輸入會議的補充背景資料、參考數據或重要考量..."
            className="w-full p-3 border rounded-lg h-32 focus:ring-2 focus:ring-primary focus:border-primary"
          />
          <p className="text-sm text-gray-500 mt-2">
            添加任何您希望AI角色考慮的附加資料，例如市場數據、關鍵要求或背景信息。這些資料將被納入會議討論中。
          </p>
        </div>
        
        {/* 會議參數設置 */}
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          <div>
            <h2 className="text-xl font-semibold mb-3">會議參數</h2>
            <div className="space-y-4">
              <div>
                <label className="block mb-1">討論回合數</label>
                <input
                  type="number"
                  min="1"
                  max="20"
                  value={config.rounds}
                  onChange={handleRoundsChange}
                  className="w-full p-2 border rounded-lg"
                />
                <p className="text-sm text-gray-500 mt-1">設置1-20輪之間的回合數</p>
              </div>
              
              <div>
                <label className="block mb-1">會議主席</label>
                <select
                  value={config.chair}
                  onChange={handleChairChange}
                  className="w-full p-2 border rounded-lg"
                >
                  {config.participants
                    .filter(p => p.isActive && p.id !== 'Secretary')
                    .map(p => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.title})
                      </option>
                    ))}
                </select>
                <p className="text-sm text-gray-500 mt-1">主席將引導討論進程</p>
              </div>

              {/* 新增：情境模組選擇 */}
              <div>
                <label className="block mb-1">研討情境模式</label>
                <select
                  value={config.scenario || ''}
                  onChange={handleScenarioChange}
                  className="w-full p-2 border rounded-lg"
                  disabled={isLoadingScenarios}
                >
                  {isLoadingScenarios ? (
                    <option>載入中...</option>
                  ) : (
                    scenarios.scenarios && 
                    Object.entries(scenarios.scenarios).map(([id, scenario]) => (
                      <option key={id} value={id}>
                        {scenario.name} - {scenario.description}
                      </option>
                    ))
                  )}
                </select>
                <p className="text-sm text-gray-500 mt-1">選擇會議情境模式，以優化對話邏輯</p>
              </div>
            </div>
          </div>
          
          {/* 參與者配置 */}
          <div>
            <h2 className="text-xl font-semibold mb-3">會議參與者</h2>
            <div className="space-y-2 max-h-60 overflow-y-auto p-2">
              {config.participants.map((participant) => (
                <div 
                  key={participant.id} 
                  className="flex items-center p-2 border rounded-lg hover:bg-gray-50"
                >
                  <input
                    type="checkbox"
                    checked={participant.isActive}
                    onChange={(e) => handleParticipantActiveChange(participant.id, e.target.checked)}
                    className="mr-3 h-5 w-5 text-primary focus:ring-primary"
                    disabled={participant.id === 'Secretary'}
                  />
                  <div>
                    <div className="font-medium">{participant.name}</div>
                    <div className="text-sm text-gray-500">{participant.title}</div>
                  </div>
                  <div className="ml-auto text-xs bg-gray-200 px-2 py-1 rounded">
                    溫度: {participant.temperature}
                  </div>
                </div>
              ))}
            </div>
            <p className="text-sm text-gray-500 mt-2">
              選擇參與會議的成員（秘書為必選成員）
            </p>
          </div>
        </div>
        
        {/* 情境模組說明 */}
        {scenarios.selection_guide && (
          <div className="mb-6 bg-gray-50 p-4 rounded-lg">
            <h2 className="text-xl font-semibold mb-2">研討情境說明</h2>
            <div className="whitespace-pre-line text-sm">
              {scenarios.selection_guide}
            </div>
          </div>
        )}
        
        {/* 預設會議說明 */}
        <div className="mb-6 bg-gray-50 p-4 rounded-lg">
          <h2 className="text-xl font-semibold mb-2">會議進行規則</h2>
          <ol className="list-decimal pl-5 space-y-1">
            <li>會議開始時，每個智能體會進行簡短自我介紹</li>
            <li>主席將引導會議進程，提出討論議題</li>
            <li>每輪討論中，參與者依次發表意見</li>
            <li>討論完成所有回合後，秘書將總結會議內容</li>
            <li>您可以在會議結束後查看或導出會議記錄</li>
          </ol>
        </div>
        
        {/* 開始會議按鈕 */}
        <div className="text-center">
          <button
            onClick={handleStartConference}
            disabled={isSubmitting || !config.topic.trim()}
            className={`px-8 py-3 rounded-lg text-lg font-medium transition duration-200 ${
              isSubmitting || !config.topic.trim() 
                ? 'bg-gray-300 cursor-not-allowed' 
                : 'bg-primary text-white hover:bg-opacity-90'
            }`}
          >
            {isSubmitting ? '準備會議中...' : '開始會議'}
          </button>
        </div>
        
      </div>
    </div>
  );
};

export default SetupPanel; 