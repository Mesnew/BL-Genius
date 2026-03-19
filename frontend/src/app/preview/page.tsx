'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import PageTransition from '@/components/PageTransition';

interface VideoFile {
  id: string;
  file: File;
  url: string;
  name: string;
  size: number;
  duration?: number;
}

export default function PreviewPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [videos, setVideos] = useState<VideoFile[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    handleFiles(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files) {
      handleFiles(files);
    }
  };

  const handleFiles = (files: FileList) => {
    const validFormats = ['.mp4', '.avi', '.mov', '.mkv', '.webm'];

    Array.from(files).forEach((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (validFormats.includes(ext)) {
        const videoUrl = URL.createObjectURL(file);
        const newVideo: VideoFile = {
          id: Date.now().toString() + Math.random().toString(36).substr(2, 9),
          file,
          url: videoUrl,
          name: file.name,
          size: file.size,
        };
        setVideos((prev) => [...prev, newVideo]);
        if (!selectedVideoId) {
          setSelectedVideoId(newVideo.id);
        }
      }
    });
  };

  const removeVideo = (id: string) => {
    setVideos((prev) => {
      const video = prev.find((v) => v.id === id);
      if (video) {
        URL.revokeObjectURL(video.url);
      }
      const newVideos = prev.filter((v) => v.id !== id);
      if (selectedVideoId === id) {
        setSelectedVideoId(newVideos.length > 0 ? newVideos[0].id : null);
      }
      return newVideos;
    });
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const selectedVideo = videos.find((v) => v.id === selectedVideoId);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-red-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Chargement...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <PageTransition>
      <div className={`min-h-screen relative transition-opacity duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
        {/* Header */}
        <header className="py-6 px-4 relative z-10">
          <div className="max-w-6xl mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/home')}
                className="text-4xl hover:scale-110 transition-transform"
              >
                ⚽
              </button>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-yellow-400 to-red-500 bg-clip-text text-transparent">
                  Prévisualisation - Ronaldo
                </h1>
                <p className="text-sm text-gray-400">Visionnez vos matchs sans analyse IA</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <button
                onClick={() => router.push('/analyze')}
                className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
              >
                ← Mode Analyse IA
              </button>
              {user && (
                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-400">👤 {user.username}</span>
                  <button
                    onClick={logout}
                    className="text-sm text-red-400 hover:text-red-300 transition-colors"
                  >
                    Déconnexion
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="px-4 pb-16 relative z-10">
          <div className="max-w-6xl mx-auto">
            {/* Titre */}
            <div className="text-center mb-8">
              <h2 className="text-4xl font-bold text-white mb-4">
                <span className="text-yellow-400">Ronaldo</span> - Prévisualisation
              </h2>
              <p className="text-gray-300 max-w-2xl mx-auto">
                Uploadez vos vidéos de match pour les visionner directement dans le navigateur.
                Aucune analyse IA, juste une lecture simple et rapide.
              </p>
            </div>

            {/* Zone d'upload */}
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`
                relative border-2 border-dashed rounded-2xl p-12 text-center
                transition-all duration-300 cursor-pointer backdrop-blur-sm mb-8
                ${isDragging
                  ? 'border-yellow-400 bg-yellow-400/20 shadow-lg shadow-yellow-400/20'
                  : 'border-white/30 bg-black/20 hover:border-yellow-400/70 hover:bg-black/30'
                }
              `}
            >
              <input
                type="file"
                accept=".mp4,.avi,.mov,.mkv,.webm"
                onChange={handleFileInput}
                className="hidden"
                id="file-input"
                multiple
                ref={fileInputRef}
              />

              <label htmlFor="file-input" className="cursor-pointer block">
                <div className="text-6xl mb-4 animate-bounce">📹</div>
                <h3 className="text-2xl font-bold mb-2 text-white">
                  {isDragging ? 'Déposez les vidéos ici' : 'Glissez vos vidéos ici'}
                </h3>
                <p className="text-gray-300 mb-4">ou</p>

                <button className="
                  bg-gradient-to-r from-yellow-400 to-red-500
                  text-gray-900 font-bold py-3 px-8 rounded-full
                  hover:scale-105 transition-transform shadow-lg
                "
                >
                  Sélectionner des fichiers
                </button>

                <p className="mt-4 text-sm text-gray-400">
                  Formats supportés: MP4, AVI, MOV, MKV, WebM
                </p>
              </label>
            </div>

            {/* Liste des vidéos */}
            {videos.length > 0 && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Sidebar - Liste des vidéos */}
                <div className="lg:col-span-1 space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-xl font-bold text-white">🎬 Vidéos ({videos.length})</h3>
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      className="text-sm px-3 py-1 bg-white/10 hover:bg-white/20 rounded-lg transition-colors"
                    >
                      + Ajouter
                    </button>
                  </div>

                  <div className="space-y-3 max-h-[600px] overflow-y-auto">
                    {videos.map((video) => (
                      <div
                        key={video.id}
                        onClick={() => setSelectedVideoId(video.id)}
                        className={`p-4 rounded-lg cursor-pointer transition-all border ${
                          selectedVideoId === video.id
                            ? 'bg-yellow-400/20 border-yellow-400'
                            : 'bg-black/20 border-white/10 hover:border-white/30'
                        }`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-white truncate">{video.name}</p>
                            <p className="text-sm text-gray-400">{formatFileSize(video.size)}</p>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              removeVideo(video.id);
                            }}
                            className="ml-2 text-red-400 hover:text-red-300 p-1"
                          >
                            ✕
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Main - Lecteur vidéo */}
                <div className="lg:col-span-2">
                  {selectedVideo ? (
                    <div className="bg-black/40 backdrop-blur-sm rounded-2xl overflow-hidden border border-white/20"
                    >
                      <div className="aspect-video bg-black relative"
                      >
                        <video
                          key={selectedVideo.id}
                          src={selectedVideo.url}
                          controls
                          className="w-full h-full object-contain"
                          autoPlay
                          playsInline
                        >
                          Votre navigateur ne supporte pas la lecture vidéo.
                        </video>
                      </div>

                      <div className="p-6"
                      >
                        <h3 className="text-xl font-bold text-white mb-2">{selectedVideo.name}</h3>
                        <div className="flex items-center gap-4 text-sm text-gray-400">
                          <span>📁 {formatFileSize(selectedVideo.size)}</span>
                          <span>🎬 {selectedVideo.file.type || 'Vidéo'}</span>
                        </div>

                        <div className="mt-4 flex gap-3">
                          <a
                            href={selectedVideo.url}
                            download={selectedVideo.name}
                            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm transition-colors"
                          >
                            ⬇️ Télécharger
                          </a>

                          <button
                            onClick={() => router.push('/analyze')}
                            className="px-4 py-2 bg-gradient-to-r from-green-400 to-cyan-400 text-gray-900 font-bold rounded-lg text-sm hover:scale-105 transition-transform"
                          >
                            🔬 Analyser cette vidéo
                          </button>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="bg-black/20 backdrop-blur-sm rounded-2xl p-12 text-center border border-white/10"
                    >
                      <div className="text-6xl mb-4">🎬</div>
                      <p className="text-gray-400">Sélectionnez une vidéo pour la prévisualiser</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Message si aucune vidéo */}
            {videos.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4 opacity-50">📂</div>
                <p className="text-gray-400 text-lg">Aucune vidéo chargée</p>
                <p className="text-gray-500 text-sm mt-2">Uploadez une vidéo pour commencer</p>
              </div>
            )}
          </div>
        </main>
      </div>
    </PageTransition>
  );
}
