import os
from dotenv import load_dotenv
from app.deepseek_engine import DeepSeekEngine
from app.knowledge_base import DeepSeekKnowledgeBase
from app.session_manager import SessionManager

# 加载.env配置
env_path = os.path.join(os.path.dirname(__file__), '..', '.env.example')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
else:
    raise RuntimeError(".env 文件不存在，请先配置 API KEY")

def test_deepseek_engine():
    engine = DeepSeekEngine(api_key=DEEPSEEK_API_KEY)
    reply = engine.generate_chat_response(
        messages=[{"role": "user", "content": "你好，如何退货？"}],
        context="退货政策：7天无理由退货"
    )
    print("DeepSeekEngine回复:", reply)

def test_knowledge_base():
    kb = DeepSeekKnowledgeBase(
        api_key=DEEPSEEK_API_KEY,
        knowledge_dir=os.path.join(os.path.dirname(__file__), "../knowledge_data")
    )
    context = kb.retrieve_context("退货需要付运费吗？")
    print("知识库检索结果:", context)

def test_session_manager():
    sm = SessionManager(redis_url=REDIS_URL)
    sm.save_session("test_session", {"history": [{"query": "hi", "response": "hello"}]})
    session = sm.get_session("test_session")
    print("Session内容:", session)

if __name__ == "__main__":
    print("=== 测试 DeepSeekEngine ===")
    test_deepseek_engine()
    print("\n=== 测试 DeepSeekKnowledgeBase ===")
    test_knowledge_base()
    print("\n=== 测试 SessionManager ===")
    test_session_manager()
