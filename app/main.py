import sys
from pathlib import Path
from fastapi.staticfiles import StaticFiles
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse, HTMLResponse
# 添加项目根目录到 Python 路径
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

import os
import logging
import time
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(dotenv_path=BASE_DIR / '.env')

 # 导入应用模块
from app.deepseek_engine import DeepSeekEngine
from app.knowledge_base import DeepSeekKnowledgeBase
from app.session_manager import SessionManager

app = FastAPI()
# 静态文件服务配置
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "static")), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    # 使用绝对路径确保正确找到文件
    index_path = os.path.join(os.path.dirname(__file__), "..", "static", "index.html")
    return FileResponse(index_path)

# 添加路由处理其他静态文件请求
@app.get("/{file_path:path}")
async def serve_static(file_path: str):
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    file_path = os.path.join(static_dir, file_path)
    
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 如果请求的是根目录，返回index.html
    if file_path == "" or file_path.endswith("/"):
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    # 文件不存在返回404
    return {"error": "File not found"}, 404

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("customer_service")

# 从环境变量读取配置
DEEPSEEK_API_KEY = "sk-9f546130337e4fb893e089b1c2169cf5"
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
KNOWLEDGE_DIR = os.environ.get("KNOWLEDGE_DIR", "knowledge_data")

# 验证环境变量
if not DEEPSEEK_API_KEY:
    logger.error("DEEPSEEK_API_KEY环境变量未设置")
    raise ValueError("DEEPSEEK_API_KEY环境变量未设置")

# 初始化核心组件
deepseek_engine = DeepSeekEngine(DEEPSEEK_API_KEY)
knowledge_base = DeepSeekKnowledgeBase(
    api_key=DEEPSEEK_API_KEY,
    knowledge_dir=KNOWLEDGE_DIR
)
session_manager = SessionManager(redis_url=REDIS_URL)

# 定义请求/响应模型
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

# API端点
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
            # 流式响应处理
            response_text = ""
            for chunk in deepseek_engine.generate_chat_stream(messages, context):
                # 实际流式处理需要EventSourceResponse
                # 这里仅收集响应
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

@app.get("/health/detail")
def detailed_health_check():
    """详细健康检查"""
    status = {
        "status": "healthy",
        "version": "1.0.0",
        "embedding_model_loaded": deepseek_engine.embedding_model is not None,
        "knowledge_base_count": len(knowledge_base.knowledge) if hasattr(knowledge_base, 'knowledge') else 0
    }
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)