const startConference = async () => {
  try {
    setIsLoading(true);
    setError(null);
    
    // 添加主持人
    const configWithModerator = {
      ...config,
      participants: [
        {
          id: "moderator",
          name: "會議主持人",
          title: "AI會議助手",
          personality: "專業、公正、有條理",
          expertise: "會議協調與總結",
          isActive: true
        },
        ...config.participants
      ]
    };
    
    console.log("發送到後端的完整會議配置:", JSON.stringify(configWithModerator, null, 2));
    
    // 發送API請求創建會議
    const response = await fetch(`${API_BASE_URL}/api/conference/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(configWithModerator),
    });
    
    const data = await response.json();
    console.log("後端返回的會議創建響應:", data);
    
    if (!response.ok) {
      let errorMsg = data.error || data.detail || "創建會議失敗";
      if (Array.isArray(data.detail)) {
        errorMsg = data.detail.map(err => `${err.loc.join('.')}：${err.msg}`).join('\n');
      }
      console.error("會議創建失敗:", errorMsg);
      throw new Error(errorMsg);
    }
    
    // 成功創建會議
    setConferenceId(data.conferenceId);
    setStage('introduction');
    
    // 連接到WebSocket
    connectSocket(data.conferenceId);
    
  } catch (error) {
    console.error("會議創建時發生錯誤:", error);
    setError(error.message);
  } finally {
    setIsLoading(false);
  }
}; 