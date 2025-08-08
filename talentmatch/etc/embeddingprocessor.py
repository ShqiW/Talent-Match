import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


class EmbeddingProcessor:

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """Initialize embedding processor"""
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> np.ndarray:
        """Generate text embedding"""
        # Clean text
        cleaned_text = self._clean_text(text)
        # Generate embedding
        embedding = self.model.encode(
            cleaned_text,
            show_progress_bar=True,
        )
        return embedding

    def _clean_text(self, text: str) -> str:
        """Clean text, remove special characters and extra spaces"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Remove special characters, keep letters, numbers, spaces and basic punctuation
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        # Remove extra spaces
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """Calculate cosine similarity between two embeddings"""
        # Ensure 2D arrays
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)

        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)
