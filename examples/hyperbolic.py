
import requests
import os
import sys
HYPERBOLIC_API_KEY = os.environ.get('HYPERBOLIC_API_KEY')

url = "https://api.hyperbolic.xyz/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {HYPERBOLIC_API_KEY}"
}
text_origin = "What can I do in SF?"
data = {
    "messages": [
    {"role": "system", "content": "You are a translation assistant."},
    {"role": "user", "content": f"将该文本翻译成中文: {text_origin}"}
    ],
    "model": "openai/gpt-oss-20b",
    "max_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.8
}
response = requests.post(url, headers=headers, json=data)
print(response.json())
