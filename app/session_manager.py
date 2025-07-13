import redis
import json
import time
import logging
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)

class SessionManager:
    def __init__(self, redis_url: str, ttl: int = 86400):  # 默认24小时过期
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl
        logging.info(f"已连接到Redis: {redis_url}")

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """获取或创建会话"""
        session_data = self.redis.get(f"session:{session_id}")
        
        if session_data:
            return json.loads(session_data)
        
        # 创建新会话
        new_session = {
            "session_id": session_id,
            "history": [],
            "created_at": time.time()
        }
        self.save_session(session_id, new_session)
        return new_session

    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """保存会话"""
        session_data["updated_at"] = time.time()
        self.redis.set(
            f"session:{session_id}", 
            json.dumps(session_data),
            ex=self.ttl
        )

    def add_to_history(self, session_id: str, query: str, response: str):
        """添加对话历史"""
        session = self.get_session(session_id)
        session["history"].append({
            "timestamp": time.time(),
            "query": query,
            "response": response
        })
        self.save_session(session_id, session)

    def clear_history(self, session_id: str):
        """清空对话历史"""
        session = self.get_session(session_id)
        session["history"] = []
        self.save_session(session_id, session)
        
    # 可选保留的方法（如果其他地方使用）
    def update_metadata(self, session_id: str, key: str, value: Any):
        """更新会话元数据（可选）"""
        session = self.get_session(session_id)
        if "metadata" not in session:
            session["metadata"] = {}
        session["metadata"][key] = value
        self.save_session(session_id, session)
        
    def end_session(self, session_id: str):
        """结束会话（可选）"""
        self.redis.delete(f"session:{session_id}")