import requests

'''
4교시. Flask — 받는 쪽이 되기
'''

response = requests.get("http://127.0.0.1:5001/rules")
print(response.json())