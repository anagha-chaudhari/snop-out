import requests

URL = "https://jsonplaceholder.typicode.com/posts"

response = requests.get(URL, params={"_page": 1, "_limit": 3}, timeout=10)

print("status:", response.status_code)
print("content-type:", response.headers.get("Content-Type"))
print("total posts:", response.headers.get("X-Total-Count"))

posts = response.json()
print("type:", type(posts), "length:", len(posts))
for post in posts:
    print(post["id"], post["title"][:40])