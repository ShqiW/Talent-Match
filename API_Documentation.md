# Talent Match API Documentation

## Overview
This API provides candidate recommendation services that analyze job descriptions against candidate resumes to find the best matches using cosine similarity and AI-generated summaries.

---

## **Talent Match**
**Generates recommendations for job candidates based on resume similarity**

**Method** 
POST

**Endpoint**  
/api/recommendations

**Status Codes**  
Success: 200  
Failure: 400, 500

**Body**
```json
{
  job_description: string;
  candidates: {
    text_input?: Array<{
      id?: string;
      name: string;
      resume_text: string;
    }>;
    bulk_text?: string;
    uploaded_files?: Array<{
      file_id: string;
      filename: string;
      extracted_text: string;
      candidate_name?: string;
    }>;
  };
  options?: {
    top_k?: number; // default: 5
    generate_summary?: boolean; // default: true
  };
}
```

**Response**
```json
{
  job_id: string;
  total_candidates: number;
  input_sources: {
    manual_entries: number;
    bulk_parsed: number;
    uploaded_files: number;
  };
  top_candidates: Array<{
    id: string;
    name: string;
    source: "text_input" | "bulk_text" | "uploaded_file";
    similarity_score: number;
    rank: number;
    ai_summary?: string;
    filename?: string;
  }>;
  processing_time_ms: number;
}
```

**Example Request**
```json
{
  "job_description": "We are looking for a Senior Software Engineer with React and Node.js experience...",
  "candidates": {
    "text_input": [
      {
        "id": "manual_001",
        "name": "John Doe",
        "resume_text": "Experienced software engineer with 5 years of React development..."
      }
    ],
    "bulk_text": "CANDIDATE 1: Alice Johnson\nSoftware Engineer with React expertise...\n\nCANDIDATE 2: Bob Wilson\nBackend developer with Node.js...",
    "uploaded_files": [
      {
        "file_id": "upload_abc123",
        "filename": "resume_alice.pdf",
        "extracted_text": "Alice Johnson\nSenior Developer with 7 years experience...",
        "candidate_name": "Alice Johnson"
      }
    ]
  },
  "options": {
    "top_k": 5,
    "generate_summary": true
  }
}
```

**Example Response**
```json
{
  "job_id": "job_12345",
  "total_candidates": 4,
  "input_sources": {
    "manual_entries": 1,
    "bulk_parsed": 2,
    "uploaded_files": 1
  },
  "top_candidates": [
    {
      "id": "upload_abc123",
      "name": "Alice Johnson",
      "source": "uploaded_file",
      "filename": "resume_alice.pdf",
      "similarity_score": 0.8547,
      "rank": 1,
      "ai_summary": "Strong technical match with 7+ years React experience and proven track record in full-stack development."
    },
    {
      "id": "bulk_parsed_001",
      "name": "Alice Johnson",
      "source": "bulk_text",
      "similarity_score": 0.8234,
      "rank": 2,
      "ai_summary": "Excellent React expertise aligns perfectly with job requirements for senior-level position."
    },
    {
      "id": "manual_001",
      "name": "John Doe",
      "source": "text_input",
      "similarity_score": 0.8156,
      "rank": 3,
      "ai_summary": "Solid 5-year React development background matches core technical requirements."
    }
  ],
  "processing_time_ms": 2340
}
```

---

## **Upload Resumes**
**Uploads and processes resume files for candidate analysis**

**Method**  
POST

**Endpoint**  
/api/upload-resumes

**Status Codes**  
Success: 200  
Failure: 400, 413, 500

**Body**  
`multipart/form-data`
- `files[]`: File[] (PDF, DOCX)
- `parse_names`: boolean (optional)

**Response**
```json
{
  uploaded_files: Array<{
    file_id: string;
    filename: string;
    extracted_text: string;
    candidate_name?: string;
    status: "success" | "error";
    error?: string;
  }>;
}
```

**Example Response**
```json
{
  "uploaded_files": [
    {
      "file_id": "upload_abc123",
      "filename": "resume_alice.pdf",
      "extracted_text": "Alice Johnson\nSenior Developer with 7 years experience in React, Node.js, and full-stack development...",
      "candidate_name": "Alice Johnson",
      "status": "success"
    },
    {
      "file_id": "upload_def456",
      "filename": "corrupted.pdf",
      "status": "error",
      "error": "Unable to extract text from PDF file"
    }
  ]
}
```

---

## **Parse Bulk Text**
**Parses bulk text input to extract individual candidate information**

**Method**  
POST

**Endpoint**  
/api/parse-bulk-text

**Status Codes**  
Success: 200  
Failure: 400, 500

**Body**
```json
{
  bulk_text: string;
  separator_hints?: string[];
}
```

**Response**
```json
{
  parsed_candidates: Array<{
    id: string;
    name: string;
    resume_text: string;
    confidence: number;
  }>;
  parsing_stats: {
    total_found: number;
    avg_confidence: number;
  };
}
```

**Example Request**
```json
{
  "bulk_text": "CANDIDATE 1: Alice Johnson\nSoftware Engineer with React expertise and 5 years of experience...\n\n---\n\nCANDIDATE 2: Bob Wilson\nBackend developer specializing in Node.js and microservices architecture...",
  "separator_hints": ["CANDIDATE", "---", "Name:", "Resume:"]
}
```

**Example Response**
```json
{
  "parsed_candidates": [
    {
      "id": "bulk_001",
      "name": "Alice Johnson",
      "resume_text": "Software Engineer with React expertise and 5 years of experience...",
      "confidence": 0.95
    },
    {
      "id": "bulk_002",
      "name": "Bob Wilson",
      "resume_text": "Backend developer specializing in Node.js and microservices architecture...",
      "confidence": 0.88
    }
  ],
  "parsing_stats": {
    "total_found": 2,
    "avg_confidence": 0.915
  }
}
```

---

## **Text Similarity**
**Calculates cosine similarity between two text inputs**

**Method**  
POST

**Endpoint**  
/api/similarity

**Status Codes**  
Success: 200  
Failure: 400, 500

**Body**
```json
{
  text1: string;
  text2: string;
}
```

**Response**
```json
{
  similarity: number;
  text1_length: number;
  text2_length: number;
}
```

**Example Request**
```json
{
  "text1": "Software engineer with React and Node.js experience",
  "text2": "Full-stack developer specializing in React and backend technologies"
}
```

**Example Response**
```json
{
  "similarity": 0.8547,
  "text1_length": 52,
  "text2_length": 67
}
```

---

## **Health Check**
**Checks API service health and model status**

**Method**  
GET

**Usable by**  
Public

**Endpoint**  
/health

**Status Codes**  
Success: 200  
Failure: 503

**Response**
```json
{
  status: "healthy" | "unhealthy";
  model_loaded: boolean;
  timestamp: string;
}
```

**Example Response**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "timestamp": "2025-01-08T10:30:00Z"
}
```

---

## Error Handling

All endpoints return consistent error responses:

```json
{
  "error": string;
  "code": string;
  "details"?: string;
}
```

**Common Error Codes:**
- `VALIDATION_ERROR`: Invalid request format or missing required fields
- `FILE_PROCESSING_ERROR`: Error processing uploaded files
- `MODEL_ERROR`: Error in ML model processing
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `INTERNAL_SERVER_ERROR`: Unexpected server error

**Example Error Response**
```json
{
  "error": "Invalid request format",
  "code": "VALIDATION_ERROR",
  "details": "job_description is required"
}
```

---

## Rate Limits

- **Recommendations**: 10 requests per minute per user
- **File Upload**: 5 uploads per minute per user (max 10MB per file)
- **Similarity**: 100 requests per minute per user

---

## Authentication

All endpoints (except `/health`) require authentication via Bearer token:

```
Authorization: Bearer <your-jwt-token>
```

---

## Frontend Integration Examples

### JavaScript/TypeScript
```javascript
// Calculate recommendations
const getRecommendations = async (jobDescription, candidates) => {
  const response = await fetch('/api/recommendations', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      job_description: jobDescription,
      candidates: candidates,
      options: { top_k: 5, generate_summary: true }
    })
  });
  
  return await response.json();
};

// Upload resumes
const uploadResumes = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files[]', file));
  formData.append('parse_names', 'true');
  
  const response = await fetch('/api/upload-resumes', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });
  
  return await response.json();
};
```

### Python
```python
import requests

# Calculate similarity
def calculate_similarity(text1, text2, token):
    response = requests.post(
        'http://localhost:5000/api/similarity',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        json={'text1': text1, 'text2': text2}
    )
    return response.json()

# Get recommendations
def get_recommendations(job_desc, candidates, token):
    response = requests.post(
        'http://localhost:5000/api/recommendations',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}'
        },
        json={
            'job_description': job_desc,
            'candidates': candidates,
            'options': {'top_k': 5, 'generate_summary': True}
        }
    )
    return response.json()
```

---

## Data Models

### Candidate Object
```typescript
interface Candidate {
  id?: string;
  name: string;
  resume_text: string;
  source?: 'text_input' | 'bulk_text' | 'uploaded_file';
  filename?: string;
}
```

### Recommendation Result
```typescript
interface RecommendationResult {
  id: string;
  name: string;
  source: 'text_input' | 'bulk_text' | 'uploaded_file';
  similarity_score: number;
  rank: number;
  ai_summary?: string;
  filename?: string;
}
```

### Options
```typescript
interface RecommendationOptions {
  top_k?: number; // default: 5, max: 20
  generate_summary?: boolean; // default: true
  min_similarity?: number; // default: 0.0
}
```