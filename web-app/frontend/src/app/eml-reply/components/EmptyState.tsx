'use client';

export default function EmptyState() {
  return (
    <div className="text-center p-8 border-2 border-black rounded-md">
      <p className="text-black">No recipients found. Try a different email address.</p>
    </div>
  );
}