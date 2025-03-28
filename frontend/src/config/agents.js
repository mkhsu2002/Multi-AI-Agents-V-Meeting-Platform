/**
 * 飛豬隊友 AI 虛擬會議系統前端配置
 * 包含智能體參數設定和消息類型定義
 */

// 主持人配置
export const MODERATOR_CONFIG = {
  id: "moderator",
  name: "會議主持人",
  title: "AI會議助手",
  personality: "專業、公正、有條理",
  expertise: "會議協調與總結",
  isActive: true
};

// WebSocket 消息類型
export const MESSAGE_TYPES = {
  NEW_MESSAGE: "new_message",
  INIT: "init",
  STAGE_CHANGE: "stage_change",
  ROUND_UPDATE: "round_update",
  ROUND_COMPLETED: "round_completed",
  CONCLUSION: "conclusion",
  ERROR: "error",
  NEXT_ROUND: "next_round",
  END_CONFERENCE: "end_conference"
};

// 會議階段
export const CONFERENCE_STAGES = {
  WAITING: "waiting",
  INTRODUCTIONS: "introductions",
  DISCUSSION: "discussion",
  CONCLUSION: "conclusion",
  ENDED: "ended"
};

// 可用的預設角色設定
export const DEFAULT_ROLES = [
  {
    id: "Pig Boss",
    name: "領頭豬",
    title: "CEO",
    personality: "果斷、有遠見、領導力強",
    expertise: "策略規劃與決策",
    isActive: true
  },
  {
    id: "Brainy Pig",
    name: "智囊豬",
    title: "行銷總監",
    personality: "創意、開放、思維敏捷",
    expertise: "品牌策略與市場趨勢",
    isActive: true
  },
  {
    id: "Busy Pig",
    name: "業務豬",
    title: "業務拓展經理",
    personality: "外向、積極、樂觀",
    expertise: "市場開發與客戶關係",
    isActive: true
  },
  {
    id: "Professor Pig",
    name: "教授豬",
    title: "技術總監",
    personality: "邏輯、細心、求知慾強",
    expertise: "技術研發與創新",
    isActive: true
  },
  {
    id: "Calculator Pig",
    name: "計算豬",
    title: "財務長",
    personality: "精確、謹慎、細節導向",
    expertise: "財務規劃與風險控制",
    isActive: true
  },
  {
    id: "Caregiver Pig",
    name: "照顧豬",
    title: "人資總監",
    personality: "親切、體貼、善解人意",
    expertise: "團隊建設與員工關懷",
    isActive: true
  },
  {
    id: "Secretary Pig",
    name: "秘書豬",
    title: "執行秘書",
    personality: "組織、負責、高效",
    expertise: "會議記錄與資訊整理",
    isActive: true
  }
]; 