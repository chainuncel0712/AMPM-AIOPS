"""向量記憶 - 語義搜尋"""
try:
    import chromadb
    from chromadb.utils import embedding_functions
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False
    print("⚠️ chromadb 未安裝，向量記憶功能將不可用")

class VectorMemory:
    def __init__(self):
        if not HAS_CHROMADB:
            raise RuntimeError("chromadb is required for VectorMemory")
        self.client = chromadb.PersistentClient(path="./memory_db")
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        try:
            self.collection = self.client.get_collection("memory", embedding_function=self.ef)
        except:
            self.collection = self.client.create_collection("memory", embedding_function=self.ef)
    
    def remember(self, text: str, metadata: dict = None):
        """記住"""
        import uuid
        self.collection.add(
            documents=[text],
            metadatas=[metadata or {}],
            ids=[str(uuid.uuid4())]
        )
    
    def recall(self, query: str, n: int = 3) -> list:
        """回想相關記憶"""
        results = self.collection.query(query_texts=[query], n_results=n)
        return results.get("documents", [[]])[0]
    
    def run(self, input_data=None):
        if isinstance(input_data, dict):
            if "query" in input_data:
                return self.recall(input_data["query"])
            if "text" in input_data:
                self.remember(input_data["text"])
                return "已記憶"
        return "向量記憶就緒"
    
    def status(self):
        return {"alive": True, "count": self.collection.count()}
