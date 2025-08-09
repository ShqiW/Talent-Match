export interface Candidate {
  id: string;
  name: string;
  resume: string; // Base64 encoded string
  // resume: ArrayBuffer; // binary data as ArrayBuffer
  info: string;
  similarityScore?: number;
  aiSummary?: string;
  resume_name?: string; // Name of the resume file
}

