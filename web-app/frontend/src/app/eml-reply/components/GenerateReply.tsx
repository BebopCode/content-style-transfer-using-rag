'use client';

import { useState } from 'react';
import { ThreadMessage } from './types';

interface GenerateReplyProps {
  threadMessages: ThreadMessage[];
  myEmail: string;
  selectedRecipient: string;
}

export default function GenerateReply({ 
  threadMessages, 
  myEmail, 
  selectedRecipient 
}: GenerateReplyProps) {
  const [customPrompt, setCustomPrompt] = useState('');
  const [generatedReply, setGeneratedReply] = useState('');
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    if (threadMessages.length === 0) {
      alert('No thread messages to generate reply for');
      return;
    }

    setLoading(true);
    setGeneratedReply('');

    // Get the last message in thread as the one to reply to
    const lastMessage = threadMessages[threadMessages.length - 1];

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/generate`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            sender: myEmail,
            receiver: selectedRecipient,
            content: lastMessage.content,
            custom_prompt: customPrompt,
            thread_messages: threadMessages,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to generate reply');
      }

      const data = await response.json();
      setGeneratedReply(data);
    } catch (error) {
      console.error('Error generating reply:', error);
      alert('Error generating reply. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mt-6 p-4 border-2 border-black rounded-md bg-white">
      <h3 className="text-lg font-semibold text-black mb-4">Generate Reply</h3>
      
      <div className="mb-4">
        <label 
          htmlFor="custom-prompt" 
          className="block text-sm font-medium text-black mb-2"
        >
          Give context for generation
        </label>
        <textarea
          id="custom-prompt"
          value={customPrompt}
          onChange={(e) => setCustomPrompt(e.target.value)}
          placeholder="E.g., Be formal, mention the deadline is extended, ask about the project status..."
          className="w-full px-4 py-2 border-2 border-black rounded-md
            focus:outline-none focus:ring-2 focus:ring-black
            text-black placeholder-gray-400 min-h-[100px] resize-y"
        />
      </div>

      <button
        onClick={handleGenerate}
        disabled={loading || threadMessages.length === 0}
        className="w-full bg-black text-white py-2 px-4 rounded-md
          hover:bg-gray-800 disabled:bg-gray-300 disabled:text-gray-500
          disabled:cursor-not-allowed transition-colors font-medium"
      >
        {loading ? 'Generating...' : 'Generate Reply for Thread'}
      </button>

      {generatedReply && (
        <div className="mt-4">
          <label className="block text-sm font-medium text-black mb-2">
            Generated Reply
          </label>
          <div className="p-4 border-2 border-gray-300 rounded-md bg-gray-50">
            <p className="text-sm text-black whitespace-pre-wrap">{generatedReply}</p>
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(generatedReply)}
            className="mt-2 text-sm text-black underline hover:no-underline"
          >
            Copy to clipboard
          </button>
        </div>
      )}
    </div>
  );
}