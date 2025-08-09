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
    // First verify invitation code
    const verify = await apiService.verifyInvitation(invitationCode);
    if (verify.error) {
      throw new Error('Invalid invitation code');
    }

    // Check API connection
    const healthCheck = await apiService.healthCheck();
    if (healthCheck.error) {
      console.error('API health check failed:', healthCheck.error);
      throw new Error('Unable to connect to backend service, please ensure backend server is running');
    }

    setProgress(20);

    // Call recommendation API
    const response = await apiService.getRecommendations(
      jobDescription,
      candidates,
      invitationCode,
    );

    if (response.error) {
      console.error('API request failed:', response.error);
      throw new Error(`API request failed: ${response.error}`);
    }

    if (!response.data) {
      throw new Error('API returned empty data');
    }

    setProgress(80);

    // Convert API response to frontend format (compatible with possible empty returns or old field names from backend)
    const topCandidates = (response.data as any).top_candidates || [];
    const processedCandidates: Candidate[] = Array.isArray(topCandidates)
      ? topCandidates.map((candidate: any) => ({
        id: candidate.id,
        name: candidate.name,
        resume: candidate.resume,
        info: candidate.resume_text || '',
        similarityScore: candidate.similarity_score,
        aiSummary: candidate.summary,
        resume_name: candidate.resume_name || '',
      }))
      : [];

    setProgress(100);

    return processedCandidates;

  } catch (error) {
    console.error('Processing error:', error);
    throw error;
  }
};

// Keep original simulation function as backup
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