"""
零件總表 - 手機監控用
"""
MANIFEST = [
    {
        "name": "nerve_eye",
        "class": "Eye",
        "location": "nerve/eye.py",
        "depends_on": ["web_search"],
        "version": "v2.0",
        "status": "active",
        "desc": "視覺感測器 - 網頁搜尋"
    },
    {
        "name": "nerve_ear",
        "class": "Ear",
        "location": "nerve/ear.py",
        "depends_on": [],
        "version": "v2.0",
        "status": "active",
        "desc": "聽覺感測器 - 語音處理"
    },
    {
        "name": "bag_web_search",
        "class": "WebSearchPlugin",
        "location": "bag/web_search.py",
        "depends_on": [],
        "version": "v2.0",
        "status": "active",
        "desc": "網頁搜尋外掛"
    },
    {
        "name": "web_search",
        "class": "WebSearch",
        "location": "web/search.py",
        "depends_on": [],
        "version": "v2.0",
        "status": "active",
        "desc": "搜尋引擎核心"
    }
]

def get_active():
    return [m for m in MANIFEST if m["status"] == "active"]

def find(name: str):
    for m in MANIFEST:
        if m["name"] == name:
            return m
    return None

if __name__ == "__main__":
    for m in get_active():
        print(f"  [{m['name']}] {m['version']} - {m['desc']}")
