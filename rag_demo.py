import os
import urllib.request
import json

API_KEY = "key"

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"

# 第一步：知识库
knowledge_base = [
    "自考没有入学考试，但需要通过所有课程考试才能毕业，一般需要1.5-4年。",
    "成考需要参加全国统一入学考试，通过后入学，学习方式较为宽松。",
    "自考的难度是三种形式中最大的，但相对含金量会高一点。",
    "成考和自考都可以拿到学位证，但需要达成一些要求，例如成绩。",
    "网教也叫远程教育，不需要考试，是三种形式中门槛最低的。"
]


# 第二步：简单的相关性搜索（用关键词匹配代替向量搜索）
def simple_search(question, knowledge_base):
    keywords = {
        "自考": [0, 2],
        "成考": [1, 3],
        "网教": [4],
        "学位": [3],
        "难度": [2],
        "考试": [0, 1, 4]
    }
    relevant_indices = set()
    for keyword, indices in keywords.items():
        if keyword in question:
            relevant_indices.update(indices)

    if not relevant_indices:
        return knowledge_base  # 没匹配到关键词，返回全部

    return [knowledge_base[i] for i in relevant_indices]


# 第三步：把找到的内容+问题一起发给AI
def ask_with_rag(question):
    relevant_docs = simple_search(question, knowledge_base)
    context = "\n".join(relevant_docs)

    prompt = f"""你是一个专业的招生顾问助手。请根据以下知识库内容回答用户问题，
不要编造知识库之外的信息。

知识库内容：
{context}

用户问题：{question}
"""

    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}]
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode("utf-8"))
        return result["candidates"][0]["content"]["parts"][0]["text"]


# 测试
print(ask_with_rag("网教需要考试吗？"))


# 对比：没有RAG，直接问AI
import time


def ask_without_rag(question, retries=3):
    data = json.dumps({
        "contents": [{"parts": [{"text": question}]}]
    }, ensure_ascii=False).encode("utf-8")

    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json; charset=utf-8"})

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 503 and attempt < retries - 1:
                print(f"服务器繁忙，{2}秒后重试...")
                time.sleep(2)
            else:
                raise

print("=== 没有RAG ===")
print(ask_without_rag("网教需要考试吗？请用50字以内回答"))

print("\n=== 有RAG ===")
print(ask_with_rag("网教需要考试吗？"))