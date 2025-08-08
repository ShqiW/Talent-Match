import type { Candidate } from '../shared/types/index';

// Support environment variable configuration for API URL
const getApiBaseUrl = () => {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }

  const hostname = window.location.hostname;
  const port = window.location.port;

  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:5000';
  }

  return `${window.location.protocol}//${hostname}:5000`;
};

// const API_BASE_URL = getApiBaseUrl();
const API_BASE_URL = ""

console.log('API Base URL:', API_BASE_URL);
console.log('Current location:', window.location.href);

export interface ApiResponse<T> {
  data?: T;
  error?: string;
}

export interface RecommendationRequest {
  job_description: string;
  candidates: Candidate[];
  top_k?: number;
  min_similarity?: number;
  invitation_code?: string;
}

export interface RecommendationResponse {
  job_id: string;
  total_candidates: number;
  top_candidates: Array<{
    id: string;
    name: string;
    similarity_score: number;
    rank: number;
    ai_summary?: string;
  }>;
  processing_time_ms: number;
}

class ApiService {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      console.log('Making API request to:', url);

      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      const data = await response.json();

      if (!response.ok) {
        console.error('API request failed:', response.status, data);
        return { error: data.error || 'Request failed' };
      }

      return { data };
    } catch (error) {
      console.error('Network error:', error);
      return { error: error instanceof Error ? error.message : 'Network error' };
    }
  }

  async verifyInvitation(invitationCode?: string): Promise<ApiResponse<{ valid: boolean }>> {
    const payload = invitationCode ? { invitation_code: invitationCode } : {};
    return this.request<{ valid: boolean }>(`/api/verify-invitation`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getRecommendations(
    jobDescription: string,
    candidates: Candidate[],
    invitationCode?: string,
    options: { top_k?: number; min_similarity?: number } = {}
  ): Promise<ApiResponse<RecommendationResponse>> {

    const payload: RecommendationRequest = {
      job_description: jobDescription,
      candidates: candidates.map(candidate => ({
        id: candidate.id,
        name: candidate.name,
        info: candidate.info,
        resume: candidate.resume, // Pass binary data
      })),
      ...options
    };

    if (invitationCode) {
      (payload as RecommendationRequest).invitation_code = invitationCode;
    }

    console.log('Sending recommendation request with payload:', payload);

    return this.request<RecommendationResponse>('/api/match', {
      method: 'POST',
      body: JSON.stringify(payload),
      // files: candidates.map(candidate => candidate.resume)
    });
  }

  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    return this.request<{ status: string }>('/api/health');
  }
}

export const apiService = new ApiService();
export default apiService; 