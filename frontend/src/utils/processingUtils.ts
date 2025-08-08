import type { Candidate } from '../shared/types/index';
import { apiService } from '../lib/api';

export const processCandidatesWithAPI = async (
  candidates: Candidate[],
  jobDescription: string,
  setProgress: (progress: number) => void,
  invitationCode?: string,
): Promise<Candidate[]> => {
  setProgress(0);

  try {
    // 检查API连接
    const healthCheck = await apiService.healthCheck();
    if (healthCheck.error) {
      console.error('API health check failed:', healthCheck.error);
      throw new Error('无法连接到后端服务，请确保后端服务器正在运行');
    }

    setProgress(20);

    // 调用推荐API
    const response = await apiService.getRecommendations(
      jobDescription,
      candidates,
      invitationCode,
    );

    if (response.error) {
      console.error('API request failed:', response.error);
      throw new Error(`API请求失败: ${response.error}`);
    }

    if (!response.data) {
      throw new Error('API返回了空数据');
    }

    setProgress(80);

    // 转换API响应为前端格式（兼容后端可能返回空或老字段名）
    const topCandidates = (response.data as any).top_candidates || [];
    const processedCandidates: Candidate[] = Array.isArray(topCandidates)
      ? topCandidates.map((candidate: any) => ({
        id: candidate.id,
        name: candidate.name,
        resume: candidate.resume,
        info: candidate.resume_text || '',
        similarityScore: candidate.similarity_score,
        aiSummary: candidate.summary,
      }))
      : [];

    setProgress(100);

    return processedCandidates;

  } catch (error) {
    console.error('Processing error:', error);
    throw error;
  }
};

// 保留原有的模拟函数作为备用
export const simulateProcessing = async (
  candidates: Candidate[],
  setProgress: (progress: number) => void
): Promise<Candidate[]> => {
  setProgress(0);

  // processing steps
  const steps = [
    'Analyzing job description...',
    'Processing candidate resumes...',
    'Generating embeddings...',
    'Computing similarity scores...',
    'Generating AI summaries...',
    'Finalizing recommendations...'
  ];

  for (let i = 0; i < steps.length; i++) {
    await new Promise(resolve => setTimeout(resolve, 600));
    setProgress(((i + 1) / steps.length) * 100);
  }

  // process candidates
  const processedCandidates: Candidate[] = candidates.map((candidate, index) => ({
    ...candidate,
    similarityScore: Math.random() * 0.4 + 0.6, // 60-100% similarity
    aiSummary: `This candidate shows strong alignment with the role requirements. Their experience in ${['React', 'TypeScript', 'Node.js', 'Python', 'Machine Learning'][index % 5]} and background in ${['frontend development', 'backend systems', 'data analysis', 'UI/UX design', 'cloud infrastructure'][index % 5]} makes them an excellent fit for this position.`
  }));

  // rank by similarity score
  processedCandidates.sort((a, b) => (b.similarityScore || 0) - (a.similarityScore || 0));

  return processedCandidates.slice(0, 5); // Top 5 results
}; 