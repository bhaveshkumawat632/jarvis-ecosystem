import chromadb
import uuid
import os
from configs.settings import BASE_DIR

class MemorySystem:
    def __init__(self):
        db_path = os.path.join(BASE_DIR, "logs", "chromadb")
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="vidrush_memory")
        
    def store_pattern(self, hook: str, topic: str, style: str, score: float = 1.0):
        # High score means it was successful
        if score > 0.8:
            doc_id = str(uuid.uuid4())
            self.collection.add(
                documents=[hook],
                metadatas=[{"topic": topic, "style": style, "score": score}],
                ids=[doc_id]
            )
            print(f"Memory saved: Hook for '{topic}'")

    def query_best_hooks(self, topic: str, n_results: int = 3):
        results = self.collection.query(
            query_texts=[topic],
            n_results=n_results
        )
        return results

if __name__ == "__main__":
    mem = MemorySystem()
    mem.store_pattern("I died 5 times.", "Near Death Experience", "reddit", 0.95)
    print("Memory DB initialized.")
