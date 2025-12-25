'use client';

import { useState, useEffect } from 'react';

interface Recipient {
  email: string;
  count: number;
}

interface Email {
  message_id: string;
  subject: string;
  sender: string;
  receiver: string;
  sent_at: string;
}

export default function EmailSearch() {
  const [myEmail, setMyEmail] = useState('');
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [selectedRecipient, setSelectedRecipient] = useState('');
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmailId, setSelectedEmailId] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingEmails, setLoadingEmails] = useState(false);

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!myEmail.trim()) {
      alert('Please enter your email address');
      return;
    }

    setLoading(true);
    setRecipients([]);
    setSelectedRecipient('');
    setEmails([]);
    setSelectedEmailId('');

    try {
      const response = await fetch(
        `http://localhost:8000/recipients/${encodeURIComponent(myEmail)}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch recipients');
      }

      const data = await response.json();
      setRecipients(data);

      if (data.length === 0) {
        alert('No recipients found for this email address');
      }
    } catch (error) {
      console.error('Error fetching recipients:', error);
      alert('Error fetching recipients. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const fetchEmails = async (recipient: string) => {
    setLoadingEmails(true);
    
    try {
      const response = await fetch(
        `http://localhost:8000/emails/conversation/${encodeURIComponent(myEmail)}/${encodeURIComponent(recipient)}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch emails');
      }

      const data = await response.json();
      
      // Filter out replies (subjects starting with "Re: ")
      const filteredEmails = data.filter((email: Email) => 
        email.subject && !email.subject.trim().startsWith('Re:')
      );
      
      setEmails(filteredEmails);

      if (filteredEmails.length === 0) {
        alert('No non-reply emails found in this conversation');
      }
    } catch (error) {
      console.error('Error fetching emails:', error);
      alert('Error fetching emails. Please try again.');
    } finally {
      setLoadingEmails(false);
    }
  };

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-md mx-auto">
        <h1 className="text-3xl font-bold text-black mb-8">Email Search</h1>

        {/* Email Input Form */}
        <form onSubmit={handleEmailSubmit} className="mb-8">
          <label htmlFor="my-email" className="block text-sm font-medium text-black mb-2">
            Your Email Address
          </label>
          <input
            id="my-email"
            type="email"
            value={myEmail}
            onChange={(e) => setMyEmail(e.target.value)}
            placeholder="your.email@example.com"
            className="w-full px-4 py-2 border-2 border-black rounded-md
              focus:outline-none focus:ring-2 focus:ring-black
              text-black placeholder-gray-400"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="w-full mt-4 bg-black text-white py-2 px-4 rounded-md
              hover:bg-gray-800 disabled:bg-gray-300 disabled:text-gray-500
              disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? 'Searching...' : 'Find Recipients'}
          </button>
        </form>

        {/* Recipients Dropdown */}
        {recipients.length > 0 && (
          <div>
            <label htmlFor="recipient-select" className="block text-sm font-medium text-black mb-2">
              Select Recipient ({recipients.length} found)
            </label>
            <select
              id="recipient-select"
              value={selectedRecipient}
              onChange={(e) => {
                setSelectedRecipient(e.target.value);
                setEmails([]);
                setSelectedEmailId('');
                if (e.target.value) {
                  fetchEmails(e.target.value);
                }
              }}
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

            {selectedRecipient && (
              <div className="mt-6 p-4 border-2 border-black rounded-md bg-white">
                <p className="text-sm text-black mb-4">
                  <span className="font-medium">Selected:</span> {selectedRecipient}
                </p>

                {loadingEmails ? (
                  <p className="text-sm text-black">Loading emails...</p>
                ) : emails.length > 0 ? (
                  <>
                    <label htmlFor="email-select" className="block text-sm font-medium text-black mb-2">
                      Select Email Thread ({emails.length} found)
                    </label>
                    <select
                      id="email-select"
                      value={selectedEmailId}
                      onChange={(e) => setSelectedEmailId(e.target.value)}
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
                  <p className="text-sm text-black">No non-reply emails found</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Empty State */}
        {!loading && recipients.length === 0 && myEmail && (
          <div className="text-center p-8 border-2 border-black rounded-md">
            <p className="text-black">No recipients found. Try a different email address.</p>
          </div>
        )}
      </div>
    </div>
  );
}