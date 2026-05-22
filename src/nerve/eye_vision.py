"""視覺皮層 - 圖片理解"""
import os, base64, requests

class VisionEye:
    def __init__(self):
        self.key = os.getenv("OPENAI_API_KEY")
    
    def see_image(self, image_path: str, question: str = "描述這張圖片") -> str:
        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        
        r = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.key}"},
            json={
                "model": "gpt-4o",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}}
                    ]
                }]
            }, timeout=30
        )
        if r.status_code == 200:
            return r.json()["choices"][0]["message"]["content"]
        return f"視覺錯誤: {r.status_code}"
    
    def run(self, input_data=None):
        if isinstance(input_data, dict):
            return self.see_image(input_data.get("path", ""), input_data.get("question", ""))
        return "需要圖片路徑"
    
    def status(self):
        return {"alive": True, "model": "gpt-4o-vision"}
