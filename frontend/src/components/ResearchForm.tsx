"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useResearchStore } from '@/stores/researchStore';
import { startResearch } from '@/lib/api';

export default function ResearchForm() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const setTaskId = useResearchStore((state) => state.setTaskId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const data = await startResearch({ query });
      setTaskId(data.task_id);
      router.push(`/research/${data.task_id}`);
    } catch (error) {
      console.error("Failed to start research", error);
      alert("Error starting research. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">Start New Research</h2>
      <textarea
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="What would you like to research today?"
        className="w-full p-4 border rounded-md mb-4 h-32 focus:ring-2 focus:ring-blue-500 outline-none"
        required
      />
      <button
        type="submit"
        disabled={loading}
        className="w-full bg-blue-600 text-white py-3 rounded-md font-semibold hover:bg-blue-700 transition disabled:opacity-50"
      >
        {loading ? "Initializing Agents..." : "Run Research Swarm"}
      </button>
    </form>
  );
}
