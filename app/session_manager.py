import redis
import json
import datetime
import logging
from typing import Dict, Any, Optional, List

logging.basicConfig(level=logging.INFO)

class SessionManager:
    def __init__(self, redis_url: str, ttl: int = 3600):
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl  # 会话过期时间(秒)
    
    def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取或创建会话"""
        session_data = self.redis.get(f"session:{session_id}")
        
        if session_data:
            return json.loads(session_data)
        
        # 创建新会话
        new_session = {
            "created_at": datetime.datetime.utcnow().isoformat(),
            "updated_at": datetime.datetime.utcnow().isoformat(),
            "history": [],
            "metadata": {}
        }
        self.save_session(session_id, new_session)
        return new_session
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """保存会话"""
        session_data["updated_at"] = datetime.datetime.utcnow().isoformat()
        self.redis.set(
            f"session:{session_id}", 
            json.dumps(session_data),
            ex=self.ttl
        )
    
    def update_metadata(self, session_id: str, key: str, value: Any):
        """更新会话元数据"""
        session = self.get_session(session_id)
        session["metadata"][key] = value
        self.save_session(session_id, session)
    
    def add_to_history(self, session_id: str, query: str, response: str):
        """添加对话历史"""
        session = self.get_session(session_id)
        session["history"].append({
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "query": query,
            "response": response
        })
        self.save_session(session_id, session)
    
    def get_full_history(self, session_id: str) -> List[Dict]:
        """获取完整对话历史"""
        session = self.get_session(session_id)
        return session.get("history", [])
    
    def end_session(self, session_id: str):
        """结束会话"""
        self.redis.delete(f"session:{session_id}")

    def generate_session_summary(self, session_id: str) -> str:
        """生成会话摘要"""
        history = self.get_full_history(session_id)
        if not history:
            return ""
        
        # 构建提示
        prompt = "请为以下客服对话生成摘要，突出关键问题和解决方案：\n\n"
        for i, item in enumerate(history, 1):
            prompt += f"用户{i}: {item['query']}\n"
            prompt += f"客服{i}: {item['response']}\n\n"
        
        # 调用DeepSeek API生成摘要（这里简化，实际需要调用引擎）
        # 实际应用中，这里应该调用DeepSeekEngine的生成方法
        summary = "会话摘要功能需要DeepSeekEngine实例，这里返回示例摘要。"
        
        # 保存摘要
        self.update_metadata(session_id, "summary", summary)
        return summary