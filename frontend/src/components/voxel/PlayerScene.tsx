'use client';

import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import VoxelPlayer from './VoxelPlayer';
import VoxelEnvironment from './VoxelEnvironment';
import * as THREE from 'three';

interface PlayerSceneProps {
  onSelectPlayer: (player: 'messi' | 'ronaldo') => void;
  selectedPlayer?: string | null;
}

function Scene({ onSelectPlayer, selectedPlayer }: PlayerSceneProps) {
  const isMessiSelected = selectedPlayer === 'messi';
  const isRonaldoSelected = selectedPlayer === 'ronaldo';

  return (
    <>
      {/* Lumières */}
      <ambientLight intensity={0.6} />
      <directionalLight
        position={[10, 20, 10]}
        intensity={1}
        castShadow
        shadow-mapSize={[2048, 2048]}
      />
      <directionalLight
        position={[-10, 10, -10]}
        intensity={0.3}
      />

      {/* Environnement */}
      <VoxelEnvironment />

      {/* Étoiles */}
      <Stars
        radius={100}
        depth={50}
        count={1000}
        factor={4}
        saturation={0}
        fade
      />

      {/* Joueur 1: Messi - Design Barcelone 1899/2024 (Half-Half) */}
      <VoxelPlayer
        name="Messi"
        position={[-4, 0, 0]}
        jerseyColors={{
          primary: '#004D98',      // Bleu profond Barcelone
          secondary: '#A50044',  // Rouge noble/grenat
          shorts: '#004D98',     // Short bleu
          socks: '#004D98',      // Chaussettes bleues
          accent: '#FFD700'      // Or pour accents 125ème anniversaire
        }}
        onClick={() => onSelectPlayer('messi')}
        isSelected={isMessiSelected}
      />

      {/* Joueur 2: Ronaldo - Design Real Madrid 2011-12 (White & Gold) */}
      <VoxelPlayer
        name="Ronaldo"
        position={[4, 0, 0]}
        jerseyColors={{
          primary: '#FFFFFF',    // Blanc pur
          secondary: '#FFD700',  // Or
          shorts: '#000000',     // Short noir
          socks: '#FFFFFF',      // Chaussettes blanches
          accent: '#000000'      // Noir pour les bandes
        }}
        onClick={() => onSelectPlayer('ronaldo')}
        isSelected={isRonaldoSelected}
      />

      {/* Contrôles caméra */}
      <OrbitControls
        enablePan={false}
        enableZoom={true}
        minDistance={5}
        maxDistance={20}
        minPolarAngle={Math.PI / 6}
        maxPolarAngle={Math.PI / 2.5}
        target={[0, 1, 0]}
      />
    </>
  );
}

// Fallback pendant le chargement
function LoadingFallback() {
  return (
    <div className="flex items-center justify-center h-full text-white text-2xl font-bold">
      <div className="animate-pulse">Chargement de la scène 3D...</div>
    </div>
  );
}

export default function PlayerScene({ onSelectPlayer, selectedPlayer }: PlayerSceneProps) {
  return (
    <div className="w-full h-full">
      <Suspense fallback={<LoadingFallback />}>
        <Canvas
          shadows
          camera={{ position: [0, 5, 12], fov: 50 }}
          gl={{ antialias: true, alpha: true }}
        >
          <color attach="background" args={['#87CEEB']} />
          <fog attach="fog" args={['#87CEEB', 30, 80]} />
          <Scene onSelectPlayer={onSelectPlayer} selectedPlayer={selectedPlayer} />
        </Canvas>
      </Suspense>
    </div>
  );
}
