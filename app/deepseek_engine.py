import os
import requests
import time
import logging
import json
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)

class DeepSeekEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """获取文本嵌入向量"""
        try:
            payload = {
                "model": "text-embedding",
                "input": texts,
                "encoding_format": "float"
            }
            
            response = requests.post(
                f"{self.base_url}/embeddings",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                error_msg = response.json().get("error", {}).get("message", "Unknown error")
                logging.error(f"Embeddings API error {response.status_code}: {error_msg}")
                return []
                
            data = response.json()
            return [item['embedding'] for item in data['data']]
        
        except Exception as e:
            logging.error(f"Embeddings error: {str(e)}")
            return []
    
    def generate_chat_response(self, messages: List[Dict], context: Optional[str] = None) -> str:
        """生成客服对话回复"""
        try:
            # 构建系统提示
            system_content = "你是一名专业电商客服助手，请用友好、专业的态度回答用户问题。"
            if context:
                system_content += f"\n\n[相关知识]\n{context}"
            
            # 构建完整消息
            full_messages = [{"role": "system", "content": system_content}]
            full_messages.extend(messages)
            
            payload = {
                "model": "deepseek-chat",
                "messages": full_messages,
                "temperature": 0.7,
                "max_tokens": 512,
                "top_p": 0.9,
                "frequency_penalty": 0.2
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=20
            )
            
            if response.status_code != 200:
                error_data = response.json()
                error_msg = error_data.get("error", {}).get("message", "Unknown error")
                logging.error(f"Chat API error {response.status_code}: {error_msg}")
                return "抱歉，我暂时无法回答这个问题，请稍后再试。"
            
            return response.json()["choices"][0]["message"]["content"].strip()
        
        except requests.exceptions.Timeout:
            logging.error("API请求超时")
            return "请求超时，请稍后再试。"
        except Exception as e:
            logging.error(f"Chat generation error: {str(e)}")
            return "系统繁忙，请稍后再试。"
    
    def evaluate_response(self, query: str, response: str) -> dict:
        """评估回复质量"""
        try:
            prompt = f"""
            请评估以下客服回复的质量（1-5分），并给出改进建议：
            问题：{query}
            回复：{response}
            
            评估维度：
            1. 信息准确性
            2. 语言专业性
            3. 问题解决程度
            
            请用JSON格式返回：
            {{
                "score": 分数,
                "improvement": "改进建议"
            }}
            """
            
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 256,
                "response_format": {"type": "json_object"}
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                timeout=15
            )
            
            if response.status_code != 200:
                return {"score": 3, "improvement": "评估失败"}
            
            result = response.json()["choices"][0]["message"]["content"].strip()
            return json.loads(result)
        
        except Exception as e:
            logging.error(f"Evaluation error: {str(e)}")
            return {"score": 3, "improvement": "评估服务异常"}

    def generate_chat_stream(self, messages: List[Dict], context: Optional[str] = None):
        """流式生成回复"""
        try:
            # 构建系统提示
            system_content = "你是一名专业电商客服助手，请用友好、专业的态度回答用户问题。"
            if context:
                system_content += f"\n\n[相关知识]\n{context}"
            
            full_messages = [{"role": "system", "content": system_content}]
            full_messages.extend(messages)
            
            payload = {
                "model": "deepseek-chat",
                "messages": full_messages,
                "temperature": 0.7,
                "max_tokens": 512,
                "stream": True
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self.headers,
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code != 200:
                yield "data: [ERROR]\n\n"
                return
            
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith('data:'):
                        if decoded_line == 'data: [DONE]':
                            break
                        try:
                            chunk = json.loads(decoded_line[5:])
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield f"data: {json.dumps({'content': content})}\n\n"
                        except:
                            continue
        except Exception as e:
            logging.error(f"Stream error: {str(e)}")
            yield "data: [ERROR]\n\n"