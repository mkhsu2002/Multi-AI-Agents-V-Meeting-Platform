"""
研討情境模組 - 動態載入器

這個模組會自動掃描 scenarios 目錄下的所有 Python 檔案，
匯入它們，並從中提取 scenario_config 字典，
最後動態建立 DISCUSSION_SCENARIOS 字典和 SCENARIO_INFO 列表。
"""

import os
import importlib
import logging

logger = logging.getLogger(__name__)

DISCUSSION_SCENARIOS = {}
SCENARIO_INFO = []

# 定義預設情境 (從 config_scenarios.py 移過來)
DEFAULT_SCENARIO = "business_meeting"

# 定義情境選擇指導 (從 config_scenarios.py 移過來)
SCENARIO_SELECTION_GUIDE = """
根據會議目的選擇合適的情境模組：

1. 董事會議：適用於需要做出重要戰略決策、討論公司治理或長期規劃的場合
2. 商務會議：適用於討論具體業務計劃、市場策略或銷售目標的場合
3. 辯論大會：適用於需要探討具有爭議性話題，或從多角度分析復雜問題的場合
4. 腦力激盪：適用於需要產生創新想法、解決方案或新產品概念的場合
5. 創作接龍：適用於進行創意寫作、故事構建或產品概念逐步完善的場合
"""

# 定義情境模組參數說明 (從 config_scenarios.py 移過來)
SCENARIO_PARAMETERS_EXPLANATION = """
每個情境模組包含以下參數：

name: 情境的名稱
description: 情境的簡短描述
system_prompt: 提供給AI的系統提示，指導其在該情境下的行為方式
round_structure: 定義每輪討論的主要目標和重點
role_emphasis: 通過權重調整不同角色在該情境下的發言頻率和重要性
discussion_guidance: 引導如何在該情境下進行有效的討論
"""


def load_scenarios():
    """動態載入所有場景設定檔"""
    global DISCUSSION_SCENARIOS, SCENARIO_INFO
    
    scenarios_dir = os.path.dirname(__file__)
    logger.info(f"正在從目錄 {scenarios_dir} 載入場景設定...")
    
    loaded_scenarios = {}
    loaded_info = []
    
    for filename in os.listdir(scenarios_dir):
        if filename.endswith(".py") and filename != "__init__.py":
            scenario_id = filename[:-3] # 去掉 .py 副檔名作為 ID
            module_name = f".{scenario_id}" # 相對導入路徑
            
            try:
                # 使用相對導入從當前包導入模組
                module = importlib.import_module(module_name, package=__package__)
                
                # 檢查模組是否包含 scenario_config 變數
                if hasattr(module, 'scenario_config') and isinstance(module.scenario_config, dict):
                    config = module.scenario_config
                    loaded_scenarios[scenario_id] = config
                    
                    # 添加到 SCENARIO_INFO 列表
                    loaded_info.append({
                        "id": scenario_id,
                        "name": config.get("name", scenario_id), # 如果沒有 name，使用 ID
                        "description": config.get("description", "")
                    })
                    logger.info(f"成功載入場景: {scenario_id}")
                else:
                    logger.warning(f"場景文件 {filename} 未包含有效的 'scenario_config' 字典。")
                    
            except ImportError as e:
                logger.error(f"無法導入場景文件 {filename}: {e}")
            except Exception as e:
                logger.error(f"載入場景文件 {filename} 時發生錯誤: {e}")
                logger.exception(f"載入 {filename} 異常詳情")

    # 確保預設情境存在
    if DEFAULT_SCENARIO not in loaded_scenarios:
        logger.error(f"預設情境 '{DEFAULT_SCENARIO}' 未成功載入！請檢查對應的設定檔。")
        # 可以選擇拋出錯誤或使用第一個載入的作為預設
        if loaded_scenarios:
            fallback_default = list(loaded_scenarios.keys())[0]
            logger.warning(f"將使用第一個載入的情境 '{fallback_default}' 作為備用預設情境。")
            # 如果需要，可以更新 DEFAULT_SCENARIO 變數
            # global DEFAULT_SCENARIO
            # DEFAULT_SCENARIO = fallback_default
        else:
            logger.critical("沒有載入任何情境！無法繼續。")
            # 可能需要拋出異常阻止應用啟動
            # raise RuntimeError("無法載入任何研討情境模組")

    DISCUSSION_SCENARIOS = loaded_scenarios
    SCENARIO_INFO = loaded_info
    logger.info(f"成功載入 {len(DISCUSSION_SCENARIOS)} 個研討情境模組。")

# 在模組首次被導入時執行載入邏輯
load_scenarios()

# 允許外部直接導入這些變數
__all__ = [
    "DISCUSSION_SCENARIOS",
    "SCENARIO_INFO",
    "DEFAULT_SCENARIO",
    "SCENARIO_SELECTION_GUIDE",
    "SCENARIO_PARAMETERS_EXPLANATION"
] 