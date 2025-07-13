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
        self.knowledge = []  # 存储知识片段
        self.embeddings = []  # 存储对应的嵌入向量
        self.engine = DeepSeekEngine(api_key)
        self.load_knowledge()
    
    def load_knowledge(self):
        """加载并向量化知识库"""
        if not self.engine.embedding_model:
            logging.error("嵌入模型未初始化，无法加载知识库")
            return
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
            batch_size = 32
            
            for i in range(0, len(self.knowledge), batch_size):
                batch = self.knowledge[i:i+batch_size]
                
                # 跳过空批次
                if not batch:
                    continue
                    
                try:
                    batch_embeddings = self.engine.get_embeddings(batch)
                    
                    if batch_embeddings and len(batch_embeddings) == len(batch):
                        self.embeddings.extend(batch_embeddings)
                    else:
                        logging.error(f"批处理嵌入失败: {i} 到 {i+batch_size}")
                        # 添加空嵌入避免索引错误
                        self.embeddings.extend([[] for _ in range(len(batch))])
                except Exception as e:
                    logging.error(f"嵌入处理错误: {str(e)}")
                    self.embeddings.extend([[] for _ in range(len(batch))])
            
            logging.info(f"知识库加载完成，共 {len(self.knowledge)} 个片段")
        else:
            logging.warning("知识库目录为空")
    
    def split_content(self, content: str, max_length: int = 300) -> List[str]:
        """智能分段内容，保留文档结构"""
        if not content.strip():
            return []
        
        # 按章节分割（Markdown标题）
        sections = []
        current_section = ""
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # 检测标题 (## 章节标题)
            if line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                current_section = line + "\n"
            else:
                # 普通内容行
                if len(current_section) + len(line) + 1 < max_length:
                    current_section += line + "\n"
                else:
                    if current_section:
                        sections.append(current_section)
                    current_section = line + "\n"
        
        if current_section:
            sections.append(current_section)
        
        # 如果未检测到章节，按句子分割
        if not sections:
            return self._split_by_sentences(content, max_length)
            
        return sections

    def _split_by_sentences(self, content: str, max_length: int) -> List[str]:
        """按句子分割内容"""
        segments = []
        current_segment = ""
        
        # 支持多种句子结束符
        sentence_endings = ['。', '！', '？', '\n', '.', '!', '?']
        
        sentences = []
        buffer = ""
        for char in content:
            buffer += char
            if char in sentence_endings:
                sentences.append(buffer.strip())
                buffer = ""
        
        if buffer:
            sentences.append(buffer.strip())
        
        for sentence in sentences:
            if not sentence:
                continue
                
            if len(current_segment) + len(sentence) + 1 < max_length:
                current_segment += sentence + "\n"
            else:
                if current_segment:
                    segments.append(current_segment)
                current_segment = sentence + "\n"
        
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def retrieve_context(self, query: str, top_k: int = 3) -> str:
        """检索最相关的知识片段（多样化结果）"""
        try:
            # 获取查询向量
            query_embedding = self.engine.get_embeddings([query])
            if not query_embedding or not query_embedding[0]:
                logging.warning("获取查询嵌入失败")
                return ""
            
            # 检查知识库
            if not self.embeddings or len(self.embeddings) != len(self.knowledge):
                logging.error("知识库嵌入不完整")
                return ""
            
            # 计算相似度
            similarities = cosine_similarity([query_embedding[0]], self.embeddings)[0]
            
            # 多样化选择：确保不同主题的知识
            context = ""
            selected_indices = set()
            
            # 第一轮：选择最相关的片段
            top_index = np.argmax(similarities)
            if similarities[top_index] > 0.2:  # 最低相似度阈值
                context += self.knowledge[top_index] + "\n\n"
                selected_indices.add(top_index)
            
            # 第二轮：选择不同主题的相关片段
            remaining_indices = [i for i in range(len(similarities)) if i not in selected_indices]
            if remaining_indices:
                # 按相似度排序
                sorted_indices = sorted(remaining_indices, key=lambda i: similarities[i], reverse=True)
                
                for i in sorted_indices[:top_k-1]:
                    if similarities[i] > 0.15:  # 次低相似度阈值
                        context += self.knowledge[i] + "\n\n"
                        selected_indices.add(i)
                        if len(selected_indices) >= top_k:
                            break
            
            return context.strip()
        
        except Exception as e:
            logging.error(f"知识检索错误: {str(e)}", exc_info=True)
            return ""
    
    def add_knowledge(self, text: str):
        """动态添加知识片段"""
        segments = self.split_content(text)
        
        # 获取新片段的嵌入
        new_embeddings = self.engine.get_embeddings(segments)
        
        if new_embeddings and len(new_embeddings) == len(segments):
            self.knowledge.extend(segments)
            self.embeddings.extend(new_embeddings)
            logging.info(f"添加 {len(segments)} 个新知识片段")
        else:
            logging.error("添加新知识片段失败，嵌入生成不完整")