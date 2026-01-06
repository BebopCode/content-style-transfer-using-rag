'use client';

import { Email } from './types';

interface ThreadSelectProps {
  emails: Email[];
  selectedEmailId: string;
  onSelect: (emailId: string) => void;
  loading: boolean;
  selectedRecipient: string;
}

export default function ThreadSelect({ 
  emails, 
  selectedEmailId, 
  onSelect, 
  loading,
  selectedRecipient 
}: ThreadSelectProps) {
  return (
    <div className="mt-6 p-4 border-2 border-black rounded-md bg-white">
      <p className="text-sm text-black mb-4">
        <span className="font-medium">Selected:</span> {selectedRecipient}
      </p>

      {loading ? (
        <p className="text-sm text-black">Loading emails...</p>
      ) : emails.length > 0 ? (
        <>
          <label htmlFor="email-select" className="block text-sm font-medium text-black mb-2">
            Select Email Thread ({emails.length} found)
          </label>
          <select
            id="email-select"
            value={selectedEmailId}
            onChange={(e) => onSelect(e.target.value)}
            className="w-full px-4 py-2 border-2 border-black rounded-md
              focus:outline-none focus:ring-2 focus:ring-black
              text-black bg-white"
          >
            <option value="">-- Select Thread --</option>
            {emails.map((email) => (
              <option key={email.message_id} value={email.message_id}>
                {email.subject || '(No Subject)'}
              </option>
            ))}
          </select>
        </>
      ) : (
        <p className="text-sm text-black">No emails found</p>
      )}
    </div>
  );
}