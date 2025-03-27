import React from 'react';

const PigAvatar = ({ name, title, isActive, size = 'md' }) => {
  // 根據大小設定不同的樣式
  const sizeClasses = {
    sm: 'w-12 h-12 text-sm',
    md: 'w-16 h-16 text-base',
    lg: 'w-24 h-24 text-xl'
  };
  
  // 獲取名稱首字
  const getInitials = (name) => {
    return name.charAt(0);
  };
  
  // 根據名稱選擇背景顏色
  const getBackgroundColor = (name) => {
    const colors = [
      'bg-red-400', 'bg-pink-400', 'bg-purple-400', 'bg-indigo-400', 
      'bg-blue-400', 'bg-green-400', 'bg-yellow-400', 'bg-orange-400'
    ];
    
    // 使用名稱的字符ASCII碼總和作為索引選擇顏色
    const sum = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[sum % colors.length];
  };
  
  // 構建CSS類名
  const classes = `pig-avatar rounded-full ${sizeClasses[size]} ${getBackgroundColor(name)} 
    flex items-center justify-center text-white font-bold 
    ${isActive ? 'pig-speaking' : ''} border-2 border-primary`;

  return (
    <div className="flex flex-col items-center">
      <div className={classes}>
        {getInitials(name)}
      </div>
      {title && size === 'lg' && (
        <div className="mt-2 text-center">
          <p className="font-bold text-sm">{name}</p>
          <p className="text-gray-500 text-xs">{title}</p>
        </div>
      )}
    </div>
  );
};

export default PigAvatar; 