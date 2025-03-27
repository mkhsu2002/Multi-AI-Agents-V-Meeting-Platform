const handleStartConference = () => {
  console.log("準備發送的會議配置:", {
    topic,
    participants: selectedParticipants,
    rounds,
    conclusion: true
  });
  
  // 設置會議配置
  setConfig({
    topic,
    participants: selectedParticipants,
    rounds,
    conclusion: true
  });
  
  // 啟動會議
  startConference();
}; 