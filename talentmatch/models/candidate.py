"""
候选人数据模型
"""
from typing import List, Dict, Any
import uuid


class Candidate:
    """候选人模型类"""
    
    def __init__(self, name: str, resume: str, candidate_id: str = None):
        self.id = candidate_id or str(uuid.uuid4())
        self.name = name
        self.resume = resume
        self.summary = ""
        self.embedding = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'resume': self.resume,
            'summary': self.summary,
            'embedding': self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        """从字典创建候选人对象"""
        candidate = cls(
            name=data['name'],
            resume=data['resume'],
            candidate_id=data.get('id')
        )
        candidate.summary = data.get('summary', '')
        candidate.embedding = data.get('embedding')
        return candidate


class CandidateStorage:
    """候选人存储管理"""
    
    def __init__(self):
        self._candidates: List[Candidate] = []
    
    def add_candidates(self, candidates: List[Candidate]) -> int:
        """添加候选人"""
        self._candidates.extend(candidates)
        return len(candidates)
    
    def get_all(self) -> List[Candidate]:
        """获取所有候选人"""
        return self._candidates.copy()
    
    def get_by_id(self, candidate_id: str) -> Candidate:
        """根据ID获取候选人"""
        for candidate in self._candidates:
            if candidate.id == candidate_id:
                return candidate
        return None
    
    def delete_by_id(self, candidate_id: str) -> Candidate:
        """根据ID删除候选人"""
        for i, candidate in enumerate(self._candidates):
            if candidate.id == candidate_id:
                return self._candidates.pop(i)
        return None
    
    def clear_all(self) -> int:
        """清空所有候选人"""
        count = len(self._candidates)
        self._candidates.clear()
        return count
    
    def count(self) -> int:
        """获取候选人数量"""
        return len(self._candidates)
    
    def get_info_list(self) -> List[Dict[str, Any]]:
        """获取候选人信息列表（用于API响应）"""
        candidates_info = []
        for candidate in self._candidates:
            candidates_info.append({
                'id': candidate.id,
                'name': candidate.name,
                'summary': candidate.summary,
                'resume_preview': candidate.resume[:200] + '...' if len(candidate.resume) > 200 else candidate.resume
            })
        return candidates_info 