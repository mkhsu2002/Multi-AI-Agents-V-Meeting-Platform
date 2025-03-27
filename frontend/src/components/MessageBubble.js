import React from 'react';
import PigAvatar from './PigAvatar';

const MessageBubble = ({ 
  speaker, 
  title, 
  text, 
  isActive, 
  timestamp 
}) => {
  return (
    <div className="flex items-start gap-3">
      <div className="flex-shrink-0">
        <PigAvatar 
          name={speaker}
          title={title}
          isActive={isActive}
          size="md"
        />
      </div>
      <div className="flex-grow">
        <div className="flex items-baseline mb-1">
          <span className="font-semibold mr-2">{speaker}</span>
          <span className="text-xs text-gray-500">{title}</span>
          <span className="text-xs text-gray-400 ml-auto">{timestamp}</span>
        </div>
        <div className="speech-bubble">
          <p className="whitespace-pre-line">{text}</p>
        </div>
      </div>
    </div>
  );
};

export default MessageBubble; 