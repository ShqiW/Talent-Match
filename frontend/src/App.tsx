import { useState } from 'react'
import './App.css'
import type { Candidate } from './shared/types/index'
import { useResponsiveLayout } from './hooks/useResponsiveLayout'
import { processCandidatesWithAPI } from './utils/processingUtils'
import { validatePdfFiles } from './utils/fileValidation'
import {
  Header,
  JobDescription,
  ResumeUpload,
  AnalysisResults,
  ResumePreview,
  ApiTest
} from './components'

function App() {
  const [jobDescription, setJobDescription] = useState('')
  const [candidates, setCandidates] = useState<Candidate[]>([])

  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [results, setResults] = useState<Candidate[]>([])
  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null)

  // use responsive layout hook
  useResponsiveLayout()

  // file processing function - now includes PDF validation
  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files

    // validate file type
    const validationResult = validatePdfFiles(files)

    // show rejected files
    if (validationResult.hasRejectedFiles) {
      alert(`The following files were rejected (only PDF files are allowed):\n${validationResult.rejectedFiles.join('\n')}`);
    }

    // if no valid files, return
    if (validationResult.validFiles.length === 0) {
      // reset input
      event.target.value = '';
      return;
    }

    // convert files to candidates
    const fileReadPromises = Array.from(validationResult.validFiles).map((file, index) => {
      return new Promise<Candidate>((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => {
          resolve({
            id: `candidate-${Date.now()}-${index}`,
            name: file.name.replace(/\.pdf$/i, ''),
            // resume: reader.result as ArrayBuffer, // binary data as ArrayBuffer
            // resume: reader.result as string, // Base64 encoded string
            resume: btoa(String.fromCharCode(...new Uint8Array(reader.result as ArrayBuffer))), // Base64 encoded string
            info: '', // can be filled with additional info if needed
          })
        }
        reader.onerror = reject
        // reader.readAsArrayBuffer(file) // reads file as ArrayBuffer
        reader.readAsArrayBuffer(file) // reads file as Base64 string
      })
    })

    Promise.all(fileReadPromises).then(newCandidates => {
      setCandidates(prev => [...prev, ...newCandidates])
    })

    // setCandidates(prev => [...prev, ...newCandidates])

    // reset input
    event.target.value = '';
  }

  const handleTextInput = (text: string) => {
    const newCandidate: Candidate = {
      id: `candidate-${Date.now()}`,
      name: `Candidate ${candidates.length + 1}`,
      // convert text to base64 string
      resume: btoa(unescape(encodeURIComponent(text))), // encode text to Base64
      info: text
    }
    setCandidates(prev => [...prev, newCandidate])
  }

  const handleAnalyze = async () => {
    if (!jobDescription.trim()) {
      alert('Please enter a job description')
      return
    }
    if (candidates.length === 0) {
      alert('Please add at least one candidate resume')
      return
    }

    setIsProcessing(true)
    try {
      const processedResults = await processCandidatesWithAPI(candidates, jobDescription, setProgress)
      setResults(processedResults)
    } catch (error) {
      console.error('Processing failed:', error)
      alert(error instanceof Error ? error.message : '处理失败，请重试')
    } finally {
      setIsProcessing(false)
      setProgress(0)
    }
  }

  const removeCandidate = (id: string) => {
    setCandidates(prev => prev.filter(c => c.id !== id))
  }

  const clearAll = () => {
    setCandidates([])
    setResults([])
    setJobDescription('')
    setSelectedCandidate(null)
  }

  const handleCandidateClick = (candidate: Candidate) => {
    setSelectedCandidate(candidate)
  }

  return (
    <div className="app">
      <div className="container">
        <Header />

        {/* API Test Component */}
        <ApiTest />

        {/* 2x2 Grid Layout */}
        <div display='block'>
          {/* Collapse JobDescription and ResumeUpload when a candidate is selected */}
          {selectedCandidate && (
            <button
              style={{ marginBottom: '1rem' }}
              onClick={() => setSelectedCandidate(null)}
            >
              Show Job Description & Resume Upload
            </button>
          )}
          <div style={{ display: selectedCandidate ? 'none' : 'flex' }}>
            <JobDescription
              jobDescription={jobDescription}
              onJobDescriptionChange={setJobDescription}
            />

            <ResumeUpload
              candidates={candidates}
              onFileUpload={handleFileUpload}
              onTextInput={handleTextInput}
              onRemoveCandidate={removeCandidate}
              onAnalyze={handleAnalyze}
              onClearAll={clearAll}
              isProcessing={isProcessing}
              jobDescription={jobDescription}
            />
          </div>

          {/*           
          <JobDescription
            jobDescription={jobDescription}
            onJobDescriptionChange={setJobDescription}
          />

          <ResumeUpload
            candidates={candidates}
            onFileUpload={handleFileUpload}
            onTextInput={handleTextInput}
            onRemoveCandidate={removeCandidate}
            onAnalyze={handleAnalyze}
            onClearAll={clearAll}
            isProcessing={isProcessing}
            jobDescription={jobDescription}
          /> */}

          {/* Analysis Results and Resume Preview */}
          <div style={{ display: results ? 'flex' : 'none' }}>
            <AnalysisResults
              results={results}
              isProcessing={isProcessing}
              progress={progress}
              candidates={candidates}
              selectedCandidate={selectedCandidate}
              onCandidateClick={handleCandidateClick}
            />

            <ResumePreview selectedCandidate={selectedCandidate} />
          </div>

        </div>
      </div>
    </div>
  )
}

export default App
