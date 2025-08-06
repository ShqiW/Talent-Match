import type { Candidate } from '../shared/types/index';

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