import React from 'react';
import {
  Box, Text, Checkbox, VStack, HStack, IconButton, Tooltip
} from '@chakra-ui/react';
import { EditIcon } from '@chakra-ui/icons';

const AgentSelector = ({ allAgents, onAgentsChange, onEditAgent }) => {

  const handleCheckboxChange = (agentId) => {
    const updatedAgents = allAgents.map(agent => 
      agent.id === agentId ? { ...agent, isActive: !agent.isActive } : agent
    );
    onAgentsChange(updatedAgents);
  };

  return (
    <Box borderWidth="1px" borderRadius="lg" p={4}>
      <Text fontWeight="bold" mb={3}>選擇參會智能體:</Text>
      <VStack align="stretch" spacing={3}>
        {/* 確保 allAgents 是數組 */}
        {Array.isArray(allAgents) && allAgents.length > 0 ? (
          allAgents.map(agent => (
            <HStack key={agent.id} justify="space-between">
              <Checkbox 
                isChecked={agent.isActive ?? true} // 提供默認值
                onChange={() => handleCheckboxChange(agent.id)}
                isDisabled={agent.id === 'Secretary'} // 秘書始終啟用
              >
                {agent.name} ({agent.title})
              </Checkbox>
              <Tooltip label="編輯此智能體屬性">
                <IconButton 
                  aria-label="Edit agent" 
                  icon={<EditIcon />} 
                  size="sm"
                  variant="ghost"
                  onClick={() => onEditAgent(agent)}
                />
              </Tooltip>
            </HStack>
          ))
        ) : (
          <Text color="gray.500">沒有找到可用的智能體。請前往「智能體管理」頁面添加或重置。</Text>
        )}
      </VStack>
    </Box>
  );
};

export default AgentSelector; 