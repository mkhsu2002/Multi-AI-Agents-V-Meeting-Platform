import React, { useEffect, useRef, useState } from 'react';
import { useConference } from '../contexts/ConferenceContext';
import PigAvatar from '../components/PigAvatar';
import MessageBubble from '../components/MessageBubble';

const ConferenceRoom = ({ config, onBackToSetup }) => {
  const {
    messages,
    currentSpeaker,
    isLoading,
    currentRound,
    conferenceStage,
    conclusion,
    error,
    startConference,
    exportRecord
  } = useConference();
  
  const messagesEndRef = useRef(null);
  const [showFullHistory, setShowFullHistory] = useState(false);
  const [localError, setLocalError] = useState(null);
  
  // 開始會議
  useEffect(() => {
    const initConference = async () => {
      try {
        const result = await startConference(config);
        if (!result.success) {
          setLocalError(result.error || '啟動會議失敗');
        }
      } catch (err) {
        setLocalError(err.message || '啟動會議時發生錯誤');
      }
    };
    
    initConference();
  }, []);
  
  // 自動滾動到最新消息
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);
  
  // 計算要顯示的消息
  const displayMessages = showFullHistory 
    ? messages 
    : messages.slice(Math.max(0, messages.length - 10));
  
  // 根據會議階段顯示不同的標題
  const getStageTitle = () => {
    switch (conferenceStage) {
      case 'waiting':
        return '準備開始會議...';
      case 'introduction':
        return '成員自我介紹';
      case 'discussion':
        return `討論階段 (第 ${currentRound} 輪，共 ${config.rounds} 輪)`;
      case 'conclusion':
        return '會議總結';
      case 'ended':
        return '會議已結束';
      default:
        return '飛豬隊友 AI 虛擬會議';
    }
  };

  // 顯示的錯誤訊息(合併本地和上下文錯誤)
  const displayError = localError || error;

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* 會議標頭 */}
      <div className="bg-white rounded-lg shadow-md p-4 mb-4 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-primary">飛豬隊友 AI 虛擬會議</h1>
          <p className="text-lg">主題：{config.topic || '未指定主題'}</p>
          <p className="text-sm text-gray-600">{getStageTitle()}</p>
        </div>
        <div className="flex gap-2">
          <button 
            onClick={onBackToSetup}
            className="px-4 py-2 bg-gray-200 rounded-md hover:bg-gray-300 transition duration-200"
            disabled={!displayError && conferenceStage !== 'ended' && conferenceStage !== 'waiting' && !isLoading}
          >
            {displayError ? '返回重試' : '返回設置'}
          </button>
          <button 
            onClick={exportRecord}
            className="px-4 py-2 bg-secondary text-white rounded-md hover:bg-opacity-90 transition duration-200"
            disabled={messages.length === 0 || isLoading}
          >
            匯出會議記錄
          </button>
        </div>
      </div>
      
      {/* 錯誤提示 */}
      {displayError && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <p className="font-bold">錯誤</p>
          <p>{displayError}</p>
          <p className="mt-2 text-sm">
            請確保後端服務正在運行，並且已經正確配置了OpenAI API金鑰。點擊"返回重試"按鈕重新配置。
          </p>
        </div>
      )}
      
      {/* 載入中指示器 */}
      {isLoading && !displayError && (
        <div className="flex justify-center items-center h-40">
          <div className="animate-bounce-slow">
            <div className="w-20 h-20 bg-primary rounded-full flex items-center justify-center text-white text-2xl font-bold">
              豬
            </div>
          </div>
          <p className="ml-3 text-lg">載入中...正在準備會議</p>
        </div>
      )}
      
      {/* 會議室主體 */}
      {!isLoading && !displayError && conferenceStage !== 'waiting' && (
        <div className="flex flex-col md:flex-row gap-4">
          {/* 左側參與者顯示 */}
          <div className="md:w-1/4 bg-white rounded-lg shadow-md p-4">
            <h2 className="text-xl font-bold mb-4">會議參與者</h2>
            <div className="space-y-4">
              {config.participants
                .filter(p => p.isActive)
                .map((participant) => (
                  <div 
                    key={participant.id}
                    className={`flex items-center p-2 rounded-lg ${
                      currentSpeaker === participant.id 
                        ? 'bg-primary bg-opacity-10' 
                        : 'hover:bg-gray-100'
                    } transition-all duration-200`}
                  >
                    <PigAvatar 
                      name={participant.name}
                      title={participant.title}
                      isActive={currentSpeaker === participant.id}
                      size="sm"
                    />
                    <div className="ml-3">
                      <p className="font-medium">{participant.name}</p>
                      <p className="text-sm text-gray-500">{participant.title}</p>
                    </div>
                  </div>
                ))
              }
            </div>
          </div>
          
          {/* 右側對話區域 */}
          <div className="md:w-3/4 bg-white rounded-lg shadow-md p-4 flex flex-col">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">會議對話</h2>
              <button 
                onClick={() => setShowFullHistory(!showFullHistory)}
                className="text-sm text-secondary hover:underline"
              >
                {showFullHistory ? '只顯示最近消息' : '顯示完整歷史'}
              </button>
            </div>
            
            {/* 對話記錄區域 */}
            <div className="flex-grow overflow-y-auto max-h-[60vh] p-4 bg-gray-50 rounded-lg">
              {displayMessages.length === 0 ? (
                <p className="text-center text-gray-500 py-10">會議即將開始，請稍候...</p>
              ) : (
                <div className="space-y-6">
                  {displayMessages.map((msg) => (
                    <MessageBubble 
                      key={msg.id}
                      speaker={msg.speakerName}
                      title={msg.speakerTitle}
                      text={msg.text}
                      isActive={currentSpeaker === msg.speakerId}
                      timestamp={new Date(msg.timestamp).toLocaleTimeString()}
                    />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
            
            {/* 會議結論 */}
            {conferenceStage === 'ended' && conclusion && (
              <div className="mt-4 p-4 bg-accent bg-opacity-20 rounded-lg border border-accent">
                <h3 className="text-lg font-bold mb-2">會議結論</h3>
                <div className="whitespace-pre-line">
                  {conclusion}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConferenceRoom; 