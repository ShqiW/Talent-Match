# Talent-Match

AI-powered resume matching system that uses machine learning to intelligently match candidate resumes with job descriptions.

## Project Overview

Talent-Match is a full-stack application that analyzes the compatibility between candidate resumes and job requirements through semantic similarity analysis. The system consists of a React TypeScript frontend and a Flask Python backend, integrated with advanced machine learning capabilities.

## System Architecture

### Core Components

- **Frontend**: React + TypeScript + Vite
- **Backend**: Flask RESTful API
- **AI Engine**: Sentence Transformers semantic embeddings
- **Document Processing**: PyPDF2 PDF text extraction
- **Intelligent Analysis**: OpenAI/DeepSeek LLM for candidate summaries

### Project Structure

```
Talent-Match/
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── App.tsx          # Main application component
│   │   ├── components/      # UI components
│   │   │   ├── JobDescription/     # Job description input
│   │   │   ├── ResumeUpload/       # Resume upload
│   │   │   ├── AnalysisResults/    # Results display
│   │   │   └── ResumePreview/      # Resume preview
│   │   ├── lib/             # API service layer
│   │   ├── utils/           # Utility functions
│   │   └── shared/types/    # TypeScript type definitions
│   └── package.json
├── talentmatch/             # Flask backend application
│   ├── app.py              # Flask main application
│   ├── config.py           # Configuration file
│   ├── utils.py            # Utility functions
│   ├── etc/                # Core algorithms
│   │   ├── embeddingprocessor.py  # Embedding processor
│   │   └── recommendengine.py     # Recommendation engine
│   ├── models/             # Data models
│   ├── routes/             # API routes
│   └── services/           # Business logic services
└── requirements.txt        # Python dependencies
```

## Core Components

### 1. EmbeddingProcessor (`talentmatch/etc/embeddingprocessor.py`)
**Purpose**: Text semantic embedding generation
- **Model**: `all-mpnet-base-v2` (768-dimensional vectors, ~1.5GB)
- **Key Methods**:
  - `generate_embedding(text)`: Converts text to numerical vectors
  - `calculate_similarity(emb1, emb2)`: Computes cosine similarity
  - `_clean_text(text)`: Text preprocessing and cleaning

### 2. RecommendationEngine (`talentmatch/etc/recommendengine.py`)
**Purpose**: Core intelligent matching algorithm
- **Main Method**: `find_top_candidates(job_desc, candidates, top_k, min_similarity)`
- **Algorithm Flow**:
  1. Generate ideal candidate description as upper bound reference
  2. Create semantic embeddings for job description
  3. Calculate similarity ratio between candidates and ideal candidate
  4. Use LLM to generate personalized candidate summaries
  5. Sort by similarity and return Top-K results

### 3. Frontend Core Component (`frontend/src/App.tsx`)
**Purpose**: User interface and interaction logic
- **File Processing**: PDF validation, Base64 encoding, file reading
- **API Integration**: Communication interface with backend services
- **State Management**: Candidate data, analysis results, UI state
- **Responsive Layout**: Interface adaptation for different screen sizes

## Main API Endpoints

### Real-time Matching: `POST /api/match`
**Request Format**:
```json
{
  "job_description": "Python Software Engineer...",
  "candidates": [
    {
      "id": "candidate-1",
      "name": "John Doe",
      "resume": "base64-encoded PDF data...",
      "info": "additional information"
    }
  ],
  "top_k": 10,
  "min_similarity": 0.1,
  "invitation_code": "verification code"
}
```

**Response Format**:
```json
{
  "recommendations": [
    {
      "id": "candidate-1",
      "name": "John Doe",
      "similarity_score": 0.85,
      "summary": "AI-generated candidate match analysis...",
      "resume_text": "resume text content..."
    }
  ],
  "total_candidates": 5,
  "recommendations_count": 3
}
```

## Technical Features

### Intelligent Analysis
- **Semantic Understanding**: Deep semantic analysis beyond keyword matching
- **AI Enhancement**: Integrated LLM for personalized candidate evaluation
- **Dynamic Scoring**: Relative scoring mechanism based on ideal candidates

### Performance Optimization
- **Real-time Processing**: Sub-second response times
- **Modular Design**: Supports independent scaling and maintenance
- **Resource Management**: Efficient memory and computational resource utilization

### Security Features
- **File Validation**: Strict PDF file type checking
- **Input Sanitization**: Comprehensive text preprocessing and security filtering
- **Access Control**: Invitation code verification mechanism

## Quick Start

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

### Usage Flow
1. Start backend service (http://localhost:7860)
2. Start frontend development server (http://localhost:5173)
3. Enter invitation code and job description
4. Upload PDF resumes or input text
5. Click "Analyze" to get ranked matching results

## Known Issues and Future Improvements

### Current Limitations

#### 1. Invalid Job Description Handling
- **Issue**: When job descriptions contain meaningless text strings (e.g., "dsfdse" or other gibberish), the similarity scores can exceed 100%
- **Root Cause**: The ideal candidate generation becomes unreliable with invalid input, leading to unstable baseline similarity calculations
- **Impact**: Distorted scoring that doesn't reflect actual job-candidate compatibility
- **Status**: Input validation for job description quality has not been implemented due to time constraints

#### 2. Limited Discrimination for Unrelated Resumes
- **Issue**: Among candidates with low relevance to the job position, similarity scores show minimal differentiation
- **Root Cause**: When most candidates are poor matches, the relative scoring system struggles to meaningfully distinguish between different levels of irrelevance
- **Impact**: Reduced ranking effectiveness when the candidate pool lacks strong matches
- **Potential Solutions**: 
  - Implement absolute minimum threshold filtering
  - Add secondary ranking criteria for tie-breaking
  - Enhance embedding models with domain-specific fine-tuning

#### 3. UI and Presentation Issues
- **Analysis Display Format**: The top-K candidate analysis is currently generated in markdown format, resulting in poor presentation quality in the UI
- **Root Cause**: Raw markdown text is displayed without proper rendering, making the analysis difficult to read
- **Impact**: Reduced user experience and readability of candidate evaluations
- **Proposed Solution**: Implement proper markdown-to-HTML rendering or restructure analysis output format

#### 4. PDF Preview Deployment Issues ✅ **RESOLVED**
- **Previous Issue**: Resume preview functionality failed on Hugging Face deployment due to Content Security Policy (CSP) restrictions
- **Root Cause**: CSP headers prevented PDF display in embedded viewers or iframes
- **Solution Implemented**: Migrated frontend to GitHub Pages while keeping backend on Hugging Face Spaces
- **Current Status**: PDF preview functionality now works correctly in the distributed deployment setup

#### 5. Ideal Candidate Generation Flexibility
- **Current Limitation**: The system automatically generates ideal candidate descriptions using LLM without employer input
- **Enhancement Needed**: Provide employers with the option to upload their own ideal candidate resume
- **Proposed Workflow**:
  - **Option A**: Employer uploads an ideal candidate resume (PDF format)
  - **Option B**: System auto-generates ideal candidate description (current behavior)
  - Allow switching between modes based on employer preference
- **Benefits**: More accurate similarity baseline when employers have specific candidate profiles in mind

#### 6. Processing Time Performance
- **Current Issue**: Analysis takes longer due to local model processing compared to cloud-based embedding APIs
- **Root Cause**: Sequential processing of embeddings using local `all-mpnet-base-v2` model
- **Impact**: Users experience longer wait times, especially when analyzing multiple candidates
- **Trade-off Reasoning**: Chosen local processing for cost control, data privacy, and reliability
- **Potential Solutions**:
  - Implement parallel processing for multiple candidates
  - Add progress indicators and estimated time remaining
  - Consider hybrid approach (API + local model fallback)
  - Optimize model loading and caching strategies

#### 7. Enhanced Resume Preview with Relevance Highlighting
- **Current Limitation**: Resume preview displays plain text without visual indicators of relevance to the job description
- **Enhancement Needed**: Transform resume preview into an annotated resume with visual relevance indicators
- **Proposed Features**:
  - **Color Coding**: Highlight sentences/phrases with high relevance to job requirements in different colors
  - **Text Emphasis**: Use bold formatting for key skills and experiences that match job criteria
  - **Relevance Scoring**: Display inline relevance scores for different resume sections
  - **Interactive Highlighting**: Allow users to hover over highlighted text to see why it's relevant
- **Implementation Approach**: Use NLP techniques to identify relevant text segments and apply visual annotations
- **Benefits**: Faster resume review process and clearer understanding of candidate-job fit
- **Status**: Not implemented due to time constraints

### Future Enhancements Needed
- **Input Validation**: Add job description quality assessment before processing
- **Scoring Bounds**: Implement upper and lower bounds for similarity scores
- **Multi-factor Ranking**: Combine semantic similarity with other relevance metrics
- **Error Handling**: Graceful degradation when ideal candidate generation fails
- **UI Improvements**: Implement proper markdown rendering for analysis results
- **~~CSP Compliance~~**: ✅ Resolved through distributed deployment architecture
- **Flexible Baseline**: Support both manual and automatic ideal candidate specification
- **Annotated Resume Preview**: Implement relevance highlighting with color coding and interactive features
- **Performance Optimization**: Implement parallel processing and caching for faster analysis

## Live Demo

The application uses a distributed deployment approach to overcome platform limitations:

### Backend (API Server)
**Hugging Face Spaces**: [https://huggingface.co/spaces/ShqiW/talentMatch-backend](https://huggingface.co/spaces/ShqiW/talentMatch-backend)
- Hosts the Flask API server and machine learning models
- Handles resume processing and similarity calculations

### Frontend (User Interface)
**GitHub Pages**: [https://shqiw.coredumped.tech/Talent-Match/]
- Hosts the React TypeScript user interface
- Provides full PDF preview functionality without CSP restrictions

### Deployment Architecture Decision
Initially, both frontend and backend were deployed together on Hugging Face Spaces. However, due to Content Security Policy (CSP) restrictions on Hugging Face, PDF preview functionality was blocked. To resolve this issue, the frontend was migrated to GitHub Pages, which allows unrestricted PDF rendering while maintaining seamless API communication with the backend on Hugging Face.

> **Note**: Due to API security and cost considerations, an invitation code is required to access the live demo. Please contact shqiwen@gmail.com.

## Similarity Calculation

The core matching algorithm uses a sophisticated similarity calculation approach:

### Model Selection: all-mpnet-base-v2

The system uses the `all-mpnet-base-v2` model from Sentence Transformers for generating semantic embeddings. This model was specifically chosen based on several key considerations:

#### Performance and Quality Balance
- **Model Size**: 420MB (manageable for deployment)
- **Vector Dimensions**: 768-dimensional embeddings (optimal balance between expressiveness and computational efficiency)
- **Performance**: Achieves state-of-the-art performance on semantic textual similarity benchmarks
- **Speed**: Fast inference time suitable for real-time applications

#### Language and Domain Suitability
- **English Optimization**: Primarily designed for English text, which aligns with the assumption that most professional resumes and job descriptions are in English
- **General Domain Knowledge**: Trained on diverse text data, making it effective for professional documents across various industries
- **Semantic Understanding**: Excels at capturing semantic meaning beyond simple keyword matching

#### Hardware and Computational Constraints
- **Memory Requirements**: ~1.5GB total model size (including dependencies) - feasible for standard deployment environments
- **CPU Compatibility**: Runs efficiently on CPU-only environments (important for cost-effective deployment on platforms like Hugging Face Spaces)
- **Inference Speed**: Sub-second embedding generation for typical resume/job description lengths
- **Scalability**: Lightweight enough to handle multiple concurrent requests

#### Alternative Models Considered
- **Larger Models** (e.g., `all-mpnet-large`): Better performance but significantly higher computational requirements
- **Multilingual Models**: Not necessary given the English-focused use case
- **Domain-Specific Models**: Limited availability for HR/recruitment domain, general models provide better versatility

This model choice represents an optimal trade-off between accuracy, speed, and resource efficiency for the talent matching use case.

#### Trade-offs and Limitations

**Local Model vs. API Services**:
- **Current Approach**: Using local `all-mpnet-base-v2` model for embedding generation
- **Processing Time**: Analysis can take longer compared to cloud-based embedding APIs (e.g., OpenAI's text-embedding models)
- **Reasons for Local Model Choice**:
  - **Cost Control**: No per-request API charges, especially important for multiple candidate processing
  - **Data Privacy**: Resume data processed locally without sending to external services
  - **Reliability**: No dependency on external API availability or rate limits
  - **Consistency**: Deterministic results without API version changes affecting embeddings

**Performance Impact**:
- **Initial Load**: First-time model loading adds ~10-15 seconds startup time
- **Processing Time**: Each embedding generation takes 1-3 seconds per document (depending on text length)
- **Batch Processing**: Multiple candidates processed sequentially, leading to cumulative wait times

**Alternative Considered**:
- **API-based Solutions**: Would provide faster per-request processing but introduce cost, privacy, and reliability concerns
- **Future Enhancement**: Could implement hybrid approach - API for speed, local model as fallback

### Algorithm Overview
1. **Ideal Candidate Generation**: The system first queries an LLM (DeepSeek) to generate a description of the ideal candidate based on the job description
2. **Embedding Creation**: Both the job description and ideal candidate description are converted to 768-dimensional vectors using the `all-mpnet-base-v2` model
3. **Baseline Similarity**: Calculate cosine similarity between job description and ideal candidate embeddings as the upper bound reference
4. **Candidate Scoring**: For each candidate:
   - Generate embedding from their resume text
   - Calculate cosine similarity with job description embedding
   - Normalize by dividing by the baseline similarity: `candidate_score = similarity(job, candidate) / similarity(job, ideal_candidate)`

### Mathematical Formula
```
similarity_score = cos(job_embedding, candidate_embedding) / cos(job_embedding, ideal_candidate_embedding)
```

Where cosine similarity is calculated as:
```
cos(A, B) = (A · B) / (||A|| × ||B||)
```

### Benefits of This Approach
- **Dynamic Scaling**: Scores are relative to the theoretical best match for each specific job
- **Consistent Interpretation**: Scores closer to 1.0 indicate better alignment with the ideal candidate profile
- **Context Awareness**: The ideal candidate baseline adapts to different job requirements
- **Improved Ranking**: Provides more meaningful comparisons across different types of positions
