// 添加日誌，顯示發送前的會議配置
const handleStartConference = () => {
  console.log("準備發送的會議配置:", {
    topic,
    participants: selectedParticipants,
    rounds,
    conclusion: true
  });
  
  startConference();
}; 