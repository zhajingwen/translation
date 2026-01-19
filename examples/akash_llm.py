import os
import requests

api_key = os.getenv("AKASHML_API_KEY")

response = requests.post(
  "https://api.akashml.com/v1/chat/completions",
  headers={
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
  },
  json={
    "model": "Qwen/Qwen3-30B-A3B",
    "messages": [
          {
                "role": "user",
                "content": "Your message here"
          }
    ],
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.9
  }
)

print(response.json()["choices"][0]["message"]["content"])
