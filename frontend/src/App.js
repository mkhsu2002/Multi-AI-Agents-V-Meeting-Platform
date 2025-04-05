import React, { useState, useEffect, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import ConferenceRoom from './pages/ConferenceRoom';
import SetupPanel from './pages/SetupPanel';
import TestPage from './pages/TestPage';
import AgentManagement from './pages/AgentManagement';
import { ConferenceProvider } from './contexts/ConferenceContext';
import { DEFAULT_ROLES } from './config/agents';
import './App.css';

function App() {
  const [isSetup, setIsSetup] = useState(true);
  const [conferenceConfig, setConferenceConfig] = useState({
    topic: '',
    rounds: 6,
    chair: 'General manager',
    participants: [],
    scenario: null,
    language: "繁體中文",
    conclusion: true
  });

  // 使用 useCallback 包裝 loadAgentData
  const loadAgentData = useCallback(() => {
    try {
      const savedAgents = localStorage.getItem('agents');
      if (savedAgents) {
        const parsedAgents = JSON.parse(savedAgents);
        
        // 更新會議主席（如果當前主席不在列表中）
        let foundChair = parsedAgents.find(agent => agent.id === conferenceConfig.chair);
        if (!foundChair) {
          // 尋找第一個非秘書的啟用角色作為新主席
          const newChair = parsedAgents.find(agent => agent.id !== 'Secretary' && agent.isActive);
          if (newChair) {
            setConferenceConfig(prev => ({
              ...prev,
              chair: newChair.id
            }));
          }
        }
        
        // 更新參與者列表
        setConferenceConfig(prev => ({
          ...prev,
          participants: parsedAgents
        }));
      } else {
        // 使用默認角色
        setConferenceConfig(prev => ({
          ...prev,
          participants: DEFAULT_ROLES
        }));
      }
    } catch (error) {
      console.error('Error loading agent data:', error);
      // 出錯時使用默認角色
      setConferenceConfig(prev => ({
        ...prev,
        participants: DEFAULT_ROLES
      }));
    }
  }, [conferenceConfig.chair]);

  // 使用 useCallback 包裝 handleAgentDataChanged
  const handleAgentDataChanged = useCallback((event) => {
    if (event.detail) {
      setConferenceConfig(prev => ({
        ...prev,
        participants: event.detail
      }));
    } else {
      loadAgentData();
    }
  }, [loadAgentData]);

  // 使用 useCallback 包裝 handleStorageChange
  const handleStorageChange = useCallback((event) => {
    if (event.key === 'agents') {
      loadAgentData();
    }
  }, [loadAgentData]);

  // 將穩定引用的函數添加到 useEffect 依賴數組
  useEffect(() => {
    loadAgentData();
    window.addEventListener('agentDataChanged', handleAgentDataChanged);
    window.addEventListener('storage', handleStorageChange);
    return () => {
      window.removeEventListener('agentDataChanged', handleAgentDataChanged);
      window.removeEventListener('storage', handleStorageChange);
    };
  }, [loadAgentData, handleAgentDataChanged, handleStorageChange]);

  const startConference = (config) => {
    const completeConfig = {
      ...conferenceConfig,
      ...config,
      scenario: config.scenario || conferenceConfig.scenario
    };
    setConferenceConfig(completeConfig);
    setIsSetup(false);
  };

  const MainContent = () => (
    <ConferenceProvider>
      {isSetup ? (
        <SetupPanel 
          initialConfig={conferenceConfig} 
          onStart={startConference} 
        />
      ) : (
        <ConferenceRoom 
          config={conferenceConfig}
          onBackToSetup={() => setIsSetup(true)}
        />
      )}
    </ConferenceProvider>
  );
  
  const Navigation = () => (
    <nav className="p-4 bg-primary text-white">
      <div className="container mx-auto flex justify-between items-center">
        <div className="text-xl font-bold">飛豬隊友 AI 虛擬會議系統</div>
        <div className="space-x-4">
          <Link to="/" className="hover:underline">首頁</Link>
          <Link to="/agents" className="hover:underline">智能體管理</Link>
          <Link to="/test" className="hover:underline">測試頁面</Link>
        </div>
      </div>
    </nav>
  );

  const Footer = () => (
    <footer className="p-4 bg-primary text-white text-center mt-8">
      <div className="container mx-auto">
        <div className="mb-2">飛豬隊友 AI 虛擬會議系統 v2.1.0</div>
        <div className="flex justify-center items-center space-x-4">
          <a 
            href="https://buymeacoffee.com/mkhsu2002w" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center bg-yellow-500 text-black px-4 py-2 rounded-lg hover:bg-yellow-400 transition-colors duration-300"
          >
            <span role="img" aria-label="coffee" className="mr-2">☕</span>
            買杯咖啡支持我們
          </a>
          <a 
            href="https://github.com/mkhsu2002/TinyPigTroupe" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center bg-gray-700 px-4 py-2 rounded-lg hover:bg-gray-600 transition-colors duration-300"
          >
            <span role="img" aria-label="github" className="mr-2">⭐</span>
            GitHub
          </a>
        </div>
        <div className="mt-2 text-sm opacity-80">© 2023-2025 FlyPig AI</div>
      </div>
    </footer>
  );

  return (
    <Router>
      <div className="App min-h-screen bg-background text-text flex flex-col">
        <Navigation />
        <div className="flex-grow">
          <Routes>
            <Route path="/" element={<MainContent />} />
            <Route path="/agents" element={<AgentManagement />} />
            <Route path="/test" element={<TestPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
        <Footer />
      </div>
    </Router>
  );
}

export default App; 