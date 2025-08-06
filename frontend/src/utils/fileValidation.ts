export interface FileValidationResult {
  validFiles: File[];
  rejectedFiles: string[];
  hasRejectedFiles: boolean;
}

/**
 * Validates uploaded files to ensure only PDF files are accepted
 * @param files - FileList from input element
 * @returns FileValidationResult with valid and rejected files
 */
export const validatePdfFiles = (files: FileList | null): FileValidationResult => {
  if (!files) {
    return { validFiles: [], rejectedFiles: [], hasRejectedFiles: false };
  }

  const validFiles: File[] = [];
  const rejectedFiles: string[] = [];

  Array.from(files).forEach(file => {
    // Only allow PDF files
    if (file.type === 'application/pdf') {
      validFiles.push(file);
    } else {
      rejectedFiles.push(file.name);
    }
  });

  return {
    validFiles,
    rejectedFiles,
    hasRejectedFiles: rejectedFiles.length > 0
  };
}; 