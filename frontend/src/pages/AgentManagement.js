import React, { useState, useEffect } from 'react';
import { DEFAULT_ROLES } from '../config/agents';

// 作為備份的默認角色，以防 import 失敗
const BACKUP_DEFAULT_ROLES = [
  {
    id: "General manager",
    name: "豬霸天",
    title: "總經理",
    personality: "果斷、有遠見、領導力強",
    expertise: "策略規劃與決策",
    temperature: 0.7,
    isActive: true,
    rolePrompt: "你是一位果斷有魄力的企業總經理，帶領著團隊朝著目標前進。你擅長制定戰略規劃，做出明智的決策，並確保團隊朝著正確的方向發展。在會議中，你應該展現出明確的方向感和權威性，同時鼓勵其他成員發表意見。"
  },
  {
    id: "Secretary",
    name: "豬秘書",
    title: "秘書",
    personality: "組織、負責、高效",
    expertise: "會議記錄與資訊整理",
    temperature: 0.3,
    isActive: true,
    rolePrompt: "你是一位高效組織的秘書，負責記錄會議內容並整理各種資訊。你應該保持專業和客觀，專注於捕捉所有重要討論點，並將它們組織成清晰、結構化的格式。在會議中，你應該主要關注記錄和整理資訊，而不是提出自己的意見，除非被特別要求。"
  }
];

// 用於通知 App.js 智能體數據已更改的函數
const notifyAgentDataChange = (agents) => {
  const event = new CustomEvent('agentDataChanged', { detail: agents });
  window.dispatchEvent(event);
};

const AgentManagement = () => {
  const [agents, setAgents] = useState([]);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [currentAgent, setCurrentAgent] = useState(null);
  const [newAgent, setNewAgent] = useState({
    id: '',
    name: '',
    title: '',
    personality: '',
    expertise: '',
    temperature: 0.5,
    isActive: true,
    rolePrompt: ''
  });
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [notification, setNotification] = useState({ show: false, message: '', type: '' });
  const [tempFileContent, setTempFileContent] = useState('');
  const [showImportForm, setShowImportForm] = useState(false);

  // 加載保存的智能體或使用默認值
  useEffect(() => {
    try {
      const savedAgents = localStorage.getItem('agents');
      if (savedAgents) {
        setAgents(JSON.parse(savedAgents));
      } else {
        // 嘗試使用 import 的默認角色，如果失敗則使用備份
        try {
          setAgents(DEFAULT_ROLES.map(role => ({
            ...role,
            temperature: role.temperature || 0.5,
            isActive: role.isActive !== undefined ? role.isActive : true
          })));
        } catch (error) {
          console.error('Error loading DEFAULT_ROLES, using backup:', error);
          setAgents(BACKUP_DEFAULT_ROLES);
        }
      }
    } catch (error) {
      console.error('Error loading agent data:', error);
      setAgents(BACKUP_DEFAULT_ROLES);
    }
  }, []);

  // 當 agents 變更時保存到 localStorage
  useEffect(() => {
    if (agents.length > 0) {
      localStorage.setItem('agents', JSON.stringify(agents));
      // 通知 App.js 更新
      notifyAgentDataChange(agents);
    }
  }, [agents]);

  // 顯示通知
  const showNotification = (message, type = 'success') => {
    setNotification({ show: true, message, type });
    setTimeout(() => setNotification({ show: false, message: '', type: '' }), 3000);
  };

  // 處理智能體字段變更
  const handleInputChange = (e, agent) => {
    const { name, value, type, checked } = e.target;
    const newValue = type === 'checkbox' ? checked : 
                    name === 'temperature' ? parseFloat(value) : value;
    
    if (agent === 'new') {
      setNewAgent({ ...newAgent, [name]: newValue });
    } else {
      setCurrentAgent({ ...currentAgent, [name]: newValue });
    }
  };

  // 打開編輯表單
  const openEditForm = (agent) => {
    setCurrentAgent({ ...agent });
    setShowEditForm(true);
    setShowAddForm(false);
    setShowImportForm(false);
  };

  // 打開添加表單
  const openAddForm = () => {
    setNewAgent({
      id: generateUniqueId(),
      name: '',
      title: '',
      personality: '',
      expertise: '',
      temperature: 0.5,
      isActive: true,
      rolePrompt: ''
    });
    setShowAddForm(true);
    setShowEditForm(false);
    setShowImportForm(false);
  };

  // 打開導入表單
  const openImportForm = () => {
    setTempFileContent('');
    setShowImportForm(true);
    setShowAddForm(false);
    setShowEditForm(false);
  };

  // 生成唯一ID
  const generateUniqueId = () => {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
  };

  // 保存編輯的智能體
  const saveEditedAgent = () => {
    if (!currentAgent.name || !currentAgent.id) {
      alert('名稱和 ID 是必填項！');
      return;
    }

    setAgents(agents.map(agent => 
      agent.id === currentAgent.id ? currentAgent : agent
    ));
    setShowEditForm(false);
    showNotification(`智能體 ${currentAgent.name} 已更新`);
  };

  // 添加新智能體
  const addNewAgent = () => {
    if (!newAgent.name || !newAgent.id) {
      alert('名稱和 ID 是必填項！');
      return;
    }

    if (agents.some(agent => agent.id === newAgent.id)) {
      alert('ID 已存在！請使用不同的 ID');
      return;
    }

    setAgents([...agents, newAgent]);
    setShowAddForm(false);
    showNotification(`新智能體 ${newAgent.name} 已添加`);
  };

  // 刪除智能體
  const deleteAgent = (id) => {
    if (window.confirm('確定要刪除此智能體嗎？')) {
      const agentToDelete = agents.find(agent => agent.id === id);
      setAgents(agents.filter(agent => agent.id !== id));
      showNotification(`智能體 ${agentToDelete.name} 已刪除`, 'warning');
    }
  };

  // 恢復默認智能體
  const resetToDefaults = () => {
    if (window.confirm('確定要重置為默認智能體嗎？這將刪除所有自定義智能體！')) {
      try {
        setAgents(DEFAULT_ROLES.map(role => ({
          ...role,
          temperature: role.temperature || 0.5,
          isActive: role.isActive !== undefined ? role.isActive : true
        })));
      } catch (error) {
        console.error('Error resetting to DEFAULT_ROLES, using backup:', error);
        setAgents(BACKUP_DEFAULT_ROLES);
      }
      showNotification('已重置為默認智能體', 'info');
    }
  };

  // 導出智能體配置
  const exportAgents = () => {
    const agentsToExport = selectedAgents.length > 0 
      ? agents.filter(agent => selectedAgents.includes(agent.id))
      : agents;
    
    const dataStr = JSON.stringify(agentsToExport, null, 2);
    const dataUri = `data:application/json;charset=utf-8,${encodeURIComponent(dataStr)}`;
    
    const exportFileDefaultName = `fly_pig_agents_${new Date().toISOString().slice(0, 10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    showNotification(`已導出 ${agentsToExport.length} 個智能體`);
  };

  // 處理智能體導入
  const handleImport = () => {
    try {
      const importedAgents = JSON.parse(tempFileContent);
      
      // 驗證導入的數據
      if (!Array.isArray(importedAgents)) {
        throw new Error('導入的文件格式不正確，應為 JSON 數組');
      }
      
      const validAgents = importedAgents.filter(agent => 
        agent && agent.id && agent.name && 
        typeof agent.id === 'string' && 
        typeof agent.name === 'string'
      );
      
      if (validAgents.length === 0) {
        throw new Error('導入的文件中沒有有效的智能體');
      }
      
      // 確保所有必要的字段都存在
      const processedAgents = validAgents.map(agent => ({
        id: agent.id,
        name: agent.name,
        title: agent.title || '',
        personality: agent.personality || '',
        expertise: agent.expertise || '',
        temperature: typeof agent.temperature === 'number' ? agent.temperature : 0.5,
        isActive: agent.isActive !== undefined ? agent.isActive : true,
        rolePrompt: agent.rolePrompt || ''
      }));
      
      setAgents(processedAgents);
      setShowImportForm(false);
      showNotification(`成功導入 ${processedAgents.length} 個智能體`);
    } catch (error) {
      alert(`導入失敗: ${error.message}`);
    }
  };

  // 處理檔案上傳
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      setTempFileContent(event.target.result);
    };
    reader.readAsText(file);
  };

  // 處理智能體選擇
  const handleAgentSelection = (id) => {
    setSelectedAgents(prev => 
      prev.includes(id) 
        ? prev.filter(agentId => agentId !== id) 
        : [...prev, id]
    );
  };

  // 處理全選/全不選
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedAgents(agents.map(agent => agent.id));
    } else {
      setSelectedAgents([]);
    }
  };

  // 截斷文本，用於表格顯示
  const truncateText = (text, maxLength = 50) => {
    if (!text) return '';
    return text.length > maxLength ? `${text.substring(0, maxLength)}...` : text;
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">智能體管理</h1>
      
      {/* 操作按鈕 */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button 
          onClick={openAddForm}
          className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
        >
          添加智能體
        </button>
        <button 
          onClick={resetToDefaults}
          className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600"
        >
          重置為默認
        </button>
        <button 
          onClick={exportAgents}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
          disabled={agents.length === 0}
        >
          {selectedAgents.length > 0 ? `導出所選 (${selectedAgents.length})` : '導出全部'}
        </button>
        <button 
          onClick={openImportForm}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          導入智能體
        </button>
      </div>
      
      {/* 通知 */}
      {notification.show && (
        <div className={`p-2 mb-4 rounded ${
          notification.type === 'success' ? 'bg-green-100 text-green-800' :
          notification.type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
          notification.type === 'error' ? 'bg-red-100 text-red-800' :
          'bg-blue-100 text-blue-800'
        }`}>
          {notification.message}
        </div>
      )}
      
      {/* 智能體列表 */}
      {agents.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="min-w-full bg-white border border-gray-200">
            <thead>
              <tr className="bg-gray-100">
                <th className="border p-2">
                  <input 
                    type="checkbox" 
                    onChange={handleSelectAll} 
                    checked={selectedAgents.length === agents.length && agents.length > 0}
                  />
                </th>
                <th className="border p-2">ID</th>
                <th className="border p-2">名稱</th>
                <th className="border p-2">職稱</th>
                <th className="border p-2">個性</th>
                <th className="border p-2">專長</th>
                <th className="border p-2">溫度</th>
                <th className="border p-2">啟用</th>
                <th className="border p-2">提示詞</th>
                <th className="border p-2">操作</th>
              </tr>
            </thead>
            <tbody>
              {agents.map(agent => (
                <tr key={agent.id} className="hover:bg-gray-50">
                  <td className="border p-2">
                    <input 
                      type="checkbox" 
                      onChange={() => handleAgentSelection(agent.id)} 
                      checked={selectedAgents.includes(agent.id)}
                    />
                  </td>
                  <td className="border p-2">{agent.id}</td>
                  <td className="border p-2">{agent.name}</td>
                  <td className="border p-2">{agent.title}</td>
                  <td className="border p-2">{truncateText(agent.personality)}</td>
                  <td className="border p-2">{truncateText(agent.expertise)}</td>
                  <td className="border p-2">{agent.temperature}</td>
                  <td className="border p-2">{agent.isActive ? '✅' : '❌'}</td>
                  <td className="border p-2" title={agent.rolePrompt}>
                    {truncateText(agent.rolePrompt, 30)}
                  </td>
                  <td className="border p-2">
                    <button 
                      onClick={() => openEditForm(agent)}
                      className="px-2 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 mr-1"
                    >
                      編輯
                    </button>
                    <button 
                      onClick={() => deleteAgent(agent.id)}
                      className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                    >
                      刪除
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="text-center p-4 bg-gray-100">
          沒有找到智能體數據。請添加新智能體或重置為默認值。
        </div>
      )}
      
      {/* 編輯表單 */}
      {showEditForm && currentAgent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">編輯智能體</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block mb-1">ID</label>
                <input
                  type="text"
                  name="id"
                  value={currentAgent.id}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full p-2 border rounded"
                  disabled
                />
              </div>
              <div>
                <label className="block mb-1">名稱 *</label>
                <input
                  type="text"
                  name="name"
                  value={currentAgent.name}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full p-2 border rounded"
                  required
                />
              </div>
              <div>
                <label className="block mb-1">職稱</label>
                <input
                  type="text"
                  name="title"
                  value={currentAgent.title}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full p-2 border rounded"
                />
              </div>
              <div>
                <label className="block mb-1">溫度 (0.0-1.0)</label>
                <input
                  type="range"
                  name="temperature"
                  min="0"
                  max="1"
                  step="0.1"
                  value={currentAgent.temperature}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full"
                />
                <div className="text-center">{currentAgent.temperature}</div>
              </div>
              <div>
                <label className="block mb-1">個性特點</label>
                <input
                  type="text"
                  name="personality"
                  value={currentAgent.personality}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full p-2 border rounded"
                  placeholder="例如：果斷、有遠見、領導力強"
                />
              </div>
              <div>
                <label className="block mb-1">專業領域</label>
                <input
                  type="text"
                  name="expertise"
                  value={currentAgent.expertise}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full p-2 border rounded"
                  placeholder="例如：策略規劃與決策"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block mb-1">
                  角色提示詞
                  <span className="text-xs text-gray-500 ml-2">（影響 AI 回應風格和角色特質）</span>
                </label>
                <textarea
                  name="rolePrompt"
                  value={currentAgent.rolePrompt}
                  onChange={(e) => handleInputChange(e, 'edit')}
                  className="w-full p-2 border rounded"
                  rows="4"
                  placeholder="描述此角色應該如何表現自己，包括說話風格、專業領域、性格特點等"
                ></textarea>
              </div>
              <div className="md:col-span-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="isActive"
                    checked={currentAgent.isActive}
                    onChange={(e) => handleInputChange(e, 'edit')}
                    className="mr-2"
                  />
                  啟用此智能體
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowEditForm(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                取消
              </button>
              <button
                onClick={saveEditedAgent}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
              >
                保存
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 添加表單 */}
      {showAddForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-3xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">添加新智能體</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block mb-1">ID *</label>
                <input
                  type="text"
                  name="id"
                  value={newAgent.id}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full p-2 border rounded"
                  required
                />
                <div className="text-xs text-gray-500">用於系統識別，建議使用英文</div>
              </div>
              <div>
                <label className="block mb-1">名稱 *</label>
                <input
                  type="text"
                  name="name"
                  value={newAgent.name}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full p-2 border rounded"
                  required
                />
              </div>
              <div>
                <label className="block mb-1">職稱</label>
                <input
                  type="text"
                  name="title"
                  value={newAgent.title}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full p-2 border rounded"
                />
              </div>
              <div>
                <label className="block mb-1">溫度 (0.0-1.0)</label>
                <input
                  type="range"
                  name="temperature"
                  min="0"
                  max="1"
                  step="0.1"
                  value={newAgent.temperature}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full"
                />
                <div className="text-center">{newAgent.temperature}</div>
              </div>
              <div>
                <label className="block mb-1">個性特點</label>
                <input
                  type="text"
                  name="personality"
                  value={newAgent.personality}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full p-2 border rounded"
                  placeholder="例如：果斷、有遠見、領導力強"
                />
              </div>
              <div>
                <label className="block mb-1">專業領域</label>
                <input
                  type="text"
                  name="expertise"
                  value={newAgent.expertise}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full p-2 border rounded"
                  placeholder="例如：策略規劃與決策"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block mb-1">
                  角色提示詞
                  <span className="text-xs text-gray-500 ml-2">（影響 AI 回應風格和角色特質）</span>
                </label>
                <textarea
                  name="rolePrompt"
                  value={newAgent.rolePrompt}
                  onChange={(e) => handleInputChange(e, 'new')}
                  className="w-full p-2 border rounded"
                  rows="4"
                  placeholder="描述此角色應該如何表現自己，包括說話風格、專業領域、性格特點等"
                ></textarea>
              </div>
              <div className="md:col-span-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    name="isActive"
                    checked={newAgent.isActive}
                    onChange={(e) => handleInputChange(e, 'new')}
                    className="mr-2"
                  />
                  啟用此智能體
                </label>
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                取消
              </button>
              <button
                onClick={addNewAgent}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
              >
                添加
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 導入表單 */}
      {showImportForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg w-full max-w-2xl">
            <h2 className="text-xl font-bold mb-4">導入智能體</h2>
            <div className="mb-4">
              <p className="text-sm text-gray-600 mb-2">
                選擇一個 JSON 文件導入智能體。文件應包含智能體對象數組，每個對象至少需要 id 和 name 字段。
              </p>
              <input
                type="file"
                accept=".json"
                onChange={handleFileUpload}
                className="w-full p-2 border rounded"
              />
            </div>
            {tempFileContent && (
              <div className="mb-4">
                <label className="block mb-1">文件內容預覽</label>
                <textarea
                  value={tempFileContent}
                  onChange={(e) => setTempFileContent(e.target.value)}
                  className="w-full p-2 border rounded"
                  rows="8"
                ></textarea>
              </div>
            )}
            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowImportForm(false)}
                className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600"
              >
                取消
              </button>
              <button
                onClick={handleImport}
                className="px-4 py-2 bg-primary text-white rounded hover:bg-primary-dark"
                disabled={!tempFileContent}
              >
                導入
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 說明區域 */}
      <div className="mt-8 p-4 bg-gray-100 rounded">
        <h2 className="text-xl font-bold mb-2">如何使用智能體管理</h2>
        <ol className="list-decimal ml-5 space-y-2">
          <li><strong>編輯現有智能體</strong>：點擊智能體右側的「編輯」按鈕修改其屬性。</li>
          <li><strong>添加新智能體</strong>：點擊頂部的「添加智能體」按鈕創建新的智能體。</li>
          <li><strong>刪除智能體</strong>：點擊智能體右側的「刪除」按鈕移除不需要的智能體。</li>
          <li><strong>批量操作</strong>：使用左側的複選框選擇多個智能體進行導出。</li>
          <li><strong>導出配置</strong>：點擊「導出全部」或「導出所選」將智能體配置保存為 JSON 文件。</li>
          <li><strong>導入配置</strong>：點擊「導入智能體」上傳之前導出的 JSON 文件。</li>
          <li><strong>重置智能體</strong>：點擊「重置為默認」恢復系統預設的智能體配置。</li>
        </ol>
        <div className="mt-4">
          <p className="text-sm text-gray-600">
            <strong>提示詞說明</strong>：提示詞用於指導 AI 如何扮演智能體角色，影響其回應風格和專業表現。
            一個好的提示詞應該包含角色的個性特點、專業領域和表達方式，讓 AI 能更準確地模擬該角色。
          </p>
        </div>
      </div>
    </div>
  );
};

export default AgentManagement; 