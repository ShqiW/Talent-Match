import { useState } from 'react';
import { apiService } from '../lib/api';

export const ApiTest = () => {
  const [status, setStatus] = useState<string>('');
  const [error, setError] = useState<string>('');

  const testConnection = async () => {
    setStatus('Testing connection...');
    setError('');
    
    try {
      const response = await apiService.healthCheck();
      
      if (response.error) {
        setError(`Connection failed: ${response.error}`);
        setStatus('Failed');
      } else {
        setStatus('Connected successfully!');
        console.log('Health check response:', response.data);
      }
    } catch (err) {
      setError(`Error: ${err instanceof Error ? err.message : 'Unknown error'}`);
      setStatus('Failed');
    }
  };

  return (
    <div style={{ 
      padding: '20px', 
      border: '1px solid #ccc', 
      borderRadius: '8px',
      margin: '10px',
      backgroundColor: '#f9f9f9'
    }}>
      <h3>API Connection Test</h3>
      <button onClick={testConnection} style={{ marginBottom: '10px' }}>
        Test Backend Connection
      </button>
      {status && (
        <div style={{ marginBottom: '10px' }}>
          <strong>Status:</strong> {status}
        </div>
      )}
      {error && (
        <div style={{ color: 'red' }}>
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}; 