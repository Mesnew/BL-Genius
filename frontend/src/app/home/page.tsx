'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import dynamic from 'next/dynamic';
import { useAuth } from '@/contexts/AuthContext';

// Import dynamique pour éviter les problèmes SSR avec Three.js
const PlayerScene = dynamic(() => import('@/components/voxel/PlayerScene'), {
  ssr: false,
  loading: () => (
    <div className="flex flex-col items-center justify-center h-full">
      <div className="w-16 h-16 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mb-4" />
      <div className="text-white text-2xl font-bold animate-pulse">
        Chargement du stade 3D...
      </div>
      <div className="text-gray-400 mt-2">Préparation du terrain ⚽</div>
    </div>
  ),
});

export default function HomePage() {
  const { user, isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [selectedPlayer, setSelectedPlayer] = useState<string | null>(null);
  const [showInstructions, setShowInstructions] = useState(true);

  // Redirection si non authentifié
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth');
    }
  }, [isLoading, isAuthenticated, router]);

  // Cacher les instructions après 5 secondes
  useEffect(() => {
    const timer = setTimeout(() => {
      setShowInstructions(false);
    }, 5000);
    return () => clearTimeout(timer);
  }, []);

  const handleSelectPlayer = (player: 'messi' | 'ronaldo') => {
    setSelectedPlayer(player);

    // Animation de transition avant redirection
    setTimeout(() => {
      if (player === 'messi') {
        router.push('/analyze');
      } else {
        router.push('/preview');
      }
    }, 1500);
  };

  // Affichage du loading pendant la vérification auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-900 via-blue-700 to-green-600 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <div className="text-white text-2xl font-bold animate-pulse">
            Chargement...
          </div>
        </div>
      </div>
    );
  }

  // Si pas authentifié, ne rien afficher (redirection en cours)
  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="relative w-full h-screen overflow-hidden">
      {/* Scène 3D */}
      <PlayerScene onSelectPlayer={handleSelectPlayer} selectedPlayer={selectedPlayer} />

      {/* UI Overlay */}
      <div className="absolute top-0 left-0 w-full h-full pointer-events-none">
        {/* Header avec titre */}
        <div className="absolute top-6 left-1/2 transform -translate-x-1/2 pointer-events-auto">
          <div className="bg-black/40 backdrop-blur-lg rounded-full px-8 py-4 border border-white/20">
            <h1 className="text-3xl font-black text-white drop-shadow-lg tracking-wider">
              ⚽ CHOISISSEZ VOTRE MODE
            </h1>
          </div>
        </div>

        {/* Info utilisateur */}
        {user && (
          <div className="absolute top-6 right-6 pointer-events-auto">
            <div className="bg-white/10 backdrop-blur-md rounded-full px-6 py-3 text-white font-medium border border-white/20 flex items-center gap-3">
              <span className="text-2xl">👤</span>
              <div>
                <div className="text-sm opacity-80">Bienvenue</div>
                <div className="font-bold">{user.username}</div>
              </div>
            </div>
          </div>
        )}

        {/* Instructions avec animation */}
        {showInstructions && !selectedPlayer && (
          <div
            className={`absolute bottom-8 left-1/2 transform -translate-x-1/2 pointer-events-auto transition-all duration-1000 ${
              showInstructions ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'
            }`}
          >
            <div className="bg-black/50 backdrop-blur-lg rounded-2xl px-8 py-5 text-white text-center border border-white/20">
              <p className="text-lg font-semibold mb-3">
                🖱️ Cliquez sur un joueur pour choisir votre mode
              </p>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="bg-blue-500/20 rounded-lg p-3 border border-blue-400/30">
                  <div className="text-2xl mb-1">🔵🔴</div>
                  <div className="font-bold">Messi</div>
                  <div className="text-blue-200">Analyse IA</div>
                </div>
                <div className="bg-yellow-500/20 rounded-lg p-3 border border-yellow-400/30">
                  <div className="text-2xl mb-1">⚪⚫</div>
                  <div className="font-bold">Ronaldo</div>
                  <div className="text-yellow-200">Prévisualisation</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Overlay de transition */}
        {selectedPlayer && (
          <div className="absolute inset-0 bg-black/70 flex items-center justify-center animate-fade-in backdrop-blur-sm">
            <div className="text-center transform scale-110">
              <div className="text-8xl mb-6 animate-bounce">
                {selectedPlayer === 'messi' ? '🔵🔴' : '⚪⚫'}
              </div>
              <h2 className="text-5xl font-black text-white mb-4 drop-shadow-lg">
                {selectedPlayer === 'messi' ? 'Lionel Messi' : 'Cristiano Ronaldo'}
              </h2>
              <p className="text-white/80 text-xl mb-6">
                {selectedPlayer === 'messi'
                  ? "Préparation de l'analyse IA..."
                  : 'Ouverture du lecteur vidéo...'}
              </p>
              <div className="w-64 h-2 bg-white/30 rounded-full overflow-hidden mx-auto">
                <div className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 animate-progress" />
              </div>
            </div>
          </div>
        )}

        {/* Footer avec crédits */}
        <div className="absolute bottom-4 left-6 pointer-events-auto">
          <div className="text-white/50 text-sm">
            BL Genius © 2024 - Analyse Football IA
          </div>
        </div>
      </div>

      {/* Styles pour les animations */}
      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; backdrop-filter: blur(0px); }
          to { opacity: 1; backdrop-filter: blur(8px); }
        }
        .animate-fade-in {
          animation: fade-in 0.5s ease-out forwards;
        }
        @keyframes progress {
          from { width: 0%; }
          to { width: 100%; }
        }
        .animate-progress {
          animation: progress 1.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
}
