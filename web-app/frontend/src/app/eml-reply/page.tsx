'use client';

import { useState } from 'react';
import { 
  EmailForm, 
  RecipientSelect, 
  ThreadSelect, 
  ThreadView,
  GenerateReply,
  EmptyState,
  Recipient,
  Email,
  ThreadMessage
} from './components';

export default function EmailSearch() {
  const [myEmail, setMyEmail] = useState('');
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [selectedRecipient, setSelectedRecipient] = useState('');
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmailId, setSelectedEmailId] = useState('');
  const [threadMessages, setThreadMessages] = useState<ThreadMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingEmails, setLoadingEmails] = useState(false);
  const [loadingThread, setLoadingThread] = useState(false);

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
    setThreadMessages([]);

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/recipients/${encodeURIComponent(myEmail)}`
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
        `${process.env.NEXT_PUBLIC_API_URL}/emails/conversation/${encodeURIComponent(myEmail)}/${encodeURIComponent(recipient)}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch emails');
      }

      const data = await response.json();
      
      const getBaseSubject = (subject: string) => {
        return subject?.trim().replace(/^Re:\s*/i, '') || '';
      };

      const seenSubjects = new Set<string>();
      const uniqueThreads = data.filter((email: Email) => {
        const baseSubject = getBaseSubject(email.subject);
        if (seenSubjects.has(baseSubject)) {
          return false;
        }
        seenSubjects.add(baseSubject);
        return true;
      });
      
      setEmails(uniqueThreads);

      if (uniqueThreads.length === 0) {
        alert('No emails found in this conversation');
      }
    } catch (error) {
      console.error('Error fetching emails:', error);
      alert('Error fetching emails. Please try again.');
    } finally {
      setLoadingEmails(false);
    }
  };

  const fetchThread = async (subject: string) => {
    setLoadingThread(true);
    
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/emails/thread/${encodeURIComponent(subject)}`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch thread');
      }

      const data = await response.json();
      setThreadMessages(data);

      if (data.length === 0) {
        alert('No messages found in this thread');
      }
    } catch (error) {
      console.error('Error fetching thread:', error);
      alert('Error fetching thread. Please try again.');
    } finally {
      setLoadingThread(false);
    }
  };

  const handleRecipientSelect = (recipient: string) => {
    setSelectedRecipient(recipient);
    setEmails([]);
    setSelectedEmailId('');
    setThreadMessages([]);
    if (recipient) {
      fetchEmails(recipient);
    }
  };

  const handleThreadSelect = (emailId: string) => {
    setSelectedEmailId(emailId);
    setThreadMessages([]);
    
    if (emailId) {
      const selectedEmail = emails.find(e => e.message_id === emailId);
      if (selectedEmail) {
        fetchThread(selectedEmail.subject);
      }
    }
  };

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-black mb-8">Email Search</h1>

        <EmailForm
          myEmail={myEmail}
          setMyEmail={setMyEmail}
          onSubmit={handleEmailSubmit}
          loading={loading}
        />

        {recipients.length > 0 && (
          <>
            <RecipientSelect
              recipients={recipients}
              selectedRecipient={selectedRecipient}
              onSelect={handleRecipientSelect}
            />

            {selectedRecipient && (
              <ThreadSelect
                emails={emails}
                selectedEmailId={selectedEmailId}
                onSelect={handleThreadSelect}
                loading={loadingEmails}
                selectedRecipient={selectedRecipient}
              />
            )}

            {selectedEmailId && (
              <>
                <ThreadView
                  messages={threadMessages}
                  loading={loadingThread}
                  myEmail={myEmail}
                />

                {threadMessages.length > 0 && (
                  <GenerateReply
                    threadMessages={threadMessages}
                    myEmail={myEmail}
                    selectedRecipient={selectedRecipient}
                  />
                )}
              </>
            )}
          </>
        )}

        {!loading && recipients.length === 0 && myEmail && <EmptyState />}
      </div>
    </div>
  );
}