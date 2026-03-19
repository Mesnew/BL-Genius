'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import UploadVideo from '@/components/UploadVideo';
import VideoPlayer from '@/components/VideoPlayer';
import { useAuth } from '@/contexts/AuthContext';
import PageTransition from '@/components/PageTransition';

interface AnalyzedVideo {
  id: string;
  taskId: string;
  name: string;
  timestamp: Date;
}

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, isLoading, user, logout } = useAuth();
  const [analyzedVideos, setAnalyzedVideos] = useState<AnalyzedVideo[]>([]);
  const [selectedVideoId, setSelectedVideoId] = useState<string | null>(null);
  const [originalVideoUrl, setOriginalVideoUrl] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  // Rediriger vers la page de login si non authentifié
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  const handleUploadComplete = (taskId: string) => {
    console.log('Upload terminé:', taskId);
  };

  const handleVideoAnalyzed = (taskId: string, fileName?: string) => {
    console.log('Analyse terminée:', taskId);

    // Ajouter la nouvelle vidéo à la liste
    const newVideo: AnalyzedVideo = {
      id: Date.now().toString(),
      taskId: taskId,
      name: fileName || `Analyse ${analyzedVideos.length + 1}`,
      timestamp: new Date(),
    };

    setAnalyzedVideos(prev => [newVideo, ...prev]);
    setSelectedVideoId(newVideo.id);
  };

  const selectedVideo = analyzedVideos.find(v => v.id === selectedVideoId);

  // Afficher un loader pendant la vérification de l'authentification
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-400">Chargement...</p>
        </div>
      </div>
    );
  }

  // Ne rien afficher si non authentifié (redirection en cours)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <PageTransition>
      <div className={`min-h-screen relative transition-opacity duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
      {/* Header */}
      <header className="py-8 px-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-4xl">⚽</span>
            <h1 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-cyan-400 bg-clip-text text-transparent">
              BL Genius
            </h1>
          </div>
          <div className="flex items-center gap-6">
            <nav className="flex gap-6 text-sm text-gray-400">
              <a href="#" className="hover:text-white transition-colors">Accueil</a>
              <a href="#" className="hover:text-white transition-colors">Documentation</a>
              <a href="#" className="hover:text-white transition-colors">GitHub</a>
            </nav>
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

      {/* Hero Section */}
      <main className="px-4 pb-16">
        <div className="max-w-6xl mx-auto">
          {/* Titre */}
          <div className="text-center mb-12">
            <h2 className="text-5xl md:text-6xl font-bold text-white mb-6">
              Analysez vos matchs avec{' '}
              <span className="bg-gradient-to-r from-green-400 to-cyan-400 bg-clip-text text-transparent">
                l'IA
              </span>
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Détection automatique des joueurs, tracking du ballon et statistiques avancées
              en quelques clics.
            </p>
          </div>

          {/* Upload Component */}
          <UploadVideo
            onUploadComplete={handleUploadComplete}
            onVideoAnalyzed={handleVideoAnalyzed}
          />

          {/* Liste des vidéos analysées */}
          {analyzedVideos.length > 0 && (
            <div className="mt-8">
              <h3 className="text-xl font-bold text-white mb-4">📹 Vidéos analysées ({analyzedVideos.length})</h3>
              <div className="flex flex-wrap gap-3">
                {analyzedVideos.map((video) => (
                  <button
                    key={video.id}
                    onClick={() => setSelectedVideoId(video.id)}
                    className={`px-4 py-2 rounded-lg font-medium transition-all ${
                      selectedVideoId === video.id
                        ? 'bg-gradient-to-r from-green-400 to-cyan-400 text-gray-900'
                        : 'bg-white/10 text-white hover:bg-white/20'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <span>🎬</span>
                      <span>{video.name}</span>
                      <span className="text-xs opacity-70">
                        {video.timestamp.toLocaleTimeString()}
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Video Player */}
          {selectedVideo && (
            <div className="mt-8">
              <VideoPlayer
                taskId={selectedVideo.taskId}
                originalUrl={originalVideoUrl || undefined}
              />
            </div>
          )}

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mt-16">
            <FeatureCard
              icon="🏃"
              title="Tracking Joueurs"
              description="Détection et suivi automatique des joueurs, arbitres et ballon avec YOLO."
            />
            <FeatureCard
              icon="🎨"
              title="Assignation Équipes"
              description="Identification automatique des équipes par couleur de maillot."
            />
            <FeatureCard
              icon="📊"
              title="Statistiques"
              description="Possession, distance parcourue et vitesse des joueurs."
            />
            <FeatureCard
              icon="⚡"
              title="Rapide"
              description="Analyse optimisée avec GPU pour des résultats en temps record."
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/10 py-8 px-4 relative z-10">
        <div className="max-w-6xl mx-auto text-center text-gray-400 text-sm">
          <p><span className="text-green-400">© 2024 BL Genius</span>. Propulsé par YOLO, Next.js et FastAPI.</p>
        </div>
      </footer>
    </div>
      </PageTransition>
  );
}

interface FeatureCardProps {
  icon: string;
  title: string;
  description: string;
}

function FeatureCard({ icon, title, description }: FeatureCardProps) {
  return (
    <div className="bg-black/20 backdrop-blur-sm rounded-xl p-6 border border-white/10 hover:border-green-400/50 transition-all hover:bg-black/30">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-lg font-bold text-white mb-2">{title}</h3>
      <p className="text-gray-300 text-sm">{description}</p>
    </div>
  );
}
