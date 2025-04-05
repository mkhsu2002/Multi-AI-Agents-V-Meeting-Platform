import React from 'react';
import {
  Modal, ModalOverlay, ModalContent, ModalHeader, ModalFooter, ModalBody, ModalCloseButton,
  Button, FormControl, FormLabel, Input, Textarea, NumberInput, NumberInputField, NumberInputStepper, NumberIncrementStepper, NumberDecrementStepper, Checkbox, VStack
} from '@chakra-ui/react';

const AgentEditModal = ({ isOpen, onClose, agent, onSave }) => {
  const [editedAgent, setEditedAgent] = React.useState(agent);

  // Update local state when the agent prop changes
  React.useEffect(() => {
    setEditedAgent(agent);
  }, [agent]);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setEditedAgent(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleNumberChange = (valueAsString, valueAsNumber, name) => {
     // Ensure value is within range [0, 1] and handle potential NaN
     const clampedValue = Math.max(0, Math.min(1, valueAsNumber));
     setEditedAgent(prev => ({ ...prev, [name]: isNaN(clampedValue) ? 0.5 : clampedValue }));
  };


  const handleSave = () => {
    // Ensure temperature is a number before saving
    const agentToSave = {
        ...editedAgent,
        temperature: Number(editedAgent.temperature ?? 0.5) 
    };
    onSave(agentToSave);
    onClose(); // Close modal after saving
  };

  // Ensure agent exists before rendering form
  if (!editedAgent) {
    return null;
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} size="xl" isCentered>
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>編輯智能體: {agent?.name}</ModalHeader>
        <ModalCloseButton />
        <ModalBody pb={6}>
          <VStack spacing={4} align="stretch">
            <FormControl isRequired>
              <FormLabel>名稱</FormLabel>
              <Input name="name" value={editedAgent.name || ''} onChange={handleChange} />
            </FormControl>
            <FormControl>
              <FormLabel>職稱</FormLabel>
              <Input name="title" value={editedAgent.title || ''} onChange={handleChange} />
            </FormControl>
            <FormControl>
                {/* Displaying the current value next to the label */}
                <FormLabel>溫度 ({Number(editedAgent.temperature ?? 0.5).toFixed(1)})</FormLabel>
                <NumberInput
                    name="temperature"
                    value={editedAgent.temperature ?? 0.5} // Use ?? for default value
                    min={0}
                    max={1}
                    step={0.1}
                    onChange={(valueAsString, valueAsNumber) => handleNumberChange(valueAsString, valueAsNumber, 'temperature')}
                    precision={1} // Ensure one decimal place
                 >
                    <NumberInputField />
                    <NumberInputStepper>
                        <NumberIncrementStepper />
                        <NumberDecrementStepper />
                    </NumberInputStepper>
                </NumberInput>
            </FormControl>
            <FormControl>
              <FormLabel>個性特點</FormLabel>
              <Input name="personality" value={editedAgent.personality || ''} onChange={handleChange} placeholder="例如：果斷、有遠見" />
            </FormControl>
             <FormControl>
              <FormLabel>專業領域</FormLabel>
              <Input name="expertise" value={editedAgent.expertise || ''} onChange={handleChange} placeholder="例如：策略規劃與決策" />
            </FormControl>
            <FormControl>
              <FormLabel>角色提示詞</FormLabel>
              <Textarea name="rolePrompt" value={editedAgent.rolePrompt || ''} onChange={handleChange} rows={5} placeholder="描述此角色應如何表現自己..." />
            </FormControl>
             <FormControl>
               <Checkbox name="isActive" isChecked={editedAgent.isActive ?? true} onChange={handleChange}>
                 啟用此智能體 (參與會議)
               </Checkbox>
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button colorScheme='blue' mr={3} onClick={handleSave}>
            保存
          </Button>
          <Button variant='ghost' onClick={onClose}>取消</Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
};

export default AgentEditModal; 