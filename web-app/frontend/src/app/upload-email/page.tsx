'use client';

import { useState } from 'react';

export default function EmailUploader() {
  const [files, setFiles] = useState<FileList | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(e.target.files);
    }
  };

  const handleUpload = async () => {
    if (!files || files.length === 0) {
      alert('Please select .eml files first');
      return;
    }

    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      
      // Add all selected files to FormData
      for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
      }

const response = await fetch(
  `${process.env.NEXT_PUBLIC_API_URL}/upload-emails/`,
  {
    method: 'POST',
    body: formData,
  }
);


      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
      
      // Clear the file input
      setFiles(null);
      const fileInput = document.getElementById('file-input') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
      
    } catch (error) {
      console.error('Error uploading files:', error);
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6 text-black">Email Uploader</h1>
      
      <div className="space-y-4">
        <div className="border-2 border-dashed border-black rounded-lg p-6 bg-white">
          <input
            id="file-input"
            type="file"
            accept=".eml,application/vnd.ms-outlook"
            multiple
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-700
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border file:border-black
              file:text-sm file:font-semibold
              file:bg-white file:text-black
              hover:file:bg-gray-100"
          />
          {files && (
            <p className="mt-2 text-sm text-black font-medium">
              {files.length} file(s) selected
            </p>
          )}
        </div>

        <button
          onClick={handleUpload}
          disabled={uploading || !files}
          className="w-full bg-black text-white py-2 px-4 rounded-md
            hover:bg-gray-800 disabled:bg-gray-300 disabled:text-gray-500 disabled:cursor-not-allowed
            transition-colors font-medium"
        >
          {uploading ? 'Uploading...' : 'Upload Emails'}
        </button>
      </div>

      {result && (
        <div className="mt-6 p-4 bg-white border-2 border-black rounded-lg">
          <h2 className="font-semibold mb-2 text-black">Upload Results:</h2>
          <div className="space-y-2 text-sm text-black">
            <p>Total files: {result.total_files}</p>
            <p>✓ Successful: {result.successful}</p>
            <p>⊘ Skipped: {result.skipped}</p>
            <p>✗ Failed: {result.failed}</p>
          </div>

          {result.details.success.length > 0 && (
            <div className="mt-4">
              <h3 className="font-medium mb-2 text-black">Successfully uploaded:</h3>
              <ul className="text-sm space-y-1">
                {result.details.success.map((item: any, idx: number) => (
                  <li key={idx} className="text-black">
                    📧 {item.subject || 'No subject'}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.details.failed.length > 0 && (
            <div className="mt-4">
              <h3 className="font-medium mb-2 text-black">Failed:</h3>
              <ul className="text-sm space-y-1">
                {result.details.failed.map((item: any, idx: number) => (
                  <li key={idx} className="text-black">
                    {item.filename}: {item.error}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}