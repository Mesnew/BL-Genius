'use client';

import { useRef, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';

interface VoxelPlayerProps {
  name: string;
  position: [number, number, number];
  jerseyColors: {
    primary: string;
    secondary: string;
    shorts: string;
    socks: string;
    accent?: string;
  };
  onClick: () => void;
  isSelected?: boolean;
}

export default function VoxelPlayer({
  name,
  position,
  jerseyColors,
  onClick,
  isSelected = false
}: VoxelPlayerProps) {
  const groupRef = useRef<THREE.Group>(null);
  const [hovered, setHovered] = useState(false);

  // Déterminer si c'est Messi ou Ronaldo pour le design spécifique
  const isMessi = name === 'Messi';
  const isRonaldo = name === 'Ronaldo';

  // Animation
  useFrame((state) => {
    if (groupRef.current) {
      const time = state.clock.elapsedTime;
      // Animation de respiration
      groupRef.current.position.y = position[1] + Math.sin(time * 2) * 0.03;

      // Rotation vers le centre (face au ballon)
      if (isMessi) {
        groupRef.current.rotation.y = Math.PI / 2 + Math.sin(time * 0.5) * 0.05;
      } else {
        groupRef.current.rotation.y = -Math.PI / 2 + Math.sin(time * 0.5) * 0.05;
      }
    }
  });

  return (
    <group
      ref={groupRef}
      position={position}
      onClick={onClick}
      onPointerOver={() => {
        setHovered(true);
        document.body.style.cursor = 'pointer';
      }}
      onPointerOut={() => {
        setHovered(false);
        document.body.style.cursor = 'default';
      }}
    >
      {/* Label flottant */}
      <Html position={[0, 2.5, 0]} center distanceFactor={8}>
        <div
          style={{
            background: hovered || isSelected
              ? `linear-gradient(135deg, ${jerseyColors.primary}, ${jerseyColors.secondary})`
              : 'rgba(0,0,0,0.8)',
            color: 'white',
            padding: '8px 16px',
            borderRadius: '20px',
            fontWeight: 'bold',
            fontSize: '14px',
            whiteSpace: 'nowrap',
            pointerEvents: 'none',
            transform: hovered ? 'scale(1.1)' : 'scale(1)',
            transition: 'all 0.2s',
            boxShadow: hovered ? `0 0 20px ${jerseyColors.primary}` : 'none',
          }}
        >
          {name}
        </div>
      </Html>

      {/* Aura au survol */}
      {hovered && (
        <mesh position={[0, 1, 0]}>
          <sphereGeometry args={[1.3, 16, 16]} />
          <meshBasicMaterial color={jerseyColors.primary} transparent opacity={0.1} />
        </mesh>
      )}

      {/* Ombre */}
      <mesh position={[0, -0.95, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.8, 32]} />
        <meshBasicMaterial color="#000000" transparent opacity={0.3} />
      </mesh>

      {/* ========== CORPS ========== */}

      {/* Torse - Design spécifique selon le joueur avec plus de détails */}
      {isMessi ? (
        // Design Barcelone: Half-Half amélioré
        <>
          {/* Moitié gauche - Bleu avec texture */}
          <mesh position={[-0.2, 0.7, 0]} castShadow>
            <boxGeometry args={[0.42, 1, 0.52]} />
            <meshStandardMaterial color={jerseyColors.primary} roughness={0.6} metalness={0.1} />
          </mesh>
          {/* Moitié droite - Rouge avec texture */}
          <mesh position={[0.2, 0.7, 0]} castShadow>
            <boxGeometry args={[0.42, 1, 0.52]} />
            <meshStandardMaterial color={jerseyColors.secondary} roughness={0.6} metalness={0.1} />
          </mesh>
          {/* Ligne centrale dorée */}
          <mesh position={[0, 0.7, 0]}>
            <boxGeometry args={[0.02, 1, 0.54]} />
            <meshStandardMaterial color={jerseyColors.accent || '#FFD700'} metalness={0.8} roughness={0.2} />
          </mesh>
          {/* Logo Barcelone simplifié (voxel) */}
          <mesh position={[0, 0.9, 0.27]}>
            <boxGeometry args={[0.12, 0.12, 0.02]} />
            <meshStandardMaterial color="#FFD700" />
          </mesh>
          <mesh position={[0, 0.9, 0.28]}>
            <boxGeometry args={[0.08, 0.08, 0.02]} />
            <meshStandardMaterial color="#DC143C" />
          </mesh>
          {/* Sponsor texturé */}
          <mesh position={[0, 0.5, 0.27]}>
            <boxGeometry args={[0.3, 0.08, 0.01]} />
            <meshStandardMaterial color="#FFFFFF" />
          </mesh>
        </>
      ) : (
        // Design Real Madrid: Blanc avec accents dorés améliorés
        <>
          <mesh position={[0, 0.7, 0]} castShadow>
            <boxGeometry args={[0.8, 1, 0.5]} />
            <meshStandardMaterial color="#FFFFFF" roughness={0.5} metalness={0.1} />
          </mesh>
          {/* Bandes dorées sur les côtés avec effet métallique */}
          <mesh position={[-0.41, 0.7, 0]} castShadow>
            <boxGeometry args={[0.05, 0.95, 0.52]} />
            <meshStandardMaterial color={jerseyColors.secondary} metalness={0.7} roughness={0.2} />
          </mesh>
          <mesh position={[0.41, 0.7, 0]} castShadow>
            <boxGeometry args={[0.05, 0.95, 0.52]} />
            <meshStandardMaterial color={jerseyColors.secondary} metalness={0.7} roughness={0.2} />
          </mesh>
          {/* Logo Real Madrid simplifié (couronne voxel) */}
          <mesh position={[0.15, 0.9, 0.26]}>
            <boxGeometry args={[0.12, 0.12, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.8} roughness={0.2} />
          </mesh>
          <mesh position={[0.15, 0.98, 0.26]}>
            <boxGeometry args={[0.04, 0.04, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.8} />
          </mesh>
          {/* Sponsor Adidas simplifié */}
          <mesh position={[-0.15, 0.9, 0.26]}>
            <boxGeometry args={[0.1, 0.06, 0.02]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
          {/* Lignes de design sur le torse */}
          <mesh position={[0, 0.5, 0.26]}>
            <boxGeometry args={[0.4, 0.02, 0.01]} />
            <meshStandardMaterial color="#E0E0E0" />
          </mesh>
        </>
      )}

      {/* Col du maillot */}
      <mesh position={[0, 1.15, 0]}>
        <boxGeometry args={[0.35, 0.1, 0.35]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : jerseyColors.secondary} />
      </mesh>

      {/* Numéro sur le dos - 10 pour Messi, 7 pour Ronaldo - Version simplifiée voxel */}
      {isMessi ? (
        // Numéro 10 pour Messi - en pixels/voxels
        <group position={[0, 0.75, -0.27]}>
          {/* Chiffre 1 - barre verticale */}
          <mesh position={[-0.12, 0, 0]}>
            <boxGeometry args={[0.08, 0.35, 0.03]} />
            <meshStandardMaterial color="#FFD700" metalness={0.3} />
          </mesh>
          {/* Chiffre 1 - petit trait en haut */}
          <mesh position={[-0.16, 0.12, 0]}>
            <boxGeometry args={[0.08, 0.06, 0.03]} />
            <meshStandardMaterial color="#FFD700" metalness={0.3} />
          </mesh>

          {/* Chiffre 0 - contour haut */}
          <mesh position={[0.12, 0.16, 0]}>
            <boxGeometry args={[0.2, 0.06, 0.03]} />
            <meshStandardMaterial color="#FFD700" metalness={0.3} />
          </mesh>
          {/* Chiffre 0 - contour bas */}
          <mesh position={[0.12, -0.16, 0]}>
            <boxGeometry args={[0.2, 0.06, 0.03]} />
            <meshStandardMaterial color="#FFD700" metalness={0.3} />
          </mesh>
          {/* Chiffre 0 - contour gauche */}
          <mesh position={[0.04, 0, 0]}>
            <boxGeometry args={[0.06, 0.35, 0.03]} />
            <meshStandardMaterial color="#FFD700" metalness={0.3} />
          </mesh>
          {/* Chiffre 0 - contour droit */}
          <mesh position={[0.2, 0, 0]}>
            <boxGeometry args={[0.06, 0.35, 0.03]} />
            <meshStandardMaterial color="#FFD700" metalness={0.3} />
          </mesh>
        </group>
      ) : (
        // Numéro 7 pour Ronaldo - en pixels/voxels
        <group position={[0, 0.75, -0.27]}>
          {/* Barre horizontale haut */}
          <mesh position={[0, 0.14, 0]}>
            <boxGeometry args={[0.3, 0.08, 0.03]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
          {/* Barre diagonale - faite de segments */}
          <mesh position={[0.1, 0.06, 0]}>
            <boxGeometry args={[0.06, 0.12, 0.03]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
          <mesh position={[0.05, -0.02, 0]}>
            <boxGeometry args={[0.06, 0.12, 0.03]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
          <mesh position={[0, -0.08, 0]}>
            <boxGeometry args={[0.06, 0.12, 0.03]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
          {/* Barre verticale bas */}
          <mesh position={[-0.08, -0.12, 0]}>
            <boxGeometry args={[0.08, 0.1, 0.03]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
        </group>
      )}

      {/* Manches */}
      <mesh position={[-0.5, 0.9, 0]} castShadow>
        <boxGeometry args={[0.3, 0.4, 0.4]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.primary : '#FFFFFF'} />
      </mesh>
      <mesh position={[0.5, 0.9, 0]} castShadow>
        <boxGeometry args={[0.3, 0.4, 0.4]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : '#FFFFFF'} />
      </mesh>

      {/* Bandes sur les manches (Ronaldo) */}
      {isRonaldo && (
        <>
          <mesh position={[-0.5, 0.9, 0.21]}>
            <boxGeometry args={[0.32, 0.08, 0.02]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
          <mesh position={[0.5, 0.9, 0.21]}>
            <boxGeometry args={[0.32, 0.08, 0.02]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
        </>
      )}

      {/* Tête */}
      <mesh position={[0, 1.5, 0]} castShadow>
        <boxGeometry args={[0.5, 0.5, 0.5]} />
        <meshStandardMaterial color="#ffdbac" roughness={0.5} />
      </mesh>

      {/* Cheveux - Style spécifique */}
      {isMessi ? (
        // Cheveux Messi (plus courts, style actuel)
        <>
          <mesh position={[0, 1.78, 0]}>
            <boxGeometry args={[0.52, 0.12, 0.52]} />
            <meshStandardMaterial color="#2d1810" />
          </mesh>
          <mesh position={[0, 1.75, -0.22]}>
            <boxGeometry args={[0.52, 0.18, 0.1]} />
            <meshStandardMaterial color="#2d1810" />
          </mesh>
        </>
      ) : (
        // Cheveux Ronaldo (style coiffé, plus haut)
        <>
          <mesh position={[0, 1.82, 0]}>
            <boxGeometry args={[0.52, 0.18, 0.52]} />
            <meshStandardMaterial color="#2d1810" />
          </mesh>
          <mesh position={[0, 1.78, -0.22]}>
            <boxGeometry args={[0.52, 0.15, 0.1]} />
            <meshStandardMaterial color="#2d1810" />
          </mesh>
          {/* Mèche sur le front */}
          <mesh position={[0, 1.85, 0.15]}>
            <boxGeometry args={[0.3, 0.08, 0.1]} />
            <meshStandardMaterial color="#2d1810" />
          </mesh>
        </>
      )}

      {/* Visage amélioré */}
      {/* Yeux avec iris */}
      <mesh position={[-0.12, 1.55, 0.26]}>
        <boxGeometry args={[0.08, 0.08, 0.02]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[0.12, 1.55, 0.26]}>
        <boxGeometry args={[0.08, 0.08, 0.02]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      {/* Pupilles */}
      <mesh position={[-0.12, 1.55, 0.27]}>
        <boxGeometry args={[0.04, 0.04, 0.01]} />
        <meshBasicMaterial color="#4A3728" />
      </mesh>
      <mesh position={[0.12, 1.55, 0.27]}>
        <boxGeometry args={[0.04, 0.04, 0.01]} />
        <meshBasicMaterial color="#4A3728" />
      </mesh>
      {/* Sourcils */}
      <mesh position={[-0.12, 1.62, 0.26]}>
        <boxGeometry args={[0.1, 0.03, 0.02]} />
        <meshBasicMaterial color={isMessi ? "#2d1810" : "#1a1a1a"} />
      </mesh>
      <mesh position={[0.12, 1.62, 0.26]}>
        <boxGeometry args={[0.1, 0.03, 0.02]} />
        <meshBasicMaterial color={isMessi ? "#2d1810" : "#1a1a1a"} />
      </mesh>
      {/* Nez */}
      <mesh position={[0, 1.48, 0.28]}>
        <boxGeometry args={[0.04, 0.04, 0.02]} />
        <meshStandardMaterial color="#e6c2a0" />
      </mesh>
      {/* Bouche */}
      <mesh position={[0, 1.42, 0.26]}>
        <boxGeometry args={[0.1, 0.02, 0.01]} />
        <meshBasicMaterial color="#c4956a" />
      </mesh>

      {/* Shorts améliorés */}
      <mesh position={[-0.22, 0.2, 0]} castShadow>
        <boxGeometry args={[0.35, 0.55, 0.45]} />
        <meshStandardMaterial color={jerseyColors.shorts} roughness={0.7} />
      </mesh>
      <mesh position={[0.22, 0.2, 0]} castShadow>
        <boxGeometry args={[0.35, 0.55, 0.45]} />
        <meshStandardMaterial color={jerseyColors.shorts} roughness={0.7} />
      </mesh>

      {/* Ceinture du short */}
      <mesh position={[0, 0.42, 0]}>
        <boxGeometry args={[0.82, 0.08, 0.47]} />
        <meshStandardMaterial color={isMessi ? "#004D98" : "#000000"} />
      </mesh>

      {/* Bandes sur les shorts */}
      {isRonaldo && (
        <>
          <mesh position={[-0.22, 0.2, 0.23]}>
            <boxGeometry args={[0.37, 0.45, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.6} />
          </mesh>
          <mesh position={[0.22, 0.2, 0.23]}>
            <boxGeometry args={[0.37, 0.45, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.6} />
          </mesh>
          {/* Logo sur le short */}
          <mesh position={[0, 0.2, 0.24]}>
            <boxGeometry args={[0.1, 0.1, 0.02]} />
            <meshStandardMaterial color="#FFFFFF" />
          </mesh>
        </>
      )}

      {/* Logo équipe sur le short (Barcelone) */}
      {isMessi && (
        <mesh position={[0, 0.2, 0.24]}>
          <boxGeometry args={[0.12, 0.12, 0.02]} />
          <meshStandardMaterial color="#FFD700" />
        </mesh>
      )}

      {/* Cuisses améliorées */}
      <mesh position={[-0.22, -0.2, 0]} castShadow>
        <boxGeometry args={[0.28, 0.5, 0.32]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      <mesh position={[0.22, -0.2, 0]} castShadow>
        <boxGeometry args={[0.28, 0.5, 0.32]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>

      {/* Genoux */}
      <mesh position={[-0.22, -0.5, 0.02]} castShadow>
        <boxGeometry args={[0.22, 0.15, 0.25]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      <mesh position={[0.22, -0.5, 0.02]} castShadow>
        <boxGeometry args={[0.22, 0.15, 0.25]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>

      {/* Chaussettes améliorées */}
      <mesh position={[-0.22, -0.78, 0]} castShadow>
        <boxGeometry args={[0.24, 0.5, 0.28]} />
        <meshStandardMaterial color={jerseyColors.socks} />
      </mesh>
      <mesh position={[0.22, -0.78, 0]} castShadow>
        <boxGeometry args={[0.24, 0.5, 0.28]} />
        <meshStandardMaterial color={jerseyColors.socks} />
      </mesh>

      {/* Bandes chaussettes haut */}
      <mesh position={[-0.22, -0.58, 0]}>
        <boxGeometry args={[0.26, 0.1, 0.3]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : '#000000'} />
      </mesh>
      <mesh position={[0.22, -0.58, 0]}>
        <boxGeometry args={[0.26, 0.1, 0.3]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : '#000000'} />
      </mesh>

      {/* Bandes chaussettes milieu */}
      <mesh position={[-0.22, -0.78, 0]}>
        <boxGeometry args={[0.26, 0.06, 0.3]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : '#000000'} />
      </mesh>
      <mesh position={[0.22, -0.78, 0]}>
        <boxGeometry args={[0.26, 0.06, 0.3]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : '#000000'} />
      </mesh>

      {/* Revers des chaussettes */}
      <mesh position={[-0.22, -0.52, 0]}>
        <boxGeometry args={[0.26, 0.05, 0.3]} />
        <meshStandardMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[0.22, -0.52, 0]}>
        <boxGeometry args={[0.26, 0.05, 0.3]} />
        <meshStandardMaterial color="#FFFFFF" />
      </mesh>

      {/* Chaussures améliorées */}
      {/* Base de la chaussure */}
      <mesh position={[-0.22, -1.05, 0.05]} castShadow>
        <boxGeometry args={[0.3, 0.12, 0.5]} />
        <meshStandardMaterial color="#1a1a1a" roughness={0.8} />
      </mesh>
      <mesh position={[0.22, -1.05, 0.05]} castShadow>
        <boxGeometry args={[0.3, 0.12, 0.5]} />
        <meshStandardMaterial color="#1a1a1a" roughness={0.8} />
      </mesh>

      {/* Partie haute de la chaussure */}
      <mesh position={[-0.22, -0.92, 0.05]} castShadow>
        <boxGeometry args={[0.26, 0.18, 0.35]} />
        <meshStandardMaterial color={isMessi ? "#FF1493" : "#1a1a1a"} />
      </mesh>
      <mesh position={[0.22, -0.92, 0.05]} castShadow>
        <boxGeometry args={[0.26, 0.18, 0.35]} />
        <meshStandardMaterial color={isMessi ? "#00BFFF" : "#1a1a1a"} />
      </mesh>

      {/* Lacets */}
      <mesh position={[-0.22, -0.88, 0.15]} castShadow>
        <boxGeometry args={[0.18, 0.03, 0.15]} />
        <meshStandardMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[0.22, -0.88, 0.15]} castShadow>
        <boxGeometry args={[0.18, 0.03, 0.15]} />
        <meshStandardMaterial color="#FFFFFF" />
      </mesh>

      {/* Semelles (crampes) */}
      <mesh position={[-0.22, -1.12, 0.15]} castShadow>
        <boxGeometry args={[0.05, 0.05, 0.05]} />
        <meshStandardMaterial color="#C0C0C0" metalness={0.8} />
      </mesh>
      <mesh position={[-0.22, -1.12, -0.1]} castShadow>
        <boxGeometry args={[0.05, 0.05, 0.05]} />
        <meshStandardMaterial color="#C0C0C0" metalness={0.8} />
      </mesh>
      <mesh position={[0.22, -1.12, 0.15]} castShadow>
        <boxGeometry args={[0.05, 0.05, 0.05]} />
        <meshStandardMaterial color="#C0C0C0" metalness={0.8} />
      </mesh>
      <mesh position={[0.22, -1.12, -0.1]} castShadow>
        <boxGeometry args={[0.05, 0.05, 0.05]} />
        <meshStandardMaterial color="#C0C0C0" metalness={0.8} />
      </mesh>

      {/* Logo chaussures (Ronaldo - Nike swoosh doré) */}
      {isRonaldo && (
        <>
          <mesh position={[-0.22, -0.92, 0.24]}>
            <boxGeometry args={[0.08, 0.04, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.8} />
          </mesh>
          <mesh position={[-0.2, -0.9, 0.24]}>
            <boxGeometry args={[0.04, 0.06, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.8} />
          </mesh>
          <mesh position={[0.22, -0.92, 0.24]}>
            <boxGeometry args={[0.08, 0.04, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.8} />
          </mesh>
          <mesh position={[0.2, -0.9, 0.24]}>
            <boxGeometry args={[0.04, 0.06, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.8} />
          </mesh>
        </>
      )}

      {/* Bras améliorés avec épaules et mains */}
      {/* Épaules */}
      <mesh position={[-0.5, 1.1, 0]} castShadow>
        <boxGeometry args={[0.3, 0.25, 0.3]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.primary : "#FFFFFF"} roughness={0.7} />
      </mesh>
      <mesh position={[0.5, 1.1, 0]} castShadow>
        <boxGeometry args={[0.3, 0.25, 0.3]} />
        <meshStandardMaterial color={isMessi ? jerseyColors.secondary : "#FFFFFF"} roughness={0.7} />
      </mesh>

      {/* Bras (haut) */}
      <mesh position={[-0.5, 0.7, 0]} castShadow>
        <boxGeometry args={[0.18, 0.5, 0.18]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      <mesh position={[0.5, 0.7, 0]} castShadow>
        <boxGeometry args={[0.18, 0.5, 0.18]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>

      {/* Avant-bras */}
      <mesh position={[-0.5, 0.35, 0.1]} castShadow rotation={[0.3, 0, 0]}>
        <boxGeometry args={[0.16, 0.4, 0.16]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      <mesh position={[0.5, 0.35, 0.1]} castShadow rotation={[0.3, 0, 0]}>
        <boxGeometry args={[0.16, 0.4, 0.16]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>

      {/* Mains */}
      <mesh position={[-0.5, 0.1, 0.15]} castShadow>
        <boxGeometry args={[0.15, 0.15, 0.15]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>
      <mesh position={[0.5, 0.1, 0.15]} castShadow>
        <boxGeometry args={[0.15, 0.15, 0.15]} />
        <meshStandardMaterial color="#ffdbac" />
      </mesh>

      {/* Brassard de capitaine (Messi) - Amélioré */}
      {isMessi && (
        <>
          <mesh position={[-0.5, 0.7, 0.1]}>
            <boxGeometry args={[0.22, 0.2, 0.02]} />
            <meshStandardMaterial color="#FFD700" metalness={0.6} roughness={0.3} />
          </mesh>
          {/* Symbole C sur le brassard */}
          <mesh position={[-0.5, 0.7, 0.11]}>
            <boxGeometry args={[0.08, 0.12, 0.01]} />
            <meshBasicMaterial color="#000000" />
          </mesh>
        </>
      )}

      {/* Bracelet (Ronaldo) */}
      {isRonaldo && (
        <>
          <mesh position={[0.5, 0.35, 0.19]}>
            <boxGeometry args={[0.18, 0.05, 0.02]} />
            <meshStandardMaterial color="#FFFFFF" />
          </mesh>
          <mesh position={[0.5, 0.33, 0.19]}>
            <boxGeometry args={[0.18, 0.02, 0.02]} />
            <meshStandardMaterial color="#000000" />
          </mesh>
        </>
      )}
    </group>
  );
}
