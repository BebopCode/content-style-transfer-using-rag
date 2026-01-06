'use client';

import { ThreadMessage } from './types';

interface ThreadViewProps {
  messages: ThreadMessage[];
  loading: boolean;
  myEmail: string;
}

export default function ThreadView({ messages, loading, myEmail }: ThreadViewProps) {
  if (loading) {
    return (
      <div className="mt-6 p-4 border-2 border-black rounded-md bg-white">
        <p className="text-sm text-black">Loading thread...</p>
      </div>
    );
  }

  if (messages.length === 0) {
    return null;
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="mt-6">
      <h2 className="text-lg font-semibold text-black mb-4">
        Thread: {messages[0]?.subject?.replace(/^Re:\s*/i, '') || '(No Subject)'}
      </h2>
      <p className="text-sm text-gray-600 mb-4">{messages.length} message{messages.length !== 1 ? 's' : ''}</p>
      
      <div className="space-y-4">
        {messages.map((message) => {
          const isMe = message.sender === myEmail;
          
          return (
            <div
              key={message.message_id}
              className={`p-4 border-2 rounded-md ${
                isMe 
                  ? 'border-black bg-gray-50 ml-4' 
                  : 'border-gray-400 bg-white mr-4'
              }`}
            >
              <div className="flex justify-between items-start mb-2">
                <div>
                  <p className="text-sm font-medium text-black">
                    {isMe ? 'You' : message.sender}
                  </p>
                  <p className="text-xs text-gray-500">
                    To: {isMe ? message.receiver : 'You'}
                  </p>
                </div>
                <p className="text-xs text-gray-500">
                  {message.sent_at ? formatDate(message.sent_at) : 'Unknown date'}
                </p>
              </div>
              
              <div className="border-t border-gray-200 pt-2 mt-2">
                <p className="text-sm text-black whitespace-pre-wrap">
                  {message.content || '(No content)'}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}