"""
推荐业务逻辑服务
"""
from typing import List, Dict, Any
from talentmatch.etc.recommendengine import RecommendationEngine
from talentmatch.utils import process_candidates


class RecommendationService:
    """推荐服务类"""

    def __init__(
        self,
        recommendation_engine: RecommendationEngine,
    ):
        self.recommendation_engine = recommendation_engine

    # def get_recommendations(
    #     self,
    #     job_description: str,
    #     candidates_data: List[Dict[str, Any]] = None,
    #     top_k: int = 10,
    #     min_similarity: float = 0.5,
    # ) -> Dict[str, Any]:
    #     """获取候选人推荐"""
    #     if not job_description.strip():
    #         raise ValueError("Job description is required")

    #     # 确定使用哪些候选人数据
    #     if candidates_data:
    #         # 使用前端传入的候选人数据
    #         print(f"使用前端传入的 {len(candidates_data)} 个候选人数据")
    #         candidates_to_process = candidates_data
    #         use_stored_candidates = False
    #     else:
    #         # 使用已存储的候选人数据
    #         print("使用已存储的候选人数据")
    #         candidates_to_process = []
    #         use_stored_candidates = True

    #     # 处理候选人数据（如果需要）
    #     if not use_stored_candidates:
    #         processed_candidates = self.candidate_processor.process_candidates(
    #             candidates_to_process)
    #     else:
    #         processed_candidates = candidates_to_process

    #     # 获取推荐
    #     recommendations = self.recommendation_engine.find_top_candidates(
    #         job_description=job_description,
    #         candidates=processed_candidates,
    #         top_k=top_k,
    #         min_similarity=min_similarity)

    #     return {
    #         'job_description': job_description,
    #         'total_candidates': len(processed_candidates),
    #         'recommendations_count': len(recommendations),
    #         'recommendations': recommendations,
    #         'data_source':
    #         'frontend' if not use_stored_candidates else 'stored'
    #     }

    def match_candidates_realtime(
        self,
        job_description: str,
        candidates_data: List[Dict[str, Any]],
        top_k: int = 10,
        min_similarity: float = 0.5,
    ) -> Dict[str, Any]:
        """实时匹配候选人"""
        if not job_description.strip():
            raise ValueError("Job description is required")

        if not candidates_data:
            raise ValueError("Candidates data is required")

        # print(candidates_data)
        # input()

        print(
            f"实时匹配: 职位描述长度={len(job_description)}, 候选人数量={len(candidates_data)}"
        )

        # 处理候选人数据
        processed_candidates = process_candidates(
            self.recommendation_engine.embedding_processor,
            candidates_data,
        )

        if not processed_candidates:
            return {
                'message': 'No valid candidates found in the provided data',
                'top_candidates': [],
                'total_candidates': 0,
                'processing_time': 'real-time',
                'data_source': 'frontend'
            }

        # 获取推荐
        recommendations = self.recommendation_engine.find_top_candidates(
            job_description=job_description,
            candidates=processed_candidates,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        return {
            'job_description': job_description,
            'total_candidates': len(processed_candidates),
            'recommendations_count': len(recommendations),
            'top_candidates': recommendations,
            'processing_time': 'real-time',
            'data_source': 'frontend'
        }
