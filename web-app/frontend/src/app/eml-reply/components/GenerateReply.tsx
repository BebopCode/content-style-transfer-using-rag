'use client';

import { useState } from 'react';
import { ThreadMessage } from './types';

interface GenerateReplyProps {
  threadMessages: ThreadMessage[];
  myEmail: string;
  selectedRecipient: string;
}

interface GeneratedReplies {
  full_context_reply: string;
  thread_only_reply: string;
}

interface ReplyEvaluation {
  style_transfer: number | null;
  content_preservation: number | null;
  naturalness: number | null;
}

interface EvaluationResult {
  timestamp: string;
  thread_subject: string;
  custom_prompt: string;
  RAG: {
    reply: string;
    style_transfer: number;
    content_preservation: number;
    naturalness: number;
  };
  noRAG: {
    reply: string;
    style_transfer: number;
    content_preservation: number;
    naturalness: number;
  };
}

export default function GenerateReply({ 
  threadMessages, 
  myEmail, 
  selectedRecipient 
}: GenerateReplyProps) {
  const [customPrompt, setCustomPrompt] = useState('');
  const [generatedReplies, setGeneratedReplies] = useState<GeneratedReplies | null>(null);
  const [loading, setLoading] = useState(false);
  
  // Evaluation states for both replies
  const [reply1Eval, setReply1Eval] = useState<ReplyEvaluation>({
    style_transfer: null,
    content_preservation: null,
    naturalness: null,
  });
  
  const [reply2Eval, setReply2Eval] = useState<ReplyEvaluation>({
    style_transfer: null,
    content_preservation: null,
    naturalness: null,
  });

  const handleGenerate = async () => {
    if (threadMessages.length === 0) {
      alert('No thread messages to generate reply for');
      return;
    }

    setLoading(true);
    setGeneratedReplies(null);
    // Reset evaluations
    setReply1Eval({ style_transfer: null, content_preservation: null, naturalness: null });
    setReply2Eval({ style_transfer: null, content_preservation: null, naturalness: null });

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
      setGeneratedReplies(data);
    } catch (error) {
      console.error('Error generating reply:', error);
      alert('Error generating reply. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    alert(`${label} copied to clipboard!`);
  };

  const isEvaluationComplete = (evalData: ReplyEvaluation): boolean => {
    return evalData.style_transfer !== null && 
           evalData.content_preservation !== null && 
           evalData.naturalness !== null;
  };

  const canSaveResults = (): boolean => {
    return isEvaluationComplete(reply1Eval) && isEvaluationComplete(reply2Eval);
  };

  const saveResults = () => {
    if (!generatedReplies || !canSaveResults()) {
      alert('Please complete all evaluations for both replies before saving.');
      return;
    }

    const threadSubject = threadMessages[0]?.subject || 'Unknown Subject';

    const result: EvaluationResult = {
      timestamp: new Date().toISOString(),
      thread_subject: threadSubject,
      custom_prompt: customPrompt,
      RAG: {
        reply: generatedReplies.full_context_reply,
        style_transfer: reply1Eval.style_transfer!,
        content_preservation: reply1Eval.content_preservation!,
        naturalness: reply1Eval.naturalness!,
      },
      noRAG: {
        reply: generatedReplies.thread_only_reply,
        style_transfer: reply2Eval.style_transfer!,
        content_preservation: reply2Eval.content_preservation!,
        naturalness: reply2Eval.naturalness!,
      },
    };

    // Download as JSON file
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `evaluation_${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert('Evaluation results saved!');
  };

  const StyleTransferScale = ({ 
    value, 
    onChange 
  }: { 
    value: number | null; 
    onChange: (val: number) => void;
  }) => (
    <div className="space-y-2">
      <p className="text-xs font-medium text-black">Style Transfer (1-5)</p>
      <div className="flex gap-2">
        {[1, 2, 3, 4, 5].map((num) => (
          <button
            key={num}
            onClick={() => onChange(num)}
            className={`w-8 h-8 rounded-full border-2 text-sm font-medium transition-colors
              ${value === num 
                ? 'bg-black text-white border-black' 
                : 'bg-white text-black border-gray-300 hover:border-black'
              }`}
          >
            {num}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-500">
     1 = Completely different styles <br/>
     2 = Mostly different styles with minor similarities <br/>
     3 = Moderately similar styles with notable differences <br/>
     4 = Very similar styles with minor differences <br/>
     5 = Completely identical styles <br/>
      </p>
    </div>
  );

  const BinaryScale = ({ 
    label, 
    description,
    value, 
    onChange 
  }: { 
    label: string;
    description: string;
    value: number | null; 
    onChange: (val: number) => void;
  }) => (
    <div className="space-y-2">
      <p className="text-xs font-medium text-black">{label}</p>
      <div className="flex gap-2">
        {[0, 1].map((num) => (
          <button
            key={num}
            onClick={() => onChange(num)}
            className={`px-4 py-2 rounded border-2 text-sm font-medium transition-colors
              ${value === num 
                ? 'bg-black text-white border-black' 
                : 'bg-white text-black border-gray-300 hover:border-black'
              }`}
          >
            {num === 0 ? 'No (0)' : 'Yes (1)'}
          </button>
        ))}
      </div>
      <p className="text-xs text-gray-500">{description}</p>
    </div>
  );

  const EvaluationPanel = ({ 
    title,
    evalData, 
    setEvalData 
  }: { 
    title: string;
    evalData: ReplyEvaluation; 
    setEvalData: React.Dispatch<React.SetStateAction<ReplyEvaluation>>;
  }) => (
    <div className="mt-4 p-4 bg-gray-100 rounded-md space-y-4">
      <p className="text-sm font-semibold text-black">{title}</p>
      
      <StyleTransferScale
        value={evalData.style_transfer}
        onChange={(val) => setEvalData(prev => ({ ...prev, style_transfer: val }))}
      />
      
      <BinaryScale
        label="Content Preservation"
        description="0=Content/Meaning NOT preserved, 1=Content IS preserved"
        value={evalData.content_preservation}
        onChange={(val) => setEvalData(prev => ({ ...prev, content_preservation: val }))}
      />
      
      <BinaryScale
        label="Naturalness"
        description="0=Unnatural/incoherent, 1=Natural/coherent"
        value={evalData.naturalness}
        onChange={(val) => setEvalData(prev => ({ ...prev, naturalness: val }))}
      />
      
      {isEvaluationComplete(evalData) && (
        <p className="text-xs text-black-600 font-medium">Evaluation complete</p>
      )}
    </div>
  );

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

      {generatedReplies && (
        <div className="mt-6 space-y-6">
          <div className='text-lg font-extrabold'>Now you have to rate these two replies based on your general style of writing to this person.
            Does it match features like - Formality, Tone, Mail length, Vocabulary, Punctuation and Structure that you follow to talk to the person
          </div>
          {/* Reply 1 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-black">
                Reply 1
              </label>
            </div>
            <div className="p-4 border-2 border-black rounded-md bg-gray-50">
              <p className="text-sm text-black whitespace-pre-wrap">
                {generatedReplies.full_context_reply}
              </p>
            </div>
            <button
              onClick={() => copyToClipboard(generatedReplies.full_context_reply, 'Reply 1')}
              className="mt-2 text-sm text-black underline hover:no-underline"
            >
              Copy to clipboard
            </button>
            
            <EvaluationPanel 
              title="Evaluate Reply 1"
              evalData={reply1Eval} 
              setEvalData={setReply1Eval} 
            />
          </div>

          {/* Reply 2 */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-sm font-medium text-black">
                Reply 2
              </label>
            </div>
            <div className="p-4 border-2 border-gray-400 rounded-md bg-white">
              <p className="text-sm text-black whitespace-pre-wrap">
                {generatedReplies.thread_only_reply}
              </p>
            </div>
            <button
              onClick={() => copyToClipboard(generatedReplies.thread_only_reply, 'Reply 2')}
              className="mt-2 text-sm text-black underline hover:no-underline"
            >
              Copy to clipboard
            </button>
            
            <EvaluationPanel 
              title="Evaluate Reply 2"
              evalData={reply2Eval} 
              setEvalData={setReply2Eval} 
            />
          </div>

          {/* Save Results Button */}
          <button
            onClick={saveResults}
            disabled={!canSaveResults()}
            className={`w-full py-3 px-4 rounded-md font-medium transition-colors
              ${canSaveResults()
                ? 'bg-black text-white'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
          >
            {canSaveResults() 
              ? 'Save Evaluation Results (JSON)' 
              : 'Complete all evaluations to save'}
          </button>
        </div>
      )}
    </div>
  );
}