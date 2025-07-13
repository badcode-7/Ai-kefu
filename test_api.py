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
            print(f"相关上下文: {result['context'][:100] if result['context'] else '无'}")
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
                print(f"回复评估: 分数={data['evaluation'].get('score', 'N/A')}, 建议={data['evaluation'].get('improvement', 'N/A')}")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)

def test_health_check():
    print("=== 测试健康检查 ===")
    try:
        # 假设健康检查接口是 /health
        response = requests.get(f"{BASE_URL}/health")

        print(f"HTTP 状态码: {response.status_code}")
        print(f"响应头: {response.headers}")
        print(f"响应内容 (原始数据): {response.text}") # <--- 新增这行，打印原始响应内容

        # 检查 HTTP 状态码，如果不是 2xx，requests 会抛出异常
        response.raise_for_status()

        # 尝试将响应解析为 JSON
        # 更好的做法是先检查 Content-Type，确保它是 JSON
        if 'application/json' in response.headers.get('Content-Type', ''):
            print(f"基础健康检查 (JSON 解析): {response.json()}")
        else:
            print("响应内容不是 JSON 格式，或者 Content-Type 头信息缺失/不正确。")

    except requests.exceptions.ConnectionError as e:
        print(f"错误: 无法连接到服务器。AI 客服服务器是否运行在 {BASE_URL}？错误详情: {e}")
    except requests.exceptions.Timeout as e:
        print(f"错误: 请求超时。错误详情: {e}")
    except requests.exceptions.RequestException as e:
        print(f"发生了一个意外的请求错误: {e}")
    except Exception as e:
        print(f"发生了一个未知错误: {e}")
def test_topic_retrieval():
    print("\n=== 测试主题检索 ===")
    topics = ["退货流程", "退款时效", "运费政策", "特殊商品"]
    
    for topic in topics:
        print(f"\n主题: {topic}")
        response = requests.post(
            f"{BASE_URL}/api/knowledge/topic",
            json={"topic": topic}
        )
        if response.status_code == 200:
            result = response.json()
            print(f"检索结果: {result['context'][:150] if result['context'] else '无'}")
        else:
            print(f"错误: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    test_health_check()
    test_knowledge_retrieval()
    test_topic_retrieval()
    test_chat_api()