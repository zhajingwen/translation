import os

print(os.getenv("OPENAI_API_KEY"))  # 这应该打印出 "sk-BayJU"
import sys
print(sys.executable)
d = {'name': 'Alice', 'age': 25}
x, y = d.values()
print(x, y)  # Alice 25
