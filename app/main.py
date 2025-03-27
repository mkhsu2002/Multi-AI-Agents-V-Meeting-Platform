def get_openai_client():
    if not openai_api_key:
        return None
    try:
        # 直接創建客戶端，不使用可能引起錯誤的參數
        client = openai.OpenAI(api_key=openai_api_key)
        logger.info("成功創建 OpenAI 客戶端")
        return client
    except TypeError as te:
        # 處理參數錯誤
        logger.warning(f"創建OpenAI客戶端時遇到參數錯誤: {str(te)}，嘗試簡化參數")
        try:
            # 使用最簡單的參數
            openai.api_key = openai_api_key
            logger.info("成功使用全局設置配置 OpenAI")
            return openai
        except Exception as e2:
            logger.error(f"使用全局設置配置OpenAI失敗: {str(e2)}")
            return None
    except Exception as e:
        logger.error(f"創建OpenAI客戶端失敗: {str(e)}")
        try:
            # 備用方式：使用全局設置
            openai.api_key = openai_api_key
            return openai
        except Exception as e2:
            logger.error(f"無法創建OpenAI客戶端: {str(e2)}")
            return None 