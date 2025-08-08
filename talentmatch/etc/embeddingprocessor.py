import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import re


class EmbeddingProcessor:

    def __init__(self, model_name: str = 'all-mpnet-base-v2'):
        """初始化嵌入处理器"""
        self.model = SentenceTransformer(model_name)

    def generate_embedding(self, text: str) -> np.ndarray:
        """生成文本嵌入"""
        # 清理文本
        cleaned_text = self._clean_text(text)
        # 生成嵌入
        embedding = self.model.encode(
            cleaned_text,
            show_progress_bar=True,
        )
        return embedding

    def _clean_text(self, text: str) -> str:
        """清理文本，移除特殊字符和多余空格"""
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        # 移除特殊字符，保留字母、数字、空格和基本标点
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        # 移除多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def calculate_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray,
    ) -> float:
        """计算两个嵌入之间的余弦相似度"""
        # 确保是2D数组
        if embedding1.ndim == 1:
            embedding1 = embedding1.reshape(1, -1)
        if embedding2.ndim == 1:
            embedding2 = embedding2.reshape(1, -1)

        similarity = cosine_similarity(embedding1, embedding2)[0][0]
        return float(similarity)
