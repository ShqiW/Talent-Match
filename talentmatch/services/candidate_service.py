"""
候选人业务逻辑服务
"""
from typing import List, Dict, Any
from talentmatch.models.candidate import Candidate, CandidateStorage
from talentmatch.etc.embeddingprocessor import EmbeddingProcessor
from talentmatch.utils import process_candidates


class CandidateService:
    """候选人服务类"""

    def __init__(self, embedding_processor: EmbeddingProcessor):
        self.embedding_processor = embedding_processor
        self.storage = CandidateStorage()

    def add_candidates_from_data(
        self,
        candidates_data: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """从数据添加候选人"""
        if not candidates_data:
            raise ValueError("No candidates provided")

        # 处理候选人数据
        processed_candidates = process_candidates(self.embedding_processor,
                                                  candidates_data)

        # 添加到存储
        added_count = self.storage.add_candidates(processed_candidates)

        return {
            'message': f'Successfully added {added_count} candidates',
            'added_count': added_count,
            'total_candidates': self.storage.count()
        }

    def add_candidates_from_files(
            self, files_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """从文件数据添加候选人"""
        if not files_data:
            raise ValueError("No files provided")

        # 处理候选人数据
        processed_candidates = process_candidates(self.embedding_processor,
                                                  files_data)

        if not processed_candidates:
            raise ValueError("No valid candidates found in uploaded files")

        # 添加到存储
        added_count = self.storage.add_candidates(processed_candidates)

        return {
            'message': f'Successfully uploaded {added_count} candidates',
            'uploaded_count': added_count,
            'total_candidates': self.storage.count()
        }

    def get_all_candidates(self) -> Dict[str, Any]:
        """获取所有候选人"""
        candidates_info = self.storage.get_info_list()

        return {
            'total_candidates': self.storage.count(),
            'candidates': candidates_info
        }

    def delete_candidate(self, candidate_id: str) -> Dict[str, Any]:
        """删除特定候选人"""
        deleted_candidate = self.storage.delete_by_id(candidate_id)

        if not deleted_candidate:
            raise ValueError("Candidate not found")

        return {
            'message':
            f'Successfully deleted candidate: {deleted_candidate.name}',
            'deleted_candidate': {
                'id': deleted_candidate.id,
                'name': deleted_candidate.name
            }
        }

    def clear_all_candidates(self) -> Dict[str, Any]:
        """清空所有候选人"""
        count = self.storage.clear_all()

        return {
            'message': f'Successfully cleared {count} candidates',
            'total_candidates': 0
        }

    def get_candidates_for_recommendation(self,
                                          use_stored: bool = True
                                          ) -> List[Candidate]:
        """获取用于推荐的候选人列表"""
        if use_stored:
            candidates = self.storage.get_all()
            if not candidates:
                raise ValueError(
                    "No candidates available for recommendation. Please add candidates first."
                )
            return candidates
        else:
            return []
