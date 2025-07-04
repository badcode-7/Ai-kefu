import os
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.deepseek_engine import DeepSeekEngine
import logging
from typing import List

logging.basicConfig(level=logging.INFO)

class DeepSeekKnowledgeBase:
    def __init__(self, api_key: str, knowledge_dir: str):
        self.api_key = api_key
        self.knowledge_dir = knowledge_dir
        self.knowledge = []
        self.embeddings = []
        self.engine = DeepSeekEngine(api_key)
        self.load_knowledge()
    
    def load_knowledge(self):
        """加载并向量化知识库"""
        self.knowledge = []
        for filename in os.listdir(self.knowledge_dir):
            if filename.endswith((".txt", ".md")):
                file_path = os.path.join(self.knowledge_dir, filename)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        segments = self.split_content(content)
                        self.knowledge.extend(segments)
                        logging.info(f"从文件 {filename} 加载了 {len(segments)} 个片段")
                except Exception as e:
                    logging.error(f"读取文件 {file_path} 出错: {str(e)}")
        
        # 分批处理嵌入
        if self.knowledge:
            self.embeddings = []
            batch_size = 50
            
            for i in range(0, len(self.knowledge), batch_size):
                batch = self.knowledge[i:i+batch_size]
                batch_embeddings = self.engine.get_embeddings(batch)
                
                if batch_embeddings:
                    self.embeddings.extend(batch_embeddings)
                else:
                    logging.error(f"批处理嵌入失败: {i} 到 {i+batch_size}")
            
            logging.info(f"知识库加载完成，共 {len(self.knowledge)} 个片段")
        else:
            logging.warning("知识库目录为空")
    
    def split_content(self, content: str, max_length: int = 500) -> List[str]:
        """智能分段内容"""
        segments = []
        current_segment = ""
        
        # 按句子分割
        sentences = content.split('。')
        
        for sentence in sentences:
            if not sentence.strip():
                continue
                
            full_sentence = sentence.strip() + '。'
            
            if len(current_segment) + len(full_sentence) <= max_length:
                current_segment += full_sentence
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = full_sentence
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """检索最相关的知识片段"""
        try:
            # 获取查询向量
            query_embedding = self.engine.get_embeddings([query])
            if not query_embedding or not query_embedding[0]:
                logging.warning("获取查询嵌入失败")
                return ""
            
            # 检查知识库是否加载
            if not self.embeddings:
                logging.error("知识库嵌入未加载")
                return ""
            
            # 计算相似度
            similarities = cosine_similarity(
                [query_embedding[0]],
                self.embeddings
            )
            
            # 获取最相关的top_k个片段
            if similarities.size > 0:
                top_indices = np.argsort(similarities[0])[-top_k:][::-1]
                context = "\n\n".join([self.knowledge[i] for i in top_indices])
                return context
            return ""
        
        except Exception as e:
            logging.error(f"知识检索错误: {str(e)}")
            return ""
    
    def add_knowledge(self, text: str):
        """动态添加知识片段"""
        segments = self.split_content(text)
        
        # 获取新片段的嵌入
        new_embeddings = self.engine.get_embeddings(segments)
        
        if new_embeddings:
            self.knowledge.extend(segments)
            self.embeddings.extend(new_embeddings)
            logging.info(f"添加 {len(segments)} 个新知识片段")