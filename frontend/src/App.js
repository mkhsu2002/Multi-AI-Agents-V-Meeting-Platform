import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import ConferenceRoom from './pages/ConferenceRoom';
import SetupPanel from './pages/SetupPanel';
import TestPage from './pages/TestPage';
import { ConferenceProvider } from './contexts/ConferenceContext';
import './App.css';

function App() {
  const [isSetup, setIsSetup] = useState(true);
  const [conferenceConfig, setConferenceConfig] = useState({
    topic: '',
    rounds: 6,
    chair: 'Pig Boss',
    participants: [
      { id: 'Pig Boss', name: '豬霸天', title: '總經理', temperature: 0.7, isActive: true },
      { id: 'Brainy Pig', name: '豬腦筋', title: '行銷經理', temperature: 0.6, isActive: true },
      { id: 'Busy Pig', name: '豬搶錢', title: '業務經理', temperature: 0.6, isActive: true },
      { id: 'Professor Pig', name: '豬博士', title: '研發主管', temperature: 0.5, isActive: true },
      { id: 'Calculator Pig', name: '豬算盤', title: '財務經理', temperature: 0.4, isActive: true },
      { id: 'Caregiver Pig', name: '豬保姆', title: '人事經理', temperature: 0.5, isActive: true },
      { id: 'Secretary Pig', name: '豬秘書', title: '秘書', temperature: 0.3, isActive: true }
    ]
  });

  const startConference = (config) => {
    setConferenceConfig(config);
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
        <div className="text-xl font-bold">小豬會議系統</div>
        <div className="space-x-4">
          <Link to="/" className="hover:underline">首頁</Link>
          <Link to="/test" className="hover:underline">測試頁面</Link>
        </div>
      </div>
    </nav>
  );

  const Footer = () => (
    <footer className="p-4 bg-primary text-white text-center mt-8">
      <div className="container mx-auto">
        <div className="mb-2">飛豬隊友 AI 虛擬會議系統 v1.1</div>
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