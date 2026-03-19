'use client';

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Arbre
function VoxelTree({ position, scale = 1 }: { position: [number, number, number]; scale?: number }) {
  const treeRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (treeRef.current) {
      treeRef.current.rotation.z = Math.sin(state.clock.elapsedTime * 0.5) * 0.02;
    }
  });

  return (
    <group ref={treeRef} position={position} scale={scale}>
      {/* Tronc */}
      <mesh position={[0, 1, 0]} castShadow>
        <boxGeometry args={[0.4, 2, 0.4]} />
        <meshStandardMaterial color="#5D4037" />
      </mesh>

      {/* Feuillage */}
      <mesh position={[0, 2.5, 0]} castShadow>
        <boxGeometry args={[2, 1.2, 2]} />
        <meshStandardMaterial color="#2E7D32" />
      </mesh>
      <mesh position={[0, 3.3, 0]} castShadow>
        <boxGeometry args={[1.4, 0.8, 1.4]} />
        <meshStandardMaterial color="#388E3C" />
      </mesh>
    </group>
  );
}

// Gradins/Stade améliorés
function StadiumStands() {
  return (
    <group>
      {/* Escaliers de secours entre les sections */}
      {Array.from({ length: 6 }).map((_, i) => (
        <>
          {/* Escalier gauche */}
          <mesh key={`stairs-left-${i}`} position={[-32, -0.8 + i * 0.35, -15 + i * 6]} receiveShadow>
            <boxGeometry args={[1.5, 0.1, 4]} />
            <meshStandardMaterial color="#718096" />
          </mesh>
          {/* Escalier droit */}
          <mesh key={`stairs-right-${i}`} position={[32, -0.8 + i * 0.35, -15 + i * 6]} receiveShadow>
            <boxGeometry args={[1.5, 0.1, 4]} />
            <meshStandardMaterial color="#718096" />
          </mesh>
        </>
      ))}

      {/* Gradins principaux - Côté gauche avec plus de détails */}
      {Array.from({ length: 15 }).map((_, row) => (
        <group key={`left-${row}`}>
          {/* Marche */}
          <mesh position={[-34 - row * 1.2, -0.6 + row * 0.35, 0]} receiveShadow>
            <boxGeometry args={[1.2, 0.6, 52]} />
            <meshStandardMaterial color={row % 3 === 0 ? '#1a365d' : row % 3 === 1 ? '#2c5282' : '#2d3748'} />
          </mesh>
          {/* Siège */}
          <mesh position={[-34 - row * 1.2, -0.2 + row * 0.35, 0]} receiveShadow>
            <boxGeometry args={[0.9, 0.15, 50]} />
            <meshStandardMaterial color={row % 2 === 0 ? '#C53030' : '#C53030'} />
          </mesh>
          {/* Dossier */}
          <mesh position={[-34.3 - row * 1.2, 0.1 + row * 0.35, 0]} receiveShadow>
            <boxGeometry args={[0.1, 0.4, 50]} />
            <meshStandardMaterial color="#742A2A" />
          </mesh>
        </group>
      ))}

      {/* Gradins principaux - Côté droit */}
      {Array.from({ length: 15 }).map((_, row) => (
        <group key={`right-${row}`}>
          {/* Marche */}
          <mesh position={[34 + row * 1.2, -0.6 + row * 0.35, 0]} receiveShadow>
            <boxGeometry args={[1.2, 0.6, 52]} />
            <meshStandardMaterial color={row % 3 === 0 ? '#1a365d' : row % 3 === 1 ? '#2c5282' : '#2d3748'} />
          </mesh>
          {/* Siège */}
          <mesh position={[34 + row * 1.2, -0.2 + row * 0.35, 0]} receiveShadow>
            <boxGeometry args={[0.9, 0.15, 50]} />
            <meshStandardMaterial color={row % 2 === 0 ? '#C53030' : '#C53030'} />
          </mesh>
          {/* Dossier */}
          <mesh position={[34.3 + row * 1.2, 0.1 + row * 0.35, 0]} receiveShadow>
            <boxGeometry args={[0.1, 0.4, 50]} />
            <meshStandardMaterial color="#742A2A" />
          </mesh>
        </group>
      ))}

      {/* Gradins - Fond (tribune principale) */}
      {Array.from({ length: 18 }).map((_, row) => (
        <group key={`back-${row}`}>
          {/* Marche */}
          <mesh position={[-25, -0.6 + row * 0.35, -24 - row * 1.2]} receiveShadow>
            <boxGeometry args={[16, 0.6, 1.2]} />
            <meshStandardMaterial color={row % 3 === 0 ? '#1a365d' : row % 3 === 1 ? '#2c5282' : '#2d3748'} />
          </mesh>
          <mesh position={[25, -0.6 + row * 0.35, -24 - row * 1.2]} receiveShadow>
            <boxGeometry args={[16, 0.6, 1.2]} />
            <meshStandardMaterial color={row % 3 === 0 ? '#1a365d' : row % 3 === 1 ? '#2c5282' : '#2d3748'} />
          </mesh>
          {/* Sièges */}
          <mesh position={[-25, -0.2 + row * 0.35, -24 - row * 1.2]} receiveShadow>
            <boxGeometry args={[14, 0.15, 0.9]} />
            <meshStandardMaterial color="#C53030" />
          </mesh>
          <mesh position={[25, -0.2 + row * 0.35, -24 - row * 1.2]} receiveShadow>
            <boxGeometry args={[14, 0.15, 0.9]} />
            <meshStandardMaterial color="#C53030" />
          </mesh>
        </group>
      ))}

      {/* Gradins tribune centrale (derrière le but) */}
      {Array.from({ length: 12 }).map((_, row) => (
        <group key={`back-center-${row}`}>
          <mesh position={[0, -0.6 + row * 0.35, -24 - row * 1.2]} receiveShadow>
            <boxGeometry args={[34, 0.6, 1.2]} />
            <meshStandardMaterial color={row % 3 === 0 ? '#1a365d' : row % 3 === 1 ? '#2c5282' : '#2d3748'} />
          </mesh>
          <mesh position={[0, -0.2 + row * 0.35, -24 - row * 1.2]} receiveShadow>
            <boxGeometry args={[32, 0.15, 0.9]} />
            <meshStandardMaterial color="#C53030" />
          </mesh>
        </group>
      ))}

      {/* Coins arrondis des gradins */}
      {Array.from({ length: 10 }).map((_, row) => (
        <group key={`corner-${row}`}>
          {/* Coin arrière gauche */}
          <mesh position={[-30 - row * 0.9, -0.5 + row * 0.35, -20 - row * 0.9]} receiveShadow>
            <boxGeometry args={[1.2, 0.6, 1.2]} />
            <meshStandardMaterial color={row % 2 === 0 ? '#1a365d' : '#2c5282'} />
          </mesh>
          {/* Coin arrière droit */}
          <mesh position={[30 + row * 0.9, -0.5 + row * 0.35, -20 - row * 0.9]} receiveShadow>
            <boxGeometry args={[1.2, 0.6, 1.2]} />
            <meshStandardMaterial color={row % 2 === 0 ? '#1a365d' : '#2c5282'} />
          </mesh>
        </group>
      ))}

      {/* Spectateurs voxel - Côtés (plus nombreux et variés) */}
      {Array.from({ length: 80 }).map((_, i) => {
        const side = i % 2 === 0 ? 'left' : 'right';
        const row = Math.floor(i / 10);
        const col = i % 10;
        const x = side === 'left' ? -34 - row * 1.2 : 34 + row * 1.2;
        const z = -20 + col * 4;
        const y = -0.1 + row * 0.35;
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#FF1493', '#00CED1'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        const skinColors = ['#ffdbac', '#f1c27d', '#e0ac69', '#8d5524', '#c68642'];
        const skinColor = skinColors[Math.floor(Math.random() * skinColors.length)];

        return (
          <group key={`spectator-side-${i}`} position={[x, y, z]}>
            {/* Corps */}
            <mesh position={[0, 0.25, 0]}>
              <boxGeometry args={[0.22, 0.3, 0.22]} />
              <meshStandardMaterial color={color} />
            </mesh>
            {/* Tête */}
            <mesh position={[0, 0.5, 0]}>
              <boxGeometry args={[0.18, 0.18, 0.18]} />
              <meshStandardMaterial color={skinColor} />
            </mesh>
            {/* Bras levés aléatoirement */}
            {Math.random() > 0.7 && (
              <>
                <mesh position={[-0.15, 0.4, 0]} rotation={[0, 0, 0.5]}>
                  <boxGeometry args={[0.06, 0.25, 0.06]} />
                  <meshStandardMaterial color={color} />
                </mesh>
                <mesh position={[0.15, 0.4, 0]} rotation={[0, 0, -0.5]}>
                  <boxGeometry args={[0.06, 0.25, 0.06]} />
                  <meshStandardMaterial color={color} />
                </mesh>
              </>
            )}
          </group>
        );
      })}

      {/* Spectateurs voxel - Tribune centrale */}
      {Array.from({ length: 60 }).map((_, i) => {
        const row = Math.floor(i / 10);
        const col = i % 10;
        const x = -15 + col * 3;
        const z = -24 - row * 1.2;
        const y = -0.1 + row * 0.35;
        const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2', '#FF1493', '#00CED1'];
        const color = colors[Math.floor(Math.random() * colors.length)];
        const skinColors = ['#ffdbac', '#f1c27d', '#e0ac69', '#8d5524', '#c68642'];
        const skinColor = skinColors[Math.floor(Math.random() * skinColors.length)];

        return (
          <group key={`spectator-center-${i}`} position={[x, y, z]}>
            <mesh position={[0, 0.25, 0]}>
              <boxGeometry args={[0.22, 0.3, 0.22]} />
              <meshStandardMaterial color={color} />
            </mesh>
            <mesh position={[0, 0.5, 0]}>
              <boxGeometry args={[0.18, 0.18, 0.18]} />
              <meshStandardMaterial color={skinColor} />
            </mesh>
          </group>
        );
      })}

      {/* Structure du stade - Piliers renforcés */}
      {[
        [-40, -25], [-40, 25], [40, -25], [40, 25],
        [-30, -30], [30, -30], [-30, 30], [30, 30],
        [-50, 0], [50, 0], [0, -45]
      ].map(([x, z], i) => (
        <group key={`pillar-${i}`}>
          <mesh position={[x, 3, z]} castShadow>
            <boxGeometry args={[1.5, 8, 1.5]} />
            <meshStandardMaterial color="#2d3748" />
          </mesh>
          {/* Base du pilier */}
          <mesh position={[x, -0.5, z]} castShadow>
            <boxGeometry args={[2.5, 1, 2.5]} />
            <meshStandardMaterial color="#1a202c" />
          </mesh>
        </group>
      ))}

      {/* Toit complet du stade */}
      <group>
        {/* Toit tribune centrale */}
        <mesh position={[0, 6.5, -35]}>
          <boxGeometry args={[90, 0.4, 25]} />
          <meshStandardMaterial color="#1a202c" transparent opacity={0.95} />
        </mesh>
        {/* Toit côtés */}
        <mesh position={[-50, 6, 0]}>
          <boxGeometry args={[20, 0.4, 60]} />
          <meshStandardMaterial color="#1a202c" transparent opacity={0.95} />
        </mesh>
        <mesh position={[50, 6, 0]}>
          <boxGeometry args={[20, 0.4, 60]} />
          <meshStandardMaterial color="#1a202c" transparent opacity={0.95} />
        </mesh>
        {/* Poutres du toit */}
        {Array.from({ length: 8 }).map((_, i) => (
          <>
            <mesh key={`beam-l-${i}`} position={[-50, 5.5, -25 + i * 7]} castShadow>
              <boxGeometry args={[18, 0.3, 0.5]} />
              <meshStandardMaterial color="#4a5568" />
            </mesh>
            <mesh key={`beam-r-${i}`} position={[50, 5.5, -25 + i * 7]} castShadow>
              <boxGeometry args={[18, 0.3, 0.5]} />
              <meshStandardMaterial color="#4a5568" />
            </mesh>
          </>
        ))}
      </group>

      {/* Panneaux publicitaires LED - Touchant le sol */}
      <group>
        {/* Support du panneau arrière */}
        <mesh position={[0, -0.25, -15.5]} castShadow>
          <boxGeometry args={[32, 0.5, 0.2]} />
          <meshStandardMaterial color="#1a202c" />
        </mesh>
        {/* Panneau LED arrière */}
        <mesh position={[0, 0.4, -15.5]} castShadow>
          <boxGeometry args={[32, 1.2, 0.1]} />
          <meshStandardMaterial color="#000000" />
        </mesh>
        {/* Lignes LED */}
        {Array.from({ length: 5 }).map((_, i) => (
          <mesh key={`led-back-${i}`} position={[-12 + i * 6, 0.4, -15.45]}>
            <boxGeometry args={[4, 0.8, 0.05]} />
            <meshBasicMaterial color={i % 2 === 0 ? '#00FF00' : '#FFFFFF'} />
          </mesh>
        ))}

        {/* Support du panneau avant */}
        <mesh position={[0, -0.25, 15.5]} castShadow>
          <boxGeometry args={[32, 0.5, 0.2]} />
          <meshStandardMaterial color="#1a202c" />
        </mesh>
        {/* Panneau LED avant */}
        <mesh position={[0, 0.4, 15.5]} castShadow>
          <boxGeometry args={[32, 1.2, 0.1]} />
          <meshStandardMaterial color="#000000" />
        </mesh>
        {Array.from({ length: 5 }).map((_, i) => (
          <mesh key={`led-front-${i}`} position={[-12 + i * 6, 0.4, 15.45]}>
            <boxGeometry args={[4, 0.8, 0.05]} />
            <meshBasicMaterial color={i % 2 === 0 ? '#00FF00' : '#FFFFFF'} />
          </mesh>
        ))}
      </group>

      {/* Projecteurs améliorés */}
      {[
        [-35, 10, -35], [35, 10, -35], [-35, 10, 35], [35, 10, 35],
        [0, 12, -45], [-45, 10, 0], [45, 10, 0]
      ].map(([x, y, z], i) => (
        <group key={`floodlight-${i}`} position={[x, y, z]}>
          {/* Support */}
          <mesh position={[0, -2, 0]} castShadow>
            <boxGeometry args={[0.5, 4, 0.5]} />
            <meshStandardMaterial color="#2d3748" />
          </mesh>
          {/* Base */}
          <mesh position={[0, -4.2, 0]} castShadow>
            <boxGeometry args={[2, 0.5, 2]} />
            <meshStandardMaterial color="#1a202c" />
          </mesh>
          {/* Projecteur */}
          <mesh>
            <boxGeometry args={[3, 1.5, 3]} />
            <meshStandardMaterial color="#1a202c" />
          </mesh>
          {/* Lumière */}
          <mesh position={[0, -0.1, 0]}>
            <boxGeometry args={[2.5, 0.1, 2.5]} />
            <meshBasicMaterial color="#FFFFE0" />
          </mesh>
          {/* Lumière spot */}
          <spotLight
            position={[0, 0, 0]}
            target-position={[0, -15, 0]}
            angle={Math.PI / 3}
            penumbra={0.3}
            intensity={0.8}
            distance={80}
            castShadow
          />
        </group>
      ))}

      {/* Drapeaux aux coins */}
      {[
        [-48, -48], [48, -48], [-48, 48], [48, 48]
      ].map(([x, z], i) => (
        <group key={`flag-${i}`} position={[x, 0, z]}>
          {/* Mât */}
          <mesh position={[0, 6, 0]} castShadow>
            <boxGeometry args={[0.1, 12, 0.1]} />
            <meshStandardMaterial color="#C0C0C0" metalness={0.8} />
          </mesh>
          {/* Drapeau */}
          <mesh position={[1, 11, 0]}>
            <boxGeometry args={[2, 1.2, 0.05]} />
            <meshStandardMaterial color={i % 2 === 0 ? '#004D98' : '#A50044'} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

// Buts orientés correctement (perpendiculaires au terrain) - Améliorés
function SoccerGoal({ position, isLeft = true }: { position: [number, number, number]; isLeft?: boolean }) {
  return (
    <group position={position}>
      {/* Poteaux - maintenant orientés le long de l'axe Z (perpendiculaires) */}
      <mesh position={[0, 1.2, -3.66]} castShadow>
        <boxGeometry args={[0.12, 2.44, 0.12]} />
        <meshStandardMaterial color="#FFFFFF" metalness={0.3} roughness={0.4} />
      </mesh>
      <mesh position={[0, 1.2, 3.66]} castShadow>
        <boxGeometry args={[0.12, 2.44, 0.12]} />
        <meshStandardMaterial color="#FFFFFF" metalness={0.3} roughness={0.4} />
      </mesh>

      {/* Barre transversale */}
      <mesh position={[0, 2.44, 0]} castShadow>
        <boxGeometry args={[0.12, 0.12, 7.44]} />
        <meshStandardMaterial color="#FFFFFF" metalness={0.3} roughness={0.4} />
      </mesh>

      {/* Barres de fond - poteaux */}
      <mesh position={[isLeft ? -1.8 : 1.8, 1.2, -3.66]} castShadow>
        <boxGeometry args={[0.1, 2.44, 0.1]} />
        <meshStandardMaterial color="#FFFFFF" metalness={0.3} />
      </mesh>
      <mesh position={[isLeft ? -1.8 : 1.8, 1.2, 3.66]} castShadow>
        <boxGeometry args={[0.1, 2.44, 0.1]} />
        <meshStandardMaterial color="#FFFFFF" metalness={0.3} />
      </mesh>

      {/* Barre transversale du fond */}
      <mesh position={[isLeft ? -1.8 : 1.8, 2.44, 0]} castShadow>
        <boxGeometry args={[0.1, 0.1, 7.44]} />
        <meshStandardMaterial color="#FFFFFF" metalness={0.3} />
      </mesh>

      {/* Barres diagonales de soutien */}
      <mesh position={[isLeft ? -0.9 : 0.9, 1.8, -3.66]} rotation={[0, 0, isLeft ? 0.5 : -0.5]} castShadow>
        <boxGeometry args={[0.08, 1.5, 0.08]} />
        <meshStandardMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[isLeft ? -0.9 : 0.9, 1.8, 3.66]} rotation={[0, 0, isLeft ? 0.5 : -0.5]} castShadow>
        <boxGeometry args={[0.08, 1.5, 0.08]} />
        <meshStandardMaterial color="#FFFFFF" />
      </mesh>

      {/* Filet - grille */}
      {Array.from({ length: 15 }).map((_, i) => (
        <>
          {/* Lignes verticales */}
          <mesh key={`net-v-${i}`} position={[isLeft ? -0.9 + (i * 0.12) : 0.9 - (i * 0.12), 1.2, 0]}>
            <boxGeometry args={[0.01, 2.4, 0.01]} />
            <meshBasicMaterial color="#E8E8E8" transparent opacity={0.6} />
          </mesh>
        </>
      ))}
      {Array.from({ length: 12 }).map((_, i) => (
        <>
          {/* Lignes horizontales */}
          <mesh key={`net-h-${i}`} position={[isLeft ? -0.9 : 0.9, 0.2 + i * 0.2, 0]}>
            <boxGeometry args={[1.8, 0.01, 7.4]} />
            <meshBasicMaterial color="#E8E8E8" transparent opacity={0.6} />
          </mesh>
        </>
      ))}

      {/* Filet diagonal (côtés) */}
      <mesh position={[isLeft ? -0.9 : 0.9, 1.2, -3.66]} rotation={[0, 0, isLeft ? 0.8 : -0.8]}>
        <boxGeometry args={[0.02, 2.8, 0.02]} />
        <meshBasicMaterial color="#E8E8E8" transparent opacity={0.5} />
      </mesh>
      <mesh position={[isLeft ? -0.9 : 0.9, 1.2, 3.66]} rotation={[0, 0, isLeft ? 0.8 : -0.8]}>
        <boxGeometry args={[0.02, 2.8, 0.02]} />
        <meshBasicMaterial color="#E8E8E8" transparent opacity={0.5} />
      </mesh>
    </group>
  );
}

// Ballon amélioré
function SoccerBall({ position }: { position: [number, number, number] }) {
  const ballRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (ballRef.current) {
      ballRef.current.rotation.x += 0.02;
      ballRef.current.rotation.y += 0.03;
      ballRef.current.rotation.z += 0.01;
      ballRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 3) * 0.08;
    }
  });

  return (
    <group ref={ballRef} position={position}>
      {/* Base blanche */}
      <mesh castShadow>
        <boxGeometry args={[0.35, 0.35, 0.35]} />
        <meshStandardMaterial color="#FFFFFF" roughness={0.4} />
      </mesh>

      {/* Motif noir - face avant */}
      <mesh position={[0, 0, 0.18]}>
        <boxGeometry args={[0.15, 0.15, 0.02]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Motif noir - face arrière */}
      <mesh position={[0, 0, -0.18]}>
        <boxGeometry args={[0.15, 0.15, 0.02]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Motif noir - face droite */}
      <mesh position={[0.18, 0, 0]}>
        <boxGeometry args={[0.02, 0.15, 0.15]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Motif noir - face gauche */}
      <mesh position={[-0.18, 0, 0]}>
        <boxGeometry args={[0.02, 0.15, 0.15]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Motif noir - dessus */}
      <mesh position={[0, 0.18, 0]}>
        <boxGeometry args={[0.15, 0.02, 0.15]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Motif noir - dessous */}
      <mesh position={[0, -0.18, 0]}>
        <boxGeometry args={[0.15, 0.02, 0.15]} />
        <meshStandardMaterial color="#000000" />
      </mesh>

      {/* Détails supplémentaires - coins */}
      <mesh position={[0.12, 0.12, 0.12]}>
        <boxGeometry args={[0.08, 0.08, 0.08]} />
        <meshStandardMaterial color="#000000" />
      </mesh>
      <mesh position={[-0.12, 0.12, 0.12]}>
        <boxGeometry args={[0.08, 0.08, 0.08]} />
        <meshStandardMaterial color="#000000" />
      </mesh>
      <mesh position={[0.12, -0.12, 0.12]}>
        <boxGeometry args={[0.08, 0.08, 0.08]} />
        <meshStandardMaterial color="#000000" />
      </mesh>
      <mesh position={[-0.12, -0.12, 0.12]}>
        <boxGeometry args={[0.08, 0.08, 0.08]} />
        <meshStandardMaterial color="#000000" />
      </mesh>
    </group>
  );
}

// Nuage
function Cloud({ position }: { position: [number, number, number] }) {
  const cloudRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (cloudRef.current) {
      cloudRef.current.position.x = position[0] + Math.sin(state.clock.elapsedTime * 0.1) * 2;
    }
  });

  return (
    <group ref={cloudRef} position={position}>
      <mesh>
        <boxGeometry args={[2, 0.6, 1]} />
        <meshStandardMaterial color="#FFFFFF" transparent opacity={0.8} />
      </mesh>
      <mesh position={[-1, 0.2, 0]}>
        <boxGeometry args={[1.2, 0.5, 0.8]} />
        <meshStandardMaterial color="#FFFFFF" transparent opacity={0.7} />
      </mesh>
      <mesh position={[1, 0.1, 0]}>
        <boxGeometry args={[1.3, 0.6, 0.8]} />
        <meshStandardMaterial color="#FFFFFF" transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

export default function VoxelEnvironment() {
  return (
    <>
      {/* Gradins du stade */}
      <StadiumStands />

      {/* Terrain plat simple */}
      <mesh position={[0, -1, 0]} receiveShadow>
        <boxGeometry args={[50, 0.5, 30]} />
        <meshStandardMaterial color="#4CAF50" roughness={0.9} />
      </mesh>

      {/* Bandes d'herbe - Plus de variété */}
      {Array.from({ length: 16 }).map((_, i) => (
        <mesh
          key={i}
          position={[-22.5 + i * 3, -0.72, 0]}
          receiveShadow
        >
          <boxGeometry args={[3, 0.02, 30]} />
          <meshStandardMaterial color={i % 2 === 0 ? "#66BB6A" : "#4CAF50"} />
        </mesh>
      ))}

      {/* Herbe aléatoire pour texture */}
      {Array.from({ length: 50 }).map((_, i) => {
        const x = (Math.random() - 0.5) * 48;
        const z = (Math.random() - 0.5) * 28;
        if (Math.abs(x) > 2 || Math.abs(z) > 2) {
          const grassColors = ['#4CAF50', '#66BB6A', '#81C784', '#388E3C', '#2E7D32'];
          return (
            <mesh key={`grass-${i}`} position={[x, -0.73, z]}>
              <boxGeometry args={[0.4, 0.04, 0.4]} />
              <meshStandardMaterial color={grassColors[Math.floor(Math.random() * grassColors.length)]} />
            </mesh>
          );
        }
        return null;
      })}

      {/* Lignes blanches du terrain - Améliorées */}
      {/* Ligne centrale */}
      <mesh position={[0, -0.68, 0]}>
        <boxGeometry args={[0.15, 0.04, 30]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Lignes de touche */}
      <mesh position={[-25, -0.68, 0]}>
        <boxGeometry args={[0.15, 0.04, 30]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[25, -0.68, 0]}>
        <boxGeometry args={[0.15, 0.04, 30]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Lignes de but */}
      <mesh position={[0, -0.68, -15]}>
        <boxGeometry args={[50, 0.04, 0.15]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[0, -0.68, 15]}>
        <boxGeometry args={[50, 0.04, 0.15]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Surface de réparation gauche */}
      <mesh position={[-18.5, -0.68, 0]}>
        <boxGeometry args={[0.15, 0.04, 16.5]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[-22.75, -0.68, -8.25]}>
        <boxGeometry args={[8.5, 0.04, 0.15]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[-22.75, -0.68, 8.25]}>
        <boxGeometry args={[8.5, 0.04, 0.15]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Surface de réparation droite */}
      <mesh position={[18.5, -0.68, 0]}>
        <boxGeometry args={[0.15, 0.04, 16.5]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[22.75, -0.68, -8.25]}>
        <boxGeometry args={[8.5, 0.04, 0.15]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[22.75, -0.68, 8.25]}>
        <boxGeometry args={[8.5, 0.04, 0.15]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Cercle central */}
      <mesh position={[0, -0.66, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[8.5, 9, 64]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Point central */}
      <mesh position={[0, -0.66, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.3, 16]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Points de penalty */}
      <mesh position={[-16.5, -0.66, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.2, 16]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[16.5, -0.66, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.2, 16]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Arcs de cercle surface de réparation */}
      <mesh position={[-16.5, -0.66, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[8.5, 8.7, 32, 1, Math.PI / 2, Math.PI]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>
      <mesh position={[16.5, -0.66, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[8.5, 8.7, 32, 1, -Math.PI / 2, Math.PI]} />
        <meshBasicMaterial color="#FFFFFF" />
      </mesh>

      {/* Buts - ORIENTÉS CORRECTEMENT (perpendiculaires) */}
      <SoccerGoal position={[-25, -1, 0]} isLeft={true} />
      <SoccerGoal position={[25, -1, 0]} isLeft={false} />

      {/* Arbres - Déplacés derrière les gradins */}
      <VoxelTree position={[-45, -1, -25]} scale={1.2} />
      <VoxelTree position={[45, -1, -25]} scale={1.3} />
      <VoxelTree position={[-50, -1, 0]} scale={1} />
      <VoxelTree position={[50, -1, 0]} scale={1.1} />
      <VoxelTree position={[-45, -1, 25]} scale={0.9} />
      <VoxelTree position={[45, -1, 25]} scale={1} />
      <VoxelTree position={[0, -1, -40]} scale={1.4} />
      <VoxelTree position={[-30, -1, -35]} scale={1.1} />
      <VoxelTree position={[30, -1, -35]} scale={1.2} />

      {/* Nuages - Plus haut pour le stade */}
      <Cloud position={[-20, 15, -20]} />
      <Cloud position={[20, 18, -15]} />
      <Cloud position={[0, 20, -35]} />
      <Cloud position={[-35, 16, 10]} />
      <Cloud position={[35, 14, 15]} />

      {/* Touffes d'herbe - uniquement sur le terrain */}
      {Array.from({ length: 20 }).map((_, i) => {
        const x = (Math.random() - 0.5) * 40;
        const z = (Math.random() - 0.5) * 25;
        // Éviter le centre du terrain et les buts
        if ((Math.abs(x) > 8 || Math.abs(z) > 3) && Math.abs(x) < 22) {
          return (
            <mesh key={i} position={[x, -0.7, z]}>
              <boxGeometry args={[0.2, 0.15, 0.2]} />
              <meshStandardMaterial color="#66BB6A" />
            </mesh>
          );
        }
        return null;
      })}

      {/* Ballon au centre */}
      <SoccerBall position={[0, -0.6, 0]} />

      {/* Fleurs - autour du terrain */}
      {[
        { pos: [-15, -0.8, 10], color: '#FF69B4' },
        { pos: [15, -0.8, 10], color: '#FFD700' },
        { pos: [-15, -0.8, -10], color: '#FF6347' },
        { pos: [15, -0.8, -10], color: '#9370DB' },
        { pos: [-20, -0.8, 0], color: '#FF1493' },
        { pos: [20, -0.8, 0], color: '#00CED1' },
        { pos: [0, -0.8, -12], color: '#FF4500' },
        { pos: [0, -0.8, 12], color: '#32CD32' },
      ].map((flower, i) => (
        <group key={i} position={flower.pos as [number, number, number]}>
          <mesh position={[0, 0.1, 0]}>
            <boxGeometry args={[0.04, 0.2, 0.04]} />
            <meshStandardMaterial color="#2E7D32" />
          </mesh>
          <mesh position={[0, 0.25, 0]}>
            <boxGeometry args={[0.15, 0.15, 0.15]} />
            <meshStandardMaterial color={flower.color} />
          </mesh>
        </group>
      ))}
    </>
  );
}
