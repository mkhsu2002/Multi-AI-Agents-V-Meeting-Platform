# backend/app/scenarios/creative_relay.py

scenario_config = {
    "name": "創作接龍",
    "description": "參與者在彼此的創意基礎上進行延伸和拓展，形成連貫的創意流",
    "system_prompt": "這是一個創作接龍情境。請仔細聆聽前一位發言者的想法，並在此基礎上進行延伸和拓展。你的發言應當與前一位有明確的聯繫，同時加入新的元素或角度，讓創意不斷積累和發展。",
    "round_structure": {
        1: "創意起點：提出初始創意或故事開端",
        2: "承接發展：在前人創意基礎上進行延伸和發展",
        3: "轉折提升：引入新元素或轉折，讓創意更加豐富和完整",
        4: "收束總結：將所有創意元素進行整合，形成完整的創意或故事"
    },
    "role_emphasis": {
        "General manager": 1.0,       # 替換
        "Business manager": 1.0,       # 替換
        "Marketing manager": 1.5,     # 替換
        "Financial manager": 0.7,  # 替換
        "R&D director": 1.2,   # 替換
        "HR": 1.2    # 替換
    },
    "discussion_guidance": "在創作接龍情境中，每位參與者都應當認真聆聽前一位的發言，確保自己的發言與前一位有明確的聯繫和延續性，同時注入自己的創意和新鮮元素。"
} 