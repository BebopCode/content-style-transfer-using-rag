// app/add-email/page.tsx
'use client';

import { useState, ChangeEvent, FormEvent } from 'react';
// Assuming you created the interface in types/email.ts
import { EmailTemplate } from '@/types/email'; 
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL;
const AddEmailPage: React.FC = () => {
  const [formData, setFormData] = useState<EmailTemplate>({
    sender: '',
    receiver: '',
    content: '',
    subject: '',
    date: '',
  });

  const handleChange = (e: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();

  try {
    const isoDate = new Date(formData.date).toISOString();

    const payload = {
      sender: formData.sender,
      receiver: formData.receiver,
      content: formData.content,
      subject: formData.subject,
      sent_at: isoDate,
    };

    const response = await fetch(`${API_BASE_URL}/api/add-email`,{
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (response.ok) {
      alert('Email template submitted successfully!');
      setFormData({ sender: '', receiver: '', content: '', subject: '', date: '' });
    } else {
      alert(`Submission failed: ${data.message || 'Server error'}`);
    }
  } catch (error) {
    alert('Network error: Could not connect to backend');
    console.error(error);
  }
};

  // --- Monochrome Tailwind CSS Classes ---
  const inputClasses = "w-full px-3 py-2 border border-black bg-white focus:outline-none focus:ring-1 focus:ring-black";
  const labelClasses = "block text-sm font-medium mb-1 mt-4";
  const buttonClasses = "w-full py-2 mt-6 border border-black bg-black text-white font-semibold hover:bg-gray-800 transition duration-150";

  return (
    <div className="max-w-lg mx-auto p-6 border border-black shadow-lg">
      <h1 className="text-2xl font-bold mb-6 text-center">Add New Email Template</h1>
      
      <form onSubmit={handleSubmit}>
        
        {/* Sender Field */}
        <div>
          <label htmlFor="sender" className={labelClasses}>
            Sender
          </label>
          <input
            id="sender"
            name="sender"
            type="text"
            value={formData.sender}
            onChange={handleChange}
            required
            className={inputClasses}
          />
        </div>

        {/* Receiver Field */}
        <div>
          <label htmlFor="receiver" className={labelClasses}>
            Receiver
          </label>
          <input
            id="receiver"
            name="receiver"
            type="text"
            value={formData.receiver}
            onChange={handleChange}
            required
            className={inputClasses}
          />
        </div>

                {/* Subject Field */}
        <div>
          <label htmlFor="subject" className={labelClasses}>
            Subject
          </label>
          <input
            id="subject"
            name="subject"
            type="text"
            value={formData.subject}
            onChange={handleChange}
            required
            className={inputClasses}
          />
        </div>

        {/* Email Content Field */}
        <div>
          <label htmlFor="content" className={labelClasses}>
            Email Content
          </label>
          <textarea
            id="content"
            name="content"
            rows={6}
            value={formData.content}
            onChange={handleChange}
            required
            className={`${inputClasses} resize-none`}
          />
        </div>

        <div>
          <label htmlFor="date" className={labelClasses}>
            Date
          </label>
          <input
            id="date"
            name="date"
            type="date"
            value={formData.date}
            onChange={handleChange}
            required
            className={inputClasses}
          />
        </div>

        {/* Add Email Button */}
        <button type="submit" className={buttonClasses}>
          Add Email
        </button>
      </form>
    </div>
  );
}

export default AddEmailPage;