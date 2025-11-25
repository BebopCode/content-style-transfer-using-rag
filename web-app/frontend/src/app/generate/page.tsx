// app/generate/page.tsx
'use client';

import { useState, ChangeEvent, FormEvent } from 'react';
// Assuming you created the interface in types/generate.ts
import { GenerateInput } from '@/types/generate'; 

const GeneratePage: React.FC = () => {
  const [formData, setFormData] = useState<GenerateInput>({
    incomingMail: '',
    receiver: '',
    sender: '',
    customPrompt: ''
  });
  
  // NEW STATE: To hold the generated email response
  const [generatedResponse, setGeneratedResponse] = useState<string>('');
  // NEW STATE: To manage the loading state during the API call
  const [isLoading, setIsLoading] = useState<boolean>(false);
  // NEW STATE: To hold any error messages
  const [error, setError] = useState<string | null>(null);


  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    // Clear any previous error or response when the user starts typing again
    if (generatedResponse || error) {
      setGeneratedResponse('');
      setError(null);
    }
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    
    setIsLoading(true);
    setGeneratedResponse('');
    setError(null);
    const payload = {
      sender: formData.sender,
      receiver: formData.receiver,
      content: formData.incomingMail,
      custom_prompt: formData.customPrompt
    };
    try {
      // 1. Define the API endpoint (e.g., a Next.js API route)
      const apiEndpoint = 'http://localhost:8000/api/generate'; 
      
      // 2. Make the API call
      const response = await fetch(apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // 3. Handle HTTP errors
      if (!response.ok) {
        throw new Error(`API call failed with status: ${response.status}`);
      }
      
      // 4. Parse the response (assuming the API returns JSON with a 'reply' field)
      const data = await response.json();
      
      // Assuming your API response JSON looks like: { reply: "Generated email content..." }
      console.log(data)
      const replyContent = data || 'No reply content received.';
      
      // 5. Update the state with the received response
      setGeneratedResponse(replyContent);
      
    } catch (err) {
      console.error('Generation Error:', err);
      // 6. Update the state with the error message
      setError(`Failed to generate email: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      // 7. Reset loading state
      setIsLoading(false);
    }
  };

  // --- Monochrome Tailwind CSS Classes ---
  const inputClasses = "w-full px-3 py-2 border border-black bg-white focus:outline-none focus:ring-1 focus:ring-black disabled:bg-gray-100 disabled:text-gray-500";
  const labelClasses = "block text-sm font-medium mb-1 mt-4";
  const buttonClasses = "w-full py-2 mt-6 border border-black bg-black text-white font-semibold transition duration-150";
  const disabledButtonClasses = "w-full py-2 mt-6 border border-gray-400 bg-gray-400 text-gray-700 font-semibold cursor-not-allowed";

  return (
    <div className="max-w-lg mx-auto p-6 border border-black shadow-lg">
      <h1 className="text-2xl font-bold mb-6 text-center">Generate Email Response</h1>
      
      <form onSubmit={handleSubmit}>

        {/* Input Fields */}
        <div>
          <label htmlFor="incomingMail" className={labelClasses}>Incoming Mail</label>
          <textarea
            id="incomingMail"
            name="incomingMail"
            rows={6}
            placeholder="Paste the incoming email content here..."
            value={formData.incomingMail}
            onChange={handleChange}
            required
            className={`${inputClasses} resize-none`}
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="receiver" className={labelClasses}>Your email</label>
          <input
            id="receiver"
            name="receiver"
            type="email" // Changed type to email for better validation
            placeholder="e.g. abc@xyz.com"
            value={formData.receiver}
            onChange={handleChange}
            required
            className={inputClasses}
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="sender" className={labelClasses}>Sender</label>
          <input
            id="sender"
            name="sender"
            type="email" // Changed type to email for better validation
            placeholder="The person you want to reply to"
            value={formData.sender}
            onChange={handleChange}
            required
            className={inputClasses}
            disabled={isLoading}
          />
        </div>

        <div>
          <label htmlFor="customPrompt" className={labelClasses}>Custom Context for e-mail generation</label>
          <input
            id="customPrompt"
            name="customPrompt"
            type="text"
            placeholder="e.g. tell the sender that I am available for meeting at 16 tomorrow"
            value={formData.customPrompt} // Corrected: value should be formData.customPrompt
            onChange={handleChange}
            className={inputClasses}
            disabled={isLoading}
          />
        </div>

        {/* Generate Button */}
        <button 
          type="submit" 
          className={isLoading ? disabledButtonClasses : buttonClasses + " hover:bg-gray-800"}
          disabled={isLoading}
        >
          {isLoading ? 'Generating reply...' : 'Generate reply'}
        </button>
      </form>

      {/* --- Response Display Section --- */}
      
      {error && (
        <div className="mt-6 p-3 text-red-700 bg-red-100 border border-red-700 font-semibold">
          Error: {error}
        </div>
      )}

      {generatedResponse && (
        <div className="mt-6 pt-6 border-t border-black">
          <h2 className="text-xl font-bold mb-3">Generated Response</h2>
          <textarea
            readOnly
            rows={10}
            value={generatedResponse}
            className={`${inputClasses} bg-gray-50 font-mono`}
            placeholder="Your generated email reply will appear here..."
          />
        </div>
      )}
    </div>
  );
}

export default GeneratePage;