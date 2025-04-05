import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button, Select, Input, Textarea, IconButton, Tooltip, Box, Flex, Text, useToast, AlertDialog, AlertDialogBody, AlertDialogFooter, AlertDialogHeader, AlertDialogContent, AlertDialogOverlay, useDisclosure, FormControl, FormLabel, NumberInput, NumberInputField, NumberInputStepper, NumberIncrementStepper, NumberDecrementStepper } from '@chakra-ui/react';
import { DownloadIcon, ArrowUpIcon, EditIcon, DeleteIcon } from '@chakra-ui/icons';
import axios from 'axios';
import { fetchScenarios, startConference } from '../utils/api';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import AgentSelector from '../components/AgentSelector';
import AgentEditModal from '../components/modals/AgentEditModal';

const SetupPanel = ({ initialConfig, onStart }) => {
  const [config, setConfig] = useState(initialConfig);
  const [scenarios, setScenarios] = useState([]);
  const [defaultScenario, setDefaultScenario] = useState('');
  const [scenarioSelectionGuide, setScenarioSelectionGuide] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isEditingAgent, setIsEditingAgent] = useState(null);
  const navigate = useNavigate();

  const fileInputRef = useRef(null);

  const { isOpen: isDeleteDialogOpen, onOpen: onOpenDeleteDialog, onClose: onCloseDeleteDialog } = useDisclosure();
  const cancelRef = useRef();
  const [scenarioToDelete, setScenarioToDelete] = useState(null);

  const loadAgentData = () => {
    try {
      const savedAgents = localStorage.getItem('agents');
      const loadedParticipants = savedAgents ? JSON.parse(savedAgents) : [];
      const participantsWithActive = loadedParticipants.map(p => ({ 
        ...p, 
        isActive: p.isActive !== undefined ? p.isActive : true 
      }));
      setConfig(prev => ({ ...prev, participants: participantsWithActive }));
    } catch (error) {
      console.error('Failed to load agents from localStorage:', error);
      toast.error('加載智能體數據失敗');
    }
  };

  const loadScenarios = async () => {
    setIsLoading(true);
    try {
      const data = await fetchScenarios();
      setScenarios(data.scenarios);
      setDefaultScenario(data.default);
      setScenarioSelectionGuide(data.selection_guide || '');
      if (!config.scenario || !data.scenarios.find(s => s.id === config.scenario)) {
        setConfig(prev => ({
          ...prev,
          scenario: data.default
        }));
      }
    } catch (error) {
      console.error('Failed to fetch scenarios:', error);
      toast.error('加載研討模式列表失敗');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAgentData();
    loadScenarios();
    window.addEventListener('agentDataChanged', loadAgentData);
    return () => window.removeEventListener('agentDataChanged', loadAgentData);
  }, []);

  useEffect(() => {
    setConfig(prev => ({
      ...prev,
      ...initialConfig,
      participants: initialConfig.participants || prev.participants,
      scenario: initialConfig.scenario && scenarios.find(s => s.id === initialConfig.scenario) 
                 ? initialConfig.scenario 
                 : defaultScenario || prev.scenario
    }));
  }, [initialConfig, scenarios, defaultScenario]);

  const handleConfigChange = (key, value) => {
    setConfig(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleParticipantsChange = (newParticipants) => {
    setConfig(prev => ({ ...prev, participants: newParticipants }));
  };

  const handleStartConference = async () => {
    if (!config.topic?.trim()) {
      toast.warn('請輸入會議主題');
      return;
    }
    const activeParticipants = config.participants?.filter(p => p.isActive) ?? [];
    if (activeParticipants.length === 0) {
      toast.warn('請至少選擇一位活躍的智能體參與者');
      return;
    }
    setIsLoading(true);
    try {
      await onStart({ ...config, participants: activeParticipants });
    } catch (error) {
      console.error('Failed to start conference:', error);
      const errorMsg = error.response?.data?.detail || error.message || '啟動會議失敗';
      toast.error(`啟動會議失敗: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditAgent = (agentToEdit) => {
    setIsEditingAgent(agentToEdit);
  };

  const handleSaveAgent = (updatedAgent) => {
    const updatedParticipants = config.participants.map(p => 
      p.id === updatedAgent.id ? updatedAgent : p
    );
    setConfig(prev => ({ ...prev, participants: updatedParticipants }));
    localStorage.setItem('agents', JSON.stringify(updatedParticipants));
    window.dispatchEvent(new CustomEvent('agentDataChanged', { detail: updatedParticipants }));
    setIsEditingAgent(null);
    toast.success('智能體更新成功');
  };

  const handleDownloadScenario = () => {
    if (!config.scenario) {
      toast.warn('請先選擇一個研討模式');
      return;
    }
    
    const downloadUrl = `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/scenario/${config.scenario}/package`;
    
    toast.info(`準備下載模式 ${config.scenario}...`);

    const link = document.createElement('a');
    link.href = downloadUrl;
    link.style.display = 'none';
    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
  };

  const handleUploadScenario = async (event) => {
    const file = event.target.files[0];
    if (!file) {
      return;
    }

    if (!file.name.endsWith('.json')) {
      toast.error('請上傳 .json 格式的檔案');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    setIsLoading(true);
    try {
      const response = await axios.post('/api/scenario/package/upload', formData, {
        baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      if (response.data.success) {
        toast.success(response.data.message || '研討模式上傳成功！');
        await loadScenarios(); 
        if (response.data.scenario_id) {
          setConfig(prev => ({ ...prev, scenario: response.data.scenario_id }));
        }
      } else {
        toast.error(response.data.error || '研討模式上傳失敗');
      }
    } catch (error) {
      console.error('Failed to upload scenario:', error);
      const errorMsg = error.response?.data?.detail || error.response?.data?.error || error.message || '上傳失敗';
      toast.error(`研討模式上傳失敗: ${errorMsg}`);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const triggerFileUpload = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleDeleteScenarioClick = () => {
    if (config.scenario && config.scenario !== defaultScenario) {
      setScenarioToDelete(config.scenario);
      onOpenDeleteDialog();
    } else {
      toast.warn('不能刪除默認模式或未選擇模式');
    }
  };

  const confirmDeleteScenario = async () => {
    if (!scenarioToDelete) return;
    setIsLoading(true);
    try {
      await axios.delete(`/api/scenario/${scenarioToDelete}`, {
        baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
      });
      
      toast.success(`研討模式 "${scenarioToDelete}" 刪除成功！`);
      setScenarioToDelete(null);
      await loadScenarios();
      setConfig(prev => ({ ...prev, scenario: defaultScenario }));
      onCloseDeleteDialog();
    } catch (error) {
      console.error(`Failed to delete scenario ${scenarioToDelete}:`, error);
      const errorMsg = error.response?.data?.detail || error.message || '刪除失敗';
      toast.error(`刪除研討模式失敗: ${errorMsg}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box p={5}>
      <ToastContainer position="top-right" autoClose={3000} />
      <h2>會議設定</h2>
      
      <Box mb={4}>
        <FormControl isRequired>
          <FormLabel htmlFor="topic">研討主題</FormLabel>
          <Input 
            id="topic" 
            value={config.topic || ''}
            onChange={e => handleConfigChange('topic', e.target.value)}
            placeholder="輸入會議主題"
          />
        </FormControl>
      </Box>

      <Box mb={4}>
        <FormControl>
          <FormLabel htmlFor="rounds">討論回合數</FormLabel>
          <NumberInput 
            id="rounds" 
            value={config.rounds || 3} 
            min={1} 
            max={20}
            onChange={(valueAsString, valueAsNumber) => handleConfigChange('rounds', isNaN(valueAsNumber) ? 1 : valueAsNumber)}
          >
            <NumberInputField />
            <NumberInputStepper>
              <NumberIncrementStepper />
              <NumberDecrementStepper />
            </NumberInputStepper>
          </NumberInput>
        </FormControl>
      </Box>

      <Box mb={4}>
        <FormControl>
          <FormLabel htmlFor="scenario">討論模式</FormLabel>
          <Flex align="center">
            <Select 
              id="scenario"
              value={config.scenario || defaultScenario}
              onChange={e => handleConfigChange('scenario', e.target.value)}
              placeholder={isLoading ? "加載中..." : "選擇討論模式"}
              disabled={isLoading}
              mr={2}
            >
              <option value="" disabled>選擇模式...</option>
              {scenarios.map(s => (
                <option key={s.id} value={s.id}>{s.name} - {s.description}</option>
              ))}
            </Select>
            <Tooltip label="下載當前選定的模式配置">
              <IconButton 
                aria-label="Download scenario" 
                icon={<DownloadIcon />} 
                onClick={handleDownloadScenario} 
                disabled={!config.scenario}
                mr={1}
              />
            </Tooltip>
            <Tooltip label="上傳模式配置文件 (.json)">
              <IconButton 
                aria-label="Upload scenario" 
                icon={<ArrowUpIcon />} 
                onClick={triggerFileUpload} 
              />
            </Tooltip>
            <Tooltip label="刪除當前選定的模式 (默認模式不可刪除)">
              <IconButton
                aria-label="Delete scenario"
                icon={<DeleteIcon />}
                onClick={handleDeleteScenarioClick}
                colorScheme="red"
                disabled={!config.scenario || config.scenario === defaultScenario || isLoading}
              />
            </Tooltip>
            <input 
              type="file" 
              ref={fileInputRef} 
              onChange={handleUploadScenario}
              style={{ display: 'none' }} 
              accept=".json"
            />
          </Flex>
          {scenarioSelectionGuide && (
            <Text fontSize="sm" color="gray.500" mt={1}>
              提示: {scenarioSelectionGuide}
            </Text>
          )}
        </FormControl>
      </Box>
      
      <Box mb={4}>
        <AgentSelector 
          allAgents={config.participants || []} 
          onAgentsChange={handleParticipantsChange}
          onEditAgent={handleEditAgent} 
        />
      </Box>

      <Button 
        onClick={handleStartConference} 
        colorScheme="teal" 
        isLoading={isLoading}
        disabled={isLoading}
      >
        開始會議
      </Button>

      {isEditingAgent && (
        <AgentEditModal 
          isOpen={!!isEditingAgent} 
          onClose={() => setIsEditingAgent(null)} 
          agent={isEditingAgent} 
          onSave={handleSaveAgent}
        />
      )}

      <AlertDialog
        isOpen={isDeleteDialogOpen}
        leastDestructiveRef={cancelRef}
        onClose={onCloseDeleteDialog}
        isCentered
      >
        <AlertDialogOverlay>
          <AlertDialogContent>
            <AlertDialogHeader fontSize='lg' fontWeight='bold'>
              確認刪除研討模式
            </AlertDialogHeader>

            <AlertDialogBody>
              您確定要刪除模式 "{scenarioToDelete}" 嗎？此操作無法撤銷。
            </AlertDialogBody>

            <AlertDialogFooter>
              <Button ref={cancelRef} onClick={onCloseDeleteDialog}>
                取消
              </Button>
              <Button colorScheme='red' onClick={confirmDeleteScenario} ml={3} isLoading={isLoading}>
                確認刪除
              </Button>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialogOverlay>
      </AlertDialog>
    </Box>
  );
};

export default SetupPanel; 