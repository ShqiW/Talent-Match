"""
Candidate data model
"""
from typing import List, Dict, Any
import uuid


class Candidate:
    """Candidate model class"""
    
    def __init__(self, name: str, resume: str, candidate_id: str = None):
        self.id = candidate_id or str(uuid.uuid4())
        self.name = name
        self.resume = resume
        self.summary = ""
        self.embedding = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return {
            'id': self.id,
            'name': self.name,
            'resume': self.resume,
            'summary': self.summary,
            'embedding': self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Candidate':
        """Create candidate object from dictionary"""
        candidate = cls(
            name=data['name'],
            resume=data['resume'],
            candidate_id=data.get('id')
        )
        candidate.summary = data.get('summary', '')
        candidate.embedding = data.get('embedding')
        return candidate


class CandidateStorage:
    """Candidate storage management"""
    
    def __init__(self):
        self._candidates: List[Candidate] = []
    
    def add_candidates(self, candidates: List[Candidate]) -> int:
        """Add candidates"""
        self._candidates.extend(candidates)
        return len(candidates)
    
    def get_all(self) -> List[Candidate]:
        """Get all candidates"""
        return self._candidates.copy()
    
    def get_by_id(self, candidate_id: str) -> Candidate:
        """Get candidate by ID"""
        for candidate in self._candidates:
            if candidate.id == candidate_id:
                return candidate
        return None
    
    def delete_by_id(self, candidate_id: str) -> Candidate:
        """Delete candidate by ID"""
        for i, candidate in enumerate(self._candidates):
            if candidate.id == candidate_id:
                return self._candidates.pop(i)
        return None
    
    def clear_all(self) -> int:
        """Clear all candidates"""
        count = len(self._candidates)
        self._candidates.clear()
        return count
    
    def count(self) -> int:
        """Get candidate count"""
        return len(self._candidates)
    
    def get_info_list(self) -> List[Dict[str, Any]]:
        """Get candidate information list (for API response)"""
        candidates_info = []
        for candidate in self._candidates:
            candidates_info.append({
                'id': candidate.id,
                'name': candidate.name,
                'summary': candidate.summary,
                'resume_preview': candidate.resume[:200] + '...' if len(candidate.resume) > 200 else candidate.resume
            })
        return candidates_info 