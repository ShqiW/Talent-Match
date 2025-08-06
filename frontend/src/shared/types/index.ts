export interface Candidate {
  id: string;
  name: string;
  resume: string;
  similarityScore?: number;
  aiSummary?: string;
}

