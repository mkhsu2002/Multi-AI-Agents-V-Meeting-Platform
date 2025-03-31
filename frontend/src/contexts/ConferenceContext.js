import React, { createContext, useContext, useState, useEffect } from 'react';
import { MODERATOR_CONFIG, MESSAGE_TYPES, CONFERENCE_STAGES } from '../config/agents';
import { startConference, createWebSocketConnection } from '../utils/api';

const ConferenceContext = createContext();

export const useConference = () => useContext(ConferenceContext);

// 建立API和WebSocket的基本URL
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

export const ConferenceProvider = ({ children }) => {
  const [config, setConfig] = useState(null);
  const [messages, setMessages] = useState([]);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [conferenceStage, setConferenceStage] = useState('waiting');
  const [currentRound, setCurrentRound] = useState(0);
  const [conclusion, setConclusion] = useState(null);
  const [socket, setSocket] = useState(null);
  const [conferenceId, setConferenceId] = useState(null);
  const [error, setError] = useState(null);

  // 建立WebSocket連接
  const connectSocket = (confId) => {
    if (!confId) return;

    try {
      // 關閉任何現有連接
      if (socket) {
        socket.close();
      }

      const newSocket = new WebSocket(`${WS_BASE_URL}/ws/conference/${confId}`);
      
      newSocket.onopen = () => {
        console.log('WebSocket連接已建立');
        setError(null); // 清除任何先前的錯誤
      };
      
      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('收到WebSocket消息:', data);
        
        // 處理錯誤消息
        if (data.type === MESSAGE_TYPES.ERROR) {
          console.error('收到錯誤訊息:', data.message);
          setError(data.message);
          setIsLoading(false);
          
          // 如果錯誤是因為會議不存在，可以考慮重新創建會議
          if (data.message === "會議不存在" && config) {
            console.log('嘗試重新創建會議...');
            // 延遲1秒後重新創建會議
            setTimeout(() => {
              startConference(config);
            }, 1000);
          }
          return;
        }
        
        switch (data.type) {
          case MESSAGE_TYPES.INIT:
            setMessages(data.messages || []);
            setConferenceStage(data.stage || 'waiting');
            setCurrentRound(data.current_round || 0);
            setConclusion(data.conclusion);
            setIsLoading(false);
            break;
            
          case MESSAGE_TYPES.NEW_MESSAGE:
            setMessages(prev => [...prev, data.message]);
            setCurrentSpeaker(data.current_speaker);
            break;
            
          case MESSAGE_TYPES.STAGE_CHANGE:
            setConferenceStage(data.stage);
            break;
            
          case MESSAGE_TYPES.ROUND_UPDATE:
            setCurrentRound(data.round);
            break;
            
          case MESSAGE_TYPES.ROUND_COMPLETED:
            // 當一輪討論完成時，可能需要在UI上提示用戶
            console.log('當前輪次討論已完成');
            break;
            
          case MESSAGE_TYPES.CONCLUSION:
            // 處理會議結論
            setConclusion(data.text);
            break;
            
          default:
            console.log('未處理的WebSocket消息類型:', data.type);
        }
      };
      
      newSocket.onerror = (error) => {
        console.error('WebSocket錯誤:', error);
        setError('WebSocket連接錯誤，請檢查後端服務是否正在運行，或者嘗試刷新頁面。');
        setIsLoading(false);
        
        // 嘗試在短暫延遲後進行自動重連
        setTimeout(() => {
          if (confId && config) {
            console.log('WebSocket錯誤後自動嘗試重連...');
            connectSocket(confId);
          }
        }, 5000); // 5秒後嘗試重連
      };
      
      newSocket.onclose = (event) => {
        console.log(`WebSocket連接已關閉，代碼: ${event.code}, 原因: ${event.reason}`);
        
        if (event.code === 1011) {
          // 伺服器內部錯誤，顯示具體錯誤原因
          setError(`伺服器內部錯誤: ${event.reason || '未知錯誤'}，請聯繫管理員或稍後再試。`);
          return;
        }
        
        // 如果是正常關閉，不需處理
        if (event.code === 1000) {
          return;
        }
        
        // 如果是非正常關閉，且有配置，嘗試重新連接
        if (config && !event.wasClean) {
          console.log('嘗試重新連接...');
          setTimeout(() => {
            if (confId) {
              // 先嘗試直接重連
              connectSocket(confId);
            } else if (config) {
              // 如果沒有會議ID，嘗試重新創建會議
              startConference(config);
            }
          }, 3000); // 延遲3秒後重試
        }
      };
      
      setSocket(newSocket);
      
    } catch (err) {
      console.error('建立WebSocket連接時出錯:', err);
      setError('無法連接到會議服務，請檢查後端服務是否正在運行。若問題持續存在，請嘗試刷新頁面或重新啟動應用。');
      setIsLoading(false);
    }
  };

  // 啟動會議
  const startConference = async (configData) => {
    try {
      setConfig(configData);
      setIsLoading(true);
      setError(null);
      
      // 添加主持人
      const configWithModerator = {
        ...configData,
        participants: [
          MODERATOR_CONFIG,
          ...configData.participants
        ]
      };
      
      // 發送API請求創建會議
      const response = await fetch(`${API_BASE_URL}/api/conference/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configWithModerator),
      });
      
      const data = await response.json();
      console.log('收到會議創建響應:', data);
      
      if (!response.ok || !data.conference_id) {
        throw new Error(data.error || data.detail || '創建會議失敗');
      }
      
      // 保存會議ID
      setConferenceId(data.conference_id);
      
      // 連接WebSocket
      connectSocket(data.conference_id);
      
      return {
        success: true,
        conferenceId: data.conference_id
      };
      
    } catch (err) {
      console.error('啟動會議時出錯:', err);
      setIsLoading(false);
      setError(err.message || '啟動會議時發生錯誤');
      return {
        success: false,
        error: err.message || '啟動會議時發生錯誤'
      };
    }
  };

  // 進入下一輪討論
  const nextRound = () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: MESSAGE_TYPES.NEXT_ROUND }));
    } else {
      setError('WebSocket連接已關閉，無法進入下一輪討論');
    }
  };

  // 結束會議
  const endConference = () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: MESSAGE_TYPES.END_CONFERENCE }));
    } else {
      setError('WebSocket連接已關閉，無法結束會議');
    }
  };

  // 暫停會議
  const pauseConference = () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: MESSAGE_TYPES.PAUSE_CONFERENCE }));
    } else {
      setError('WebSocket連接已關閉，無法暫停會議');
    }
  };

  // 恢復會議
  const resumeConference = () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: MESSAGE_TYPES.RESUME_CONFERENCE }));
    } else {
      setError('WebSocket連接已關閉，無法恢復會議');
    }
  };

  // 匯出會議記錄
  const exportRecord = () => {
    // 格式化會議記錄
    let record = `# 會議記錄\n\n`;
    record += `## 主題: ${config.topic}\n\n`;
    
    // 添加會議模式信息
    let scenarioName = '標準商務會議';
    if (config.scenario) {
      // 將scenario_id轉換為更友好的顯示名稱
      switch (config.scenario) {
        case 'brainstorming':
          scenarioName = '腦力激盪模式';
          break;
        case 'board_meeting':
          scenarioName = '董事會議模式';
          break;
        case 'debate':
          scenarioName = '辯論大會模式';
          break;
        case 'creative_chain':
          scenarioName = '創作接龍模式';
          break;
        default:
          scenarioName = config.scenario; // 如果找不到特定名稱，使用原始值
      }
    }
    record += `## 會議模式: ${scenarioName}\n\n`;
    
    record += `## 參與者:\n`;
    
    config.participants.forEach(p => {
      if (p.isActive) {
        record += `- ${p.name} (${p.title})\n`;
      }
    });
    
    // 如果有附註補充資料，添加到記錄中
    if (config.additional_notes && config.additional_notes.trim()) {
      record += `\n## 附註補充資料:\n${config.additional_notes}\n\n`;
    }
    
    record += `\n## 對話內容:\n\n`;
    
    messages.forEach(msg => {
      const time = new Date(msg.timestamp).toLocaleTimeString();
      record += `### ${time} - ${msg.speakerName} (${msg.speakerTitle}):\n${msg.text}\n\n`;
    });
    
    if (conclusion) {
      record += `## 會議結論:\n\n${conclusion}\n`;
    }
    
    // 建立並下載文件
    const blob = new Blob([record], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `會議記錄-${config.topic}-${new Date().toISOString().slice(0, 10)}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // 清理資源
  useEffect(() => {
    return () => {
      if (socket) {
        socket.close();
      }
    };
  }, [socket]);

  const value = {
    config,
    messages,
    currentSpeaker,
    isLoading,
    conferenceStage,
    currentRound,
    conclusion,
    error,
    startConference,
    nextRound,
    endConference,
    pauseConference,
    resumeConference,
    exportRecord
  };

  return (
    <ConferenceContext.Provider value={value}>
      {children}
    </ConferenceContext.Provider>
  );
};

export default ConferenceContext; 