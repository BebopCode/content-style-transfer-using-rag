'use client';

import { Recipient } from './types';

interface RecipientSelectProps {
  recipients: Recipient[];
  selectedRecipient: string;
  onSelect: (recipient: string) => void;
}

export default function RecipientSelect({ 
  recipients, 
  selectedRecipient, 
  onSelect 
}: RecipientSelectProps) {
  return (
    <div>
      <label htmlFor="recipient-select" className="block text-sm font-medium text-black mb-2">
        Select Recipient ({recipients.length} found)
      </label>
      <select
        id="recipient-select"
        value={selectedRecipient}
        onChange={(e) => onSelect(e.target.value)}
        className="w-full px-4 py-2 border-2 border-black rounded-md
          focus:outline-none focus:ring-2 focus:ring-black
          text-black bg-white"
      >
        <option value="">-- Select a recipient --</option>
        {recipients.map((recipient, idx) => (
          <option key={idx} value={recipient.email}>
            {recipient.email} ({recipient.count} email{recipient.count !== 1 ? 's' : ''})
          </option>
        ))}
      </select>
    </div>
  );
}