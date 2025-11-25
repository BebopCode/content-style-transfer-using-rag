// components/PasswordForm.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const PasswordForm: React.FC = () => {
  const [password, setPassword] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/check-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });

      const data: { success: boolean; message: string } = await response.json();

      if (data.success) {
        // Successful login - redirect to the main page
        router.push('/add-email'); 
      } else {
        setError(data.message || 'Login failed.');
      }
    } catch (err) {
      setError('An error occurred during login.');
    } finally {
      setLoading(false);
    }
  };

  // Monochrome Tailwind styling
  const buttonClasses = loading 
    ? "w-full py-2 border border-black bg-gray-200 text-black font-semibold cursor-not-allowed"
    : "w-full py-2 border border-black bg-black text-white font-semibold hover:bg-gray-800 transition duration-150";

  return (
    <form onSubmit={handleSubmit} className="w-80 p-6 border border-black shadow-lg">
      <h2 className="text-2xl font-bold mb-6 text-center">Access Required</h2>
      
      {error && (
        <p className="mb-4 p-2 bg-red-100 text-red-700 border border-red-700 text-sm text-center">
          {error}
        </p>
      )}

      <div className="mb-4">
        <label htmlFor="password" className="block text-sm font-medium mb-1">
          Password
        </label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          disabled={loading}
          className="w-full px-3 py-2 border border-black bg-white focus:outline-none focus:ring-1 focus:ring-black"
        />
      </div>

      <button type="submit" disabled={loading} className={buttonClasses}>
        {loading ? 'Checking...' : 'Enter'}
      </button>
    </form>
  );
};

export default PasswordForm;