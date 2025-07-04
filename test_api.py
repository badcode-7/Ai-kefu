import requests
import time
import json

BASE_URL = "http://localhost:8000"

def test_knowledge_retrieval():
    print("=== 测试知识库检索 ===")
    queries = [
        "退款需要多长时间",
        "退货被拒绝怎么办",
        "退货运费谁承担",
        "特殊商品能退货吗"
    ]
    
    for query in queries:
        print(f"\n查询: {query}")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/knowledge/retrieve",
            json={"query": query, "top_k": 2}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"检索时间: {time.time() - start_time:.2f}s")
            print(f"相关上下文: {result['context']}")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)

def test_chat_api():
    print("\n=== 测试客服对话 ===")
    session_id = f"test_session_{int(time.time())}"
    test_cases = [
        "我想退货，怎么操作？",
        "退款需要多长时间？",
        "你们接受开封商品的退货吗？",
        "退货运费谁承担？"
    ]
    
    for query in test_cases:
        print(f"\n用户: {query}")
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={
                "session_id": session_id,
                "query": query
            }
        )
        if response.status_code == 200:
            data = response.json()
            print(f"响应时间: {time.time() - start_time:.2f}s")
            print(f"客服: {data['response']}")
            if data.get('context_used'):
                print(f"使用的知识: {data['context_used'][:80]}...")
            if data.get('evaluation'):
                print(f"回复评估: 分数={data['evaluation']['score']}, 建议={data['evaluation']['improvement']}")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    test_knowledge_retrieval()
    test_chat_api()