import sys
sys.path.insert(0, 'backend')

from processing import _get_embedder
import numpy as np

print("Testing Gemini embedder...")
embedder = _get_embedder()
print(f"✅ Embedder initialized: {type(embedder).__name__}")

# Test embedding
test_texts = ["Hello world", "Test embedding"]
print(f"\nEmbedding {len(test_texts)} texts...")
embeddings = embedder.encode(test_texts, convert_to_numpy=True, normalize_embeddings=True)

print(f"✅ Embeddings shape: {embeddings.shape}")
print(f"✅ Embedding dimension: {embeddings.shape[1]}")
print(f"✅ All embeddings normalized: {np.allclose(np.linalg.norm(embeddings, axis=1), 1.0)}")
print(f"\n🎉 Gemini embedder working correctly!")
