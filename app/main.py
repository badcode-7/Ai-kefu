from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from app.deepseek_engine import DeepSeekEngine
from app.knowledge_base import DeepSeekKnowledgeBase
from app.session_manager import SessionManager
import os
import logging
import time
from dotenv import load_dotenv

# 直接指定 .env 路径并加载
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

app = FastAPI()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("customer_service")

# 直接从 .env 文件读取变量
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
KNOWLEDGE_DIR = os.environ.get("KNOWLEDGE_DIR", "D:/project/AI kefu/knowledge_data")

if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY环境变量未设置")
    raise ValueError("DEEPSEEK_API_KEY环境变量未设置")

deepseek_engine = DeepSeekEngine(DEEPSEEK_API_KEY)
knowledge_base = DeepSeekKnowledgeBase(
    api_key=DEEPSEEK_API_KEY,
    knowledge_dir=KNOWLEDGE_DIR
)
session_manager = SessionManager(redis_url=REDIS_URL)

class ChatRequest(BaseModel):
    session_id: str
    query: str
    user_info: dict = None
    stream: bool = False  # 是否使用流式响应

class ChatResponse(BaseModel):
    response: str
    session_id: str
    context_used: str = None
    evaluation: dict = None

class KnowledgeRetrieveRequest(BaseModel):
    query: str
    top_k: int = 3

class KnowledgeAddRequest(BaseModel):
    text: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: Request, chat_request: ChatRequest):
    start_time = time.time()
    session_id = chat_request.session_id
    
    try:
        # 获取会话
        session = session_manager.get_session(session_id)
        
        # 知识检索
        context = knowledge_base.retrieve_context(chat_request.query)
        logger.info(f"检索到上下文: {context[:100] if context else '无'}")
        
        # 构建对话历史
        messages = []
        for item in session.get("history", [])[-5:]:  # 取最近5轮历史
            messages.append({"role": "user", "content": item["query"]})
            messages.append({"role": "assistant", "content": item["response"]})
        messages.append({"role": "user", "content": chat_request.query})
        
        # 生成回复
        if chat_request.stream:
            # 流式响应处理（这里简化，实际需要返回EventSourceResponse）
            response_text = ""
            for chunk in deepseek_engine.generate_chat_stream(messages, context):
                # 实际流式处理需要EventSourceResponse
                pass
            # 暂时不支持流式，返回普通响应
            response_text = deepseek_engine.generate_chat_response(messages, context)
        else:
            response_text = deepseek_engine.generate_chat_response(messages, context)
        
        # 评估回复质量
        evaluation = deepseek_engine.evaluate_response(
            query=chat_request.query,
            response=response_text
        )
        
        # 更新会话
        session_manager.add_to_history(
            session_id,
            chat_request.query,
            response_text
        )
        
        # 记录响应时间
        duration = time.time() - start_time
        logger.info(f"请求处理时间: {duration:.2f}s")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            context_used=context[:100] + "..." if context else "",
            evaluation=evaluation
        )
    
    except Exception as e:
        logger.error(f"处理聊天请求时出错: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="内部服务器错误")

@app.post("/api/knowledge/retrieve")
async def retrieve_knowledge(request: KnowledgeRetrieveRequest):
    """知识检索端点"""
    context = knowledge_base.retrieve_context(request.query, top_k=request.top_k)
    return {
        "query": request.query,
        "context": context,
        "top_k": request.top_k
    }

@app.post("/api/knowledge/add")
async def add_knowledge(request: KnowledgeAddRequest):
    """添加知识"""
    knowledge_base.add_knowledge(request.text)
    return {"status": "success", "message": "知识已添加"}

@app.get("/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)