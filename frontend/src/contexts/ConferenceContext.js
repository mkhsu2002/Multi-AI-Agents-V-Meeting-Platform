import React, { createContext, useContext, useState, useEffect } from 'react';

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
      };
      
      newSocket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('收到WebSocket消息:', data);
        
        switch (data.type) {
          case 'init':
            setMessages(data.messages || []);
            setConferenceStage(data.stage || 'waiting');
            setCurrentRound(data.current_round || 0);
            setConclusion(data.conclusion);
            setIsLoading(false);
            break;
            
          case 'new_message':
            setMessages(prev => [...prev, data.message]);
            setCurrentSpeaker(data.current_speaker);
            break;
            
          case 'stage_change':
            setConferenceStage(data.stage);
            break;
            
          case 'round_update':
            setCurrentRound(data.round);
            break;
            
          case 'round_completed':
            // 當一輪討論完成時，可能需要在UI上提示用戶
            console.log('當前輪次討論已完成');
            break;
            
          case 'error':
            setError(data.message);
            setIsLoading(false);
            break;
            
          default:
            console.log('未處理的WebSocket消息類型:', data.type);
        }
      };
      
      newSocket.onerror = (error) => {
        console.error('WebSocket錯誤:', error);
        setError('WebSocket連接錯誤，請檢查後端服務是否正在運行。');
        setIsLoading(false);
      };
      
      newSocket.onclose = () => {
        console.log('WebSocket連接已關閉');
      };
      
      setSocket(newSocket);
      
    } catch (err) {
      console.error('建立WebSocket連接時出錯:', err);
      setError('無法連接到會議服務，請檢查後端服務是否正在運行。');
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
          {
            id: "moderator",
            name: "會議主持人",
            title: "AI會議助手",
            personality: "專業、公正、有條理",
            expertise: "會議協調與總結",
            isActive: true
          },
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
      
      if (!response.ok || !data.success) {
        throw new Error(data.error || '創建會議失敗');
      }
      
      // 保存會議ID
      setConferenceId(data.conferenceId);
      
      // 連接WebSocket
      connectSocket(data.conferenceId);
      
      return {
        success: true,
        conferenceId: data.conferenceId
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
      socket.send(JSON.stringify({ type: 'next_round' }));
    } else {
      setError('WebSocket連接已關閉，無法進入下一輪討論');
    }
  };

  // 結束會議
  const endConference = () => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'end_conference' }));
    } else {
      setError('WebSocket連接已關閉，無法結束會議');
    }
  };

  // 匯出會議記錄
  const exportRecord = () => {
    // 格式化會議記錄
    let record = `# 會議記錄\n\n`;
    record += `## 主題: ${config.topic}\n\n`;
    record += `## 參與者:\n`;
    
    config.participants.forEach(p => {
      if (p.isActive) {
        record += `- ${p.name} (${p.title})\n`;
      }
    });
    
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
    exportRecord
  };

  return (
    <ConferenceContext.Provider value={value}>
      {children}
    </ConferenceContext.Provider>
  );
};

export default ConferenceContext; 