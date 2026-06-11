"use client";

import ReactMarkdown from "react-markdown";
import type { ResearchReport } from "@/types";

interface ResearchResultsProps {
  report: ResearchReport;
}

export default function ResearchResults({ report }: ResearchResultsProps) {
  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {report.title}
        </h1>
        <div className="flex gap-4 text-sm text-gray-500 mb-6">
          <span>{report.word_count.toLocaleString()} words</span>
          <span>
            {new Date(report.created_at).toLocaleDateString()}
          </span>
        </div>
        {report.executive_summary && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">
            <h2 className="font-semibold text-blue-900 mb-2">
              Executive Summary
            </h2>
            <p className="text-blue-800">{report.executive_summary}</p>
          </div>
        )}
      </div>

      <div className="bg-white rounded-lg shadow p-6 prose prose-blue max-w-none">
        <ReactMarkdown>{report.full_content}</ReactMarkdown>
      </div>

      {report.citations && report.citations.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6 mt-6">
          <h2 className="text-xl font-bold mb-4">Citations</h2>
          <ol className="list-decimal pl-5 space-y-2">
            {report.citations.map((citation: Record<string, unknown>, idx: number) => {
              const url = citation.url ? String(citation.url) : null;
              return (
                <li key={idx} className="text-sm text-gray-600">
                  {String(citation.title ?? "")}{" "}
                  {url && (
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline"
                    >
                      [Source]
                    </a>
                  )}
                </li>
              );
            })}
          </ol>
        </div>
      )}
    </div>
  );
}
