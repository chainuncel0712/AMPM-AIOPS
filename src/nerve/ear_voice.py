"""語音模組 - 聽懂人話、會說話"""
import os, requests

class VoiceEar:
    def __init__(self):
        self.key = os.getenv("OPENAI_API_KEY")
    
    def hear(self, audio_path: str) -> str:
        """語音轉文字"""
        with open(audio_path, "rb") as f:
            r = requests.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.key}"},
                files={"file": f, "model": (None, "whisper-1")},
                timeout=30
            )
        if r.status_code == 200:
            return r.json()["text"]
        return ""
    
    def speak(self, text: str, output_path: str = "/tmp/speak.mp3") -> str:
        """文字轉語音"""
        r = requests.post(
            "https://api.openai.com/v1/audio/speech",
            headers={"Authorization": f"Bearer {self.key}"},
            json={"model": "tts-1", "voice": "alloy", "input": text},
            timeout=30
        )
        if r.status_code == 200:
            with open(output_path, "wb") as f:
                f.write(r.content)
            return output_path
        return ""
    
    def run(self, input_data=None):
        return "語音模組就緒"
    
    def status(self):
        return {"alive": True}
