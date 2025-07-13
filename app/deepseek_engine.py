import os
import requests
import time
import logging
import json
import numpy as np
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)

class DeepSeekEngine:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.proxies = {
            "http": None,
            "https": None,
        }
        self.knowledge_index = {}
        
        # 加载本地嵌入模型
        self.embedding_model = self._load_embedding_model()
    
    # 修改 deepseek_engine.py 中的 _load_embedding_model 方法
    def _load_embedding_model(self):
        """加载本地嵌入模型（完全离线）"""
        try:
            # 使用绝对路径加载本地模型
            model_path = "/app/models"
            
            # 确保模型文件存在
            if not os.path.exists(os.path.join(model_path, "pytorch_model.bin")):
                logging.error(f"模型文件缺失于: {model_path}")
                return None
            
            # 禁用所有网络请求
            os.environ["TRANSFORMERS_OFFLINE"] = "1"
            os.environ["HF_DATASETS_OFFLINE"] = "1"
            
            # 加载模型
            model = SentenceTransformer(model_path)
            logging.info(f"成功从本地加载嵌入模型: {model_path}")
            return model
        except Exception as e:
            logging.error(f"加载本地嵌入模型失败: {str(e)}")
            return None
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """使用本地模型获取文本嵌入向量"""
        if not self.embedding_model:
            logging.error("嵌入模型未初始化")
            return []
        
        try:
            # 批量处理文本
            embeddings = self.embedding_model.encode(
                texts,
                convert_to_tensor=False,  # 返回 numpy 数组
                show_progress_bar=False,
                normalize_embeddings=True  # 标准化向量
            )
            
            # 转换为列表格式
            return [embedding.tolist() for embedding in embeddings]
        
        except Exception as e:
            logging.error(f"本地嵌入生成错误: {str(e)}")
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
                timeout=20,
                proxies=self.proxies
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
                timeout=15,
                proxies=self.proxies
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
                timeout=30,
                proxies=self.proxies
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
    def load_knowledge(self):
        # ...
        # 重建索引
        self.knowledge_index = defaultdict(list)
        
        for idx, text in enumerate(self.knowledge):
            # 提取主题（从Markdown标题）
            if text.startswith('## '):
                topic = text.split('\n')[0].replace('## ', '').strip()
                self.knowledge_index[topic].append(idx)
        
        logging.info(f"知识索引构建完成: {len(self.knowledge_index)} 个主题")
    
    def retrieve_by_topic(self, topic: str) -> str:
        """按主题检索知识"""
        if topic not in self.knowledge_index:
            return ""
        
        context = ""
        for idx in self.knowledge_index[topic]:
            context += self.knowledge[idx] + "\n\n"
        return context