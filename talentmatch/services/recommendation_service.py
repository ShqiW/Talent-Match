"""
Recommendation business logic service
"""
from typing import List, Dict, Any
from talentmatch.etc.recommendengine import RecommendationEngine
from talentmatch.utils import process_candidates


class RecommendationService:
    """Recommendation service class"""

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
    #     """Get candidate recommendations"""
    #     if not job_description.strip():
    #         raise ValueError("Job description is required")

    #     # Determine which candidate data to use
    #     if candidates_data:
    #         # Use candidate data passed from frontend
    #         print(f"Using {len(candidates_data)} candidate data passed from frontend")
    #         candidates_to_process = candidates_data
    #         use_stored_candidates = False
    #     else:
    #         # Use stored candidate data
    #         print("Using stored candidate data")
    #         candidates_to_process = []
    #         use_stored_candidates = True

    #     # Process candidate data (if needed)
    #     if not use_stored_candidates:
    #         processed_candidates = self.candidate_processor.process_candidates(
    #             candidates_to_process)
    #     else:
    #         processed_candidates = candidates_to_process

    #     # Get recommendations
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
        """Real-time candidate matching"""
        if not job_description.strip():
            raise ValueError("Job description is required")

        if not candidates_data:
            raise ValueError("Candidates data is required")

        # print(candidates_data)
        # input()

        print(
            f"Real-time matching: job description length={len(job_description)}, candidate count={len(candidates_data)}"
        )

        # Process candidate data
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

        # Get recommendations
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
