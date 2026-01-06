'use client';

interface EmailFormProps {
  myEmail: string;
  setMyEmail: (email: string) => void;
  onSubmit: (e: React.FormEvent) => void;
  loading: boolean;
}

export default function EmailForm({ myEmail, setMyEmail, onSubmit, loading }: EmailFormProps) {
  return (
    <form onSubmit={onSubmit} className="mb-8">
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
  );
}