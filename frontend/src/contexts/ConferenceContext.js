import React, { createContext, useState, useEffect, useCallback, useContext, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getConference, getConferenceMessages, startConference as apiStartConference } from '../utils/api';
import { MESSAGE_TYPES } from '../config/agents';
import { toast } from 'react-toastify';

const ConferenceContext = createContext();

export const useConference = () => useContext(ConferenceContext);

export const ConferenceProvider = ({ children }) => {
  const [currentConferenceId, setCurrentConferenceId] = useState(null);
  const [conferenceData, setConferenceData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [stage, setStage] = useState('loading');
  const [currentRound, setCurrentRound] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);
  const ws = useRef(null);
  const navigate = useNavigate();
  const lastMessageRef = useRef(null);

  const connectSocket = useCallback((confId) => {
    if (!confId) return;
    console.log(`嘗試連接 WebSocket: ${confId}`);

    if (ws.current) {
      ws.current.close();
      console.log("已關閉舊的 WebSocket 連接");
    }

    const wsBaseUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000'; 
    const wsUrl = `${wsBaseUrl}/ws/conference/${confId}`;
    
    try {
      const newSocket = new WebSocket(wsUrl);
      ws.current = newSocket;

      newSocket.onopen = () => {
        console.log(`WebSocket 連接已建立: ${confId}`);
        setError(null);
      };

      newSocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('收到 WebSocket 消息:', data);

          if (data.type === MESSAGE_TYPES.ERROR) {
            console.error('收到錯誤訊息:', data.message);
            setError(data.message);
            setIsLoading(false);
            return;
          }

          switch (data.type) {
            case MESSAGE_TYPES.INIT:
              setMessages(data.messages || []);
              setStage(data.stage || 'waiting');
              setCurrentRound(data.current_round || 0);
              setIsLoading(false);
              break;
            case MESSAGE_TYPES.NEW_MESSAGE:
              setMessages(prev => [...prev, data.message]);
              setCurrentSpeaker(data.current_speaker);
              setTimeout(() => lastMessageRef.current?.scrollIntoView({ behavior: "smooth" }), 100);
              break;
            case MESSAGE_TYPES.STAGE_CHANGE:
              setStage(data.stage);
              setIsLoading(false);
              break;
            case MESSAGE_TYPES.ROUND_UPDATE:
              setCurrentRound(data.round);
              break;
            case MESSAGE_TYPES.ROUND_COMPLETED:
              console.log('當前輪次討論已完成');
              break;
            default:
              console.log('未處理的 WebSocket 消息類型:', data.type);
          }
        } catch (parseError) {
          console.error('解析 WebSocket 消息失敗:', parseError, '原始數據:', event.data);
        }
      };

      newSocket.onerror = (errorEvent) => {
        console.error('WebSocket 錯誤:', errorEvent);
        setError('WebSocket 連接錯誤，請檢查後端服務或網絡連接。');
        setIsLoading(false);
      };

      newSocket.onclose = (event) => {
        console.log(`WebSocket 連接已關閉，代碼: ${event.code}, 原因: ${event.reason}`);
        setIsLoading(false); 
        setStage(prevStage => prevStage !== 'ended' ? 'ended' : 'ended'); 
        
        if (!event.wasClean && currentConferenceId) {
          setError("WebSocket 連接意外斷開。"); 
          console.warn("WebSocket 連接意外斷開");
        }
        
        if (ws.current === newSocket) { 
          ws.current = null;
        }
      };
    } catch (err) {
      console.error('創建 WebSocket 連接失敗:', err);
      setError('無法創建 WebSocket 連接。');
      setIsLoading(false);
    }
  }, [currentConferenceId]);

  const loadConference = useCallback(async (confId) => {
    if (!confId) return;
    console.log(`加載會議數據: ${confId}`);
    setIsLoading(true);
    setError(null);
    setMessages([]);
    setCurrentConferenceId(confId);
    try {
      const data = await getConference(confId);
      setConferenceData(data);
      setStage(data.stage || 'waiting');
      setCurrentRound(data.current_round || 0);
      
      connectSocket(confId);
    } catch (err) {
      console.error('加載會議數據失敗:', err);
      setError('加載會議數據失敗: ' + err.message);
      setIsLoading(false);
      setCurrentConferenceId(null);
    }
  }, [navigate, connectSocket]);

  const startConference = useCallback(async (config) => {
    console.log("ConferenceContext: 嘗試啟動會議", config);
    setIsLoading(true);
    setError(null);
    setMessages([]);
    try {
      const result = await apiStartConference(config);
      console.log("後端返回的啟動結果:", result);
      if (result && result.success && result.conference_id) {
        const newConferenceId = result.conference_id;
        setCurrentConferenceId(newConferenceId);
        setConferenceData({ config: config, id: newConferenceId, ...result });
        setStage('waiting');
        setCurrentRound(0);
        connectSocket(newConferenceId);
        console.log(`會議 ${newConferenceId} 成功啟動，正在連接 WebSocket...`);
        return { success: true, conferenceId: newConferenceId };
      } else {
        const errorMsg = result?.error || result?.message || '啟動會議失敗，後端未返回有效數據';
        console.error('啟動會議失敗:', errorMsg);
        setError(errorMsg);
        setIsLoading(false);
        return { success: false, error: errorMsg };
      }
    } catch (err) {
      console.error('啟動會議時發生錯誤:', err);
      const errorMsg = err.response?.data?.detail || err.message || '啟動會議時發生未知網絡或服務器錯誤';
      setError(errorMsg);
      setIsLoading(false);
      return { success: false, error: errorMsg };
    }
  }, [connectSocket]);

  const sendWsMessage = useCallback((message) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(message));
    } else {
      console.error('WebSocket 未連接，無法發送消息:', message);
      setError("WebSocket 連接已斷開，無法發送指令。");
    }
  }, []);

  const pauseConference = useCallback(() => {
    sendWsMessage({ type: MESSAGE_TYPES.PAUSE_CONFERENCE });
  }, [sendWsMessage]);

  const resumeConference = useCallback(() => {
    sendWsMessage({ type: MESSAGE_TYPES.RESUME_CONFERENCE });
  }, [sendWsMessage]);

  const manualEndConference = useCallback(async () => {
    console.log("ConferenceContext: 手動請求結束會議...");
    setIsLoading(true);
    setError(null);
    try {
      sendWsMessage({ type: MESSAGE_TYPES.END_CONFERENCE });
      console.log("結束會議指令已發送");
    } catch (err) {
      console.error("發送結束會議指令時發生錯誤:", err);
      setError(`發送結束指令失敗: ${err.message || '未知錯誤'}`);
      setIsLoading(false); 
    }
  }, [sendWsMessage, navigate]);

  const exportRecord = useCallback(() => {
    console.log("請求匯出會議記錄...");

    if (!messages || messages.length === 0) {
      toast.warn("沒有會議記錄可供匯出。");
      console.warn("沒有會議記錄可供匯出。");
      return;
    }

    if (stage !== 'ended') {
      console.log(`會議狀態為 ${stage}，嘗試強制結束...`);
      toast.info("正在強制結束會議並準備下載...");
      manualEndConference();
    } else {
       toast.info("準備下載會議記錄...");
    }

    let recordContent = `會議記錄\n`;
    recordContent += `==============================\n`;
    if (conferenceData) {
      const config = conferenceData.config || {};
      recordContent += `會議 ID: ${conferenceData.id || '未知'}\n`;
      recordContent += `主題: ${config.topic || '未指定'}\n`;
      recordContent += `模式: ${config.scenario || '未知'}\n`;
      recordContent += `回合數: ${config.rounds || '未知'}\n`;
      recordContent += `開始時間: ${conferenceData.start_time ? new Date(conferenceData.start_time).toLocaleString() : '未知'}\n`;

      if (config.participants && config.participants.length > 0) {
        recordContent += `\n--- 參與者 ---\n`;
        config.participants.forEach(p => {
          recordContent += `- ${p.name} (${p.title})${p.isActive ? '' : ' (未啟用)'}\n`;
        });
      }
    } else {
      recordContent += `會議基本資訊未知。\n`;
    }
    recordContent += `==============================\n\n`;
    recordContent += `--- 對話記錄 ---\n\n`;

    messages.forEach(msg => {
      const timestamp = new Date(msg.timestamp).toLocaleString();
      recordContent += `[${timestamp}] ${msg.speakerName} (${msg.speakerTitle}):\n`;
      recordContent += `${msg.text}\n\n`;
    });

    recordContent += `--- 記錄結束 ---\n`;

    try {
      const blob = new Blob([recordContent], { type: 'text/plain;charset=utf-8' });
      const conferenceIdShort = currentConferenceId ? currentConferenceId.substring(0, 8) : 'unknown';
      const timestampStr = new Date().toISOString().replace(/[:.]/g, '-');
      const filename = `conference_record_${conferenceIdShort}_${timestampStr}.txt`;

      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      link.style.display = 'none';
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);

      console.log(`會議記錄已觸發下載: ${filename}`);

    } catch (exportError) {
      console.error("匯出會議記錄時發生錯誤:", exportError);
      setError(`匯出會議記錄失敗: ${exportError.message}`);
      toast.error("匯出會議記錄失敗！");
    }

  }, [messages, stage, conferenceData, currentConferenceId, manualEndConference, setError]);

  useEffect(() => {
    return () => {
      if (ws.current) {
        console.log("ConferenceProvider 卸載，關閉 WebSocket");
        ws.current.close();
        ws.current = null;
      }
    };
  }, []);

  const value = {
    conferenceData,
    messages,
    stage,
    currentRound,
    isLoading,
    error,
    currentSpeaker,
    lastMessageRef,
    loadConference,
    startConference,
    sendMessage: sendWsMessage,
    pauseConference,
    resumeConference,
    endConference: manualEndConference,
    exportRecord
  };

  return (
    <ConferenceContext.Provider value={value}>
      {children}
    </ConferenceContext.Provider>
  );
};

export default ConferenceContext; 