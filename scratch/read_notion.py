import urllib.request
import json

NOTION_TOKEN = "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"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def create_page():
    url = "https://api.notion.com/v1/pages"
    payload = {
        "parent": {
            "type": "workspace",
            "workspace": True
        },
        "properties": {
            "title": [
                {
                    "text": {
                        "content": "NCS — SaaS & App Research"
                    }
                }
            ]
        }
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode("utf-8"))
            print("Successfully created page:")
            print(json.dumps(res, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error creating page: {e}")
        if hasattr(e, "read"):
            print(e.read().decode())

if __name__ == "__main__":
    create_page()
