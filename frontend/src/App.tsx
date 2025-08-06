import { useState } from 'react'
import './App.css'
import type { Candidate } from './shared/types/index'
import { useResponsiveLayout } from './hooks/useResponsiveLayout'
import { simulateProcessing } from './utils/processingUtils'
import { validatePdfFiles } from './utils/fileValidation'
import {
  Header,
  JobDescription,
  ResumeUpload,
  AnalysisResults,
  ResumePreview
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
    const newCandidates: Candidate[] = validationResult.validFiles.map((file, index) => ({
      id: `candidate-${Date.now()}-${index}`,
      name: file.name.replace(/\.pdf$/i, ''),
      resume: file.name // only show file name
    }))

    setCandidates(prev => [...prev, ...newCandidates])

    // reset input
    event.target.value = '';
  }

  const handleTextInput = (text: string) => {
    const newCandidate: Candidate = {
      id: `candidate-${Date.now()}`,
      name: `Candidate ${candidates.length + 1}`,
      resume: text
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
    const processedResults = await simulateProcessing(candidates, setProgress)
    setResults(processedResults)
    setIsProcessing(false)
    setProgress(0)
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

        {/* 2x2 Grid Layout */}
        <div className="grid-layout">
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
  )
}

export default App
