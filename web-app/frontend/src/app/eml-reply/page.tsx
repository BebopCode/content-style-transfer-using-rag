'use client'
import { useState, ChangeEvent } from 'react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '';

const UploadEmlPage = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [context, setContext] = useState<string>('');
  const [query, setQuery] = useState<string>('');
  const [generatedResponse, setGeneratedResponse] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    // Validate file type
    if (!file.name.endsWith('.eml')) {
      setError('Please upload a valid .eml file');
      setSelectedFile(null);
      return;
    }
    
    setSelectedFile(file);
    setError(null);
    setGeneratedResponse('');
  };

  const handleGenerate = async () => {
    if (!selectedFile) {
      setError('Please select an .eml file first');
      return;
    }

    if (!context.trim() || !query.trim()) {
      setError('Please fill in both context and query fields');
      return;
    }

    setIsLoading(true);
    setGeneratedResponse('');
    setError(null);

    try {
      // Create FormData to send the file and additional parameters
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('context', context);
      formData.append('query', query);

      const apiEndpoint = `${API_BASE_URL}/api/upload-eml`;
      
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log(data);
      const replyContent = data;
      
      setGeneratedResponse(replyContent);
      
    } catch (err) {
      console.error('Generation Error:', err);
      setError(`Failed to generate email: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsLoading(false);
    }
  };

  const inputClasses = "w-full px-3 py-2 border border-black bg-white focus:outline-none focus:ring-1 focus:ring-black disabled:bg-gray-100 disabled:text-gray-500";
  const labelClasses = "block text-sm font-medium mb-2";
  const buttonClasses = "w-full py-2 mt-6 border border-black bg-black text-white font-semibold transition duration-150";
  const disabledButtonClasses = "w-full py-2 mt-6 border border-gray-400 bg-gray-400 text-gray-700 font-semibold cursor-not-allowed";

  return (
    <div className="max-w-lg mx-auto p-6 border border-black shadow-lg">
      <h1 className="text-2xl font-bold mb-6 text-center">Upload EML</h1>
      
      {/* File Upload Section */}
      <div className="mb-4">
        <label className={labelClasses}>
          Select .eml file of the email you want to reply to.
        </label>
        <input
          type="file"
          accept=".eml"
          onChange={handleFileChange}
          disabled={isLoading}
          className="w-full px-3 py-2 border border-black bg-white focus:outline-none focus:ring-1 focus:ring-black disabled:bg-gray-100 file:mr-4 file:py-2 file:px-4 file:border-0 file:bg-black file:text-white file:font-semibold hover:file:bg-gray-800"
        />
        {selectedFile && (
          <p className="text-sm text-gray-700 mt-2">
            Selected: <span className="font-medium">{selectedFile.name}</span>
          </p>
        )}
      </div>

      {/* Context Input */}
      <div className="mb-4">
        <label htmlFor="context" className={labelClasses}>
          Additional Context on how you want to generate the reply
        </label>
        <textarea
          id="context"
          rows={4}
          placeholder="e.g. I am free for a meeting at 16:00 tomorrow"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          disabled={isLoading}
          className={`${inputClasses} resize-none`}
        />
      </div>

      {/* Query Input */}
      <div className="mb-4">
        <label htmlFor="query" className={labelClasses}>
          Semantic keywords for past email look up
        </label>
        <input
          id="query"
          type="text"
          placeholder="e.g. amazon order status"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
          className={inputClasses}
        />
      </div>

      {/* Generate Button */}
      <button 
        onClick={handleGenerate}
        className={isLoading || !selectedFile || !context.trim() || !query.trim() ? disabledButtonClasses : buttonClasses + " hover:bg-gray-800"}
        disabled={isLoading || !selectedFile || !context.trim() || !query.trim()}
      >
        {isLoading ? 'Generating reply...' : 'Generate reply'}
      </button>

      {/* Error Display */}
      {error && (
        <div className="mt-6 p-3 text-red-700 bg-red-100 border border-red-700 font-semibold">
          Error: {error}
        </div>
      )}

      {/* Response Display Section */}
      {generatedResponse && (
        <div className="mt-6 pt-6 border-t border-black">
          <h2 className="text-xl font-bold mb-3">Generated Response</h2>
          <textarea
            readOnly
            rows={12}
            value={generatedResponse}
            className={`${inputClasses} bg-gray-50 font-mono resize-none`}
            placeholder="Your generated email reply will appear here..."
          />
        </div>
      )}
    </div>
  );
}

export default UploadEmlPage;