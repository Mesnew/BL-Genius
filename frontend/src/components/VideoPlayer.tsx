'use client';

import { useState } from 'react';
import { getVideoDownloadUrl } from '@/lib/api';

interface VideoPlayerProps {
  taskId: string;
  originalUrl?: string;
}

export default function VideoPlayer({ taskId, originalUrl }: VideoPlayerProps) {
  const [isLoading, setIsLoading] = useState(true);
  const analyzedUrl = getVideoDownloadUrl(taskId);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-8">
      {/* Vidéo originale */}
      {originalUrl && (
        <div className="bg-white/5 rounded-xl p-6 border border-white/10">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-bold text-gray-300">📹 Vidéo Originale</h3>
            <span className="text-xs bg-gray-700 px-2 py-1 rounded">Input</span>
          </div>
          <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
            <video
              src={originalUrl}
              controls
              className="w-full h-full"
              onLoadedData={() => setIsLoading(false)}
            />
          </div>
        </div>
      )}

      {/* Vidéo analysée */}
      <div className="bg-white/5 rounded-xl p-6 border border-white/10">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-green-400">✨ Vidéo Analysée</h3>
          <span className="text-xs bg-green-400/20 text-green-400 px-2 py-1 rounded">Output</span>
        </div>

        <div className="relative aspect-video bg-black rounded-lg overflow-hidden">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
            </div>
          )}
          <video
            src={analyzedUrl}
            controls
            className="w-full h-full"
            onLoadedData={() => setIsLoading(false)}
          />
        </div>

        <a
          href={analyzedUrl}
          download={`bl-genius-analysis-${taskId}.mp4`}
          className="
            inline-flex items-center gap-2 mt-4
            bg-gradient-to-r from-green-400 to-cyan-400
            text-gray-900 font-bold py-2 px-6 rounded-full
            hover:scale-105 transition-transform
          "
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Télécharger
        </a>
      </div>
    </div>
  );
}
