# Talent-Match

This is a take-home assignment for fall intern that implements an AI-powered talent matching system using machine learning to match candidates with job descriptions.

## Overview

Talent-Match is a full-stack application that analyzes resumes and matches them with job descriptions using semantic similarity. The system consists of a React TypeScript frontend and a Flask Python backend with machine learning capabilities.

## Architecture

### System Components

- **Frontend**: React TypeScript application with Vite
- **Backend**: Flask REST API with machine learning services
- **AI Engine**: Sentence Transformers for semantic embeddings
- **Document Processing**: PyPDF2 for resume text extraction

## Backend Documentation

### Architecture Overview

The backend is built using Flask with a modular architecture:

```
talentmatch/
├── app.py              # Main Flask application
├── config.py           # Configuration settings
├── utils.py            # Core utility classes
├── models/             # Data models
├── routes/             # API route handlers
└── services/           # Business logic services
```

### Core Components

#### 1. EmbeddingProcessor (`utils.py`)
- **Purpose**: Generates semantic embeddings from text using pre-trained models
- **Model**: Uses `all-mpnet-base-v2` from Sentence Transformers (~1.5GB)
- **Methods**:
  - `generate_embedding(text)`: Converts text to numerical vector representation
  - `calculate_similarity(embedding1, embedding2)`: Computes cosine similarity between embeddings
  - `_clean_text(text)`: Preprocesses text by removing HTML tags and special characters

#### 2. CandidateProcessor (`utils.py`)
- **Purpose**: Processes candidate resume data and generates embeddings
- **Methods**:
  - `process_candidates(candidates)`: Batch processes candidate resumes
  - `_generate_summary(name, resume_text)`: Creates candidate summaries

#### 3. RecommendationEngine (`utils.py`)
- **Purpose**: Core matching algorithm implementation
- **Method**: `find_top_candidates(job_description, candidates, top_k, min_similarity)`
- **Algorithm**:
  1. Generate embedding for job description
  2. Calculate cosine similarity with each candidate's resume embedding
  3. Filter candidates by minimum similarity threshold
  4. Rank candidates by similarity score
  5. Return top K matches

### Recommendation Process

#### Step-by-Step Algorithm

1. **Input Processing**
   - Job description text is cleaned and preprocessed
   - PDF resumes are converted to base64 and text extracted using PyPDF2

2. **Embedding Generation**
   - Job description converted to 768-dimensional vector using Sentence Transformers
   - Each resume converted to same dimensional space

3. **Similarity Calculation**
   - Cosine similarity computed between job embedding and each candidate embedding
   - Formula: `similarity = (A · B) / (||A|| × ||B||)`
   - Results in scores between -1 (completely dissimilar) and 1 (identical)

4. **Ranking and Filtering**
   - Candidates filtered by minimum similarity threshold (default: 0.1)
   - Sorted by similarity score in descending order
   - Top K candidates returned (default: 10)

### API Endpoints

#### Health Check
- `GET /` - Basic health check
- `GET /api/health` - Detailed health status

#### Candidate Management
- `POST /api/candidates` - Add candidates via JSON
- `POST /api/candidates/upload` - Upload candidate files
- `GET /api/candidates` - Get all stored candidates
- `DELETE /api/candidates` - Clear all candidates
- `DELETE /api/candidates/<id>` - Delete specific candidate

#### Recommendations
- `POST /api/recommendations` - Get recommendations (supports both stored and frontend data)
- `POST /api/match` - Real-time matching with frontend data

#### Key API: `/api/match` (Real-time Matching)

**Request Format**:
```json
{
  "job_description": "Software engineer with Python experience...",
  "candidates": [
    {
      "id": "candidate-1",
      "name": "John Doe",
      "resume": "data:application/pdf;base64,JVBERi0xLjQ..."
    }
  ],
  "top_k": 10,
  "min_similarity": 0.1
}
```

**Response Format**:
```json
{
  "job_description": "Software engineer...",
  "total_candidates": 5,
  "recommendations_count": 3,
  "recommendations": [
    {
      "id": "candidate-1",
      "name": "John Doe",
      "similarity_score": 0.85,
      "summary": "John Doe has relevant experience in...",
      "resume_preview": "Software engineer with 5 years..."
    }
  ],
  "processing_time": "real-time",
  "data_source": "frontend"
}
```

### Configuration

Key configuration parameters in `config.py`:
- `EMBEDDING_MODEL`: Sentence transformer model name
- `UPLOAD_FOLDER`: Directory for file uploads
- `MAX_CONTENT_LENGTH`: Maximum file size limit

## Frontend Documentation

### Architecture Overview

The frontend is a React TypeScript application using Vite:

```
frontend/src/
├── App.tsx                 # Main application component
├── components/            # Reusable UI components
│   ├── JobDescription/    # Job description input
│   ├── ResumeUpload/      # File upload handling
│   ├── AnalysisResults/   # Results display
│   └── ResumePreview/     # Resume viewer
├── lib/                   # API service layer
├── utils/                 # Utility functions
├── hooks/                 # Custom React hooks
└── shared/types/          # TypeScript interfaces
```

### Core Components

#### 1. File Processing (`App.tsx`)
- **PDF Validation**: Only allows PDF files using `validatePdfFiles()`
- **File Reading**: Converts PDFs to base64 using `FileReader.readAsDataURL()`
- **Data Structure**: Creates candidate objects with id, name, and base64 resume data

#### 2. API Integration (`lib/api.ts`)
- **Dynamic URL Detection**: Automatically detects API base URL based on environment
- **Error Handling**: Comprehensive error handling for network requests
- **Type Safety**: Full TypeScript interfaces for all API interactions

#### 3. Processing Pipeline (`utils/processingUtils.ts`)

The frontend processing workflow:

1. **Health Check**: Verifies backend connectivity
2. **Data Preparation**: Formats candidate data for API
3. **API Request**: Sends job description and candidates to `/api/match`
4. **Response Processing**: Transforms API response to frontend format
5. **Progress Tracking**: Updates UI with processing progress

### User Interface Flow

1. **Job Description Input**: User enters job requirements
2. **Resume Upload**: User uploads PDF files or inputs text
3. **File Validation**: System validates PDF format and file size
4. **Analysis Trigger**: User clicks "Analyze" button
5. **Processing**: Real-time API call with progress indicators
6. **Results Display**: Ranked candidates with similarity scores
7. **Resume Preview**: Click on candidate to view full resume

### Data Types

#### Candidate Interface
```typescript
interface Candidate {
  id: string;
  name: string;
  resume: string;          // Base64 encoded PDF data
  info: string;
  similarityScore?: number;
  aiSummary?: string;
}
```

### Error Handling

The frontend implements comprehensive error handling:
- Network connectivity issues
- Invalid file formats
- API response errors
- Missing required data validation

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- Poetry (Python package manager)

### Backend Setup
```bash
cd talentmatch
poetry install
poetry run python -m talentmatch.app
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Usage
1. Start backend server (http://localhost:5000)
2. Start frontend development server (http://localhost:5173)
3. Enter job description
4. Upload PDF resumes or input text
5. Click "Analyze" to get ranked recommendations

## Technical Details

### Machine Learning Approach
- **Model**: `all-mpnet-base-v2` (384M parameters, 768-dimensional embeddings)
- **Similarity Metric**: Cosine similarity
- **Performance**: Sub-second processing for typical resume volumes
- **Accuracy**: Semantic understanding beyond keyword matching

### Security Considerations
- File type validation (PDF only)
- File size limits
- CORS configuration for cross-origin requests
- Input sanitization and text cleaning

### Scalability
- Stateless API design
- In-memory processing (suitable for demo/prototype)
- Modular architecture supports database integration
- Batch processing capabilities
