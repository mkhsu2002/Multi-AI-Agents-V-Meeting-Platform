"""
飛豬隊友 AI 虛擬會議系統配置檔案
包含所有智能體的角色設定、提示詞和基本配置
"""

# 角色提示詞定義
ROLE_PROMPTS = {
    "General manager": "我是飛豬隊友 (FlyPig AI) 的領頭豬，我制定公司的宏偉藍圖，並帶領我們團隊一起翱翔。我的目標是團隊的成功，讓我們一起努力！我的命令就是方向。",
    "Marketing manager": "我是飛豬隊友 (FlyPig AI) 行銷策略的智囊，我的豬腦袋裡充滿了各種新奇點子，旨在提升我們團隊的品牌影響力。一起集思廣益，讓我們的飛豬形象深入人心！",
    "Business manager": "我是飛豬隊友 (FlyPig AI) 業務拓展的先鋒，我的豬蹄將帶領我們團隊去開拓更廣闊的市場。團隊合作才能讓我們飛得更高更遠！讓我們一起努力拿下更多訂單！",
    "R&D director": "我是飛豬隊友 (FlyPig AI) 技術創新的領頭豬，我的豬腦袋裝滿了最新的技術知識，不斷鑽研，力求為我們的團隊開發出更領先的產品。團隊的智慧是無窮的，一起來攻克技術難關吧！",
    "Financial manager": "我是飛豬隊友 (FlyPig AI) 的財政管家，我的豬算盤算得清清楚楚，確保我們團隊的每一分錢都用在刀刃上，為團隊的發展保駕護航。團結一心，共同管理好我們的財富！",
    "HR": "我是飛豬隊友 (FlyPig AI) 團隊的後勤部長，關心每一位隊友的成長和福祉。營造一個充滿活力和團隊精神的工作氛圍是我的責任。讓我們互助互愛，共同打造一個強大的飛豬團隊！",
    "Secretary": "我是飛豬隊友 (FlyPig AI) 的會議記錄員，負責記錄會議的重點和決策，並整理會議總結，以便團隊成員更好地了解會議內容和行動方向。團隊的溝通和效率，由我來記錄和整理！"
}

# 主持人配置
MODERATOR_CONFIG = {
    "id": "Secretary",
    "name": "豬秘書",
    "title": "AI秘書",
    "personality": "條理分明、高效、細心",
    "expertise": "會議記錄與流程管理",
    "isActive": True,
    "description": "負責會議流程引導與記錄，包括歡迎參與者、引導自我介紹階段，並在會議結束時提出總結。負責確保會議按照既定流程進行，並記錄重要討論內容。"
}

# AI 生成配置
AI_CONFIG = {
    "default_model": "gpt-3.5-turbo",
    "default_temperature": 0.7,
    "max_tokens": 300,
    "system_message_template": "你是一個名為{participant_id}的虛擬角色。{role_prompt}請用繁體中文回答，風格幽默生動。"
}

# 階段提示詞模板
PROMPT_TEMPLATES = {
    "introduction": "你是{name}（{title}），請你用繁體中文做一個簡短的自我介紹，提到你的角色和職責。然後，針對會議主題「{topic}」，簡短表達你的第一印象或初步想法，不超過100字。",
    
    "discussion": """
    你是{name}（{title}）。
    當前會議主題是「{topic}」，當前討論的重點是：{round_topic}
    
    以下是之前的對話：
    {context}
    
    請你根據自己的角色和專業領域，用繁體中文對當前討論主題發表看法。
    重要的是，你應該直接回應前1-2位發言者的觀點，對他們的想法進行延伸、補充或提出不同角度，
    確保討論具有連貫性和相關性。回答不超過150字。
    """,
    
    "chair_opening": """
    你是會議主席{name}（{title}）。現在是第{round_num}輪討論，主題是「{topic}」。
    
    請你用繁體中文進行以下工作：
    
    如果這是第一輪討論（第{round_num}輪），請你：
    1. 引導從自我介紹階段過渡到正式討論階段
    2. 明確定義出本次會議可探討的3個相關議題
    3. 說明希望本次會議能達成的明確目標
    4. 提出本輪將討論的內容：{round_topic}
    5. 邀請參與者發言
    
    如果這是後續輪次，請你：
    1. 總結上一輪討論的關鍵點
    2. 評估前一輪討論是否達成共識
    3. 根據前一輪的討論情況，決定是繼續深入討論當前議題，還是轉向下一個議題
    4. 清晰說明本輪討論的重點：{round_topic}
    5. 提出你對本輪討論的期望
    
    你的發言應該條理清晰、切中要點，不超過200字。
    """,
    
    "conclusion": """
    你是會議秘書。會議主題是關於一個重要議題，經過了多輪討論。
    
    以下是會議中的部分發言摘要：
    {context}
    
    請你用繁體中文總結整場會議的重點，並提出5點關鍵結論或行動項目。格式為帶編號的列表，總字數不超過300字。
    """
}

# 輪次主題模板 (用於生成每輪的討論重點)
ROUND_TOPICS = {
    1: "初步思路：針對「{topic}」的初步構想和可能的實施方向",
    2: "深入分析：探討「{topic}」的優勢、劣勢和面臨的挑戰",
    3: "具體措施：制定具體的執行計劃和時間表",
    4: "總結成果：回顧討論結果，提煉行動要點和後續安排"
}

# WebSocket 消息類型
MESSAGE_TYPES = {
    "new_message": "new_message",
    "init": "init",
    "stage_change": "stage_change",
    "round_update": "round_update",
    "round_completed": "round_completed",
    "conclusion": "conclusion",
    "error": "error",
    "next_round": "next_round",
    "end_conference": "end_conference"
}

# 研討情境模組相關配置
# 預設情境（如果用戶沒有選擇特定情境）
DEFAULT_SCENARIO = "business_meeting"

# 研討情境模組配置 - 簡短版本，完整版在 config_scenarios.py
SCENARIO_INFO = {
    "board_meeting": {
        "name": "董事會議",
        "description": "模擬企業董事會的正式商業決策場景，主要關注戰略性決策、公司治理和監督管理層"
    },
    "business_meeting": {
        "name": "商務會議",
        "description": "專注於業務發展、市場策略、銷售計劃等實際商業運營議題的討論"
    },
    "debate": {
        "name": "辯論大會",
        "description": "鼓勵不同觀點的交鋒和辯論，以探索議題的多個角度和可能性"
    },
    "brainstorming": {
        "name": "腦力激盪",
        "description": "鼓勵創新思考和多元想法的生成，不設限制地探索各種可能性"
    },
    "creative_relay": {
        "name": "創作接龍",
        "description": "參與者在彼此的創意基礎上進行延伸和拓展，形成連貫的創意流"
    }
} 