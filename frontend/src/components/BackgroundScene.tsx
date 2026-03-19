'use client';

import { useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import * as THREE from 'three';

// Particules flottantes style "poussière de stade"
function FloatingParticles({ count = 50 }: { count?: number }) {
  const meshRef = useRef<THREE.Points>(null);

  const particles = useMemo(() => {
    const positions = new Float32Array(count * 3);
    const colors = new Float32Array(count * 3);

    for (let i = 0; i < count; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 1] = (Math.random() - 0.5) * 20;
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10;

      // Couleurs vert/bleu/blanc discrets
      const colorChoice = Math.random();
      if (colorChoice < 0.4) {
        // Vert foot
        colors[i * 3] = 0.3;
        colors[i * 3 + 1] = 0.7;
        colors[i * 3 + 2] = 0.4;
      } else if (colorChoice < 0.7) {
        // Bleu ciel
        colors[i * 3] = 0.5;
        colors[i * 3 + 1] = 0.7;
        colors[i * 3 + 2] = 0.9;
      } else {
        // Blanc
        colors[i * 3] = 1;
        colors[i * 3 + 1] = 1;
        colors[i * 3 + 2] = 1;
      }
    }

    return { positions, colors };
  }, [count]);

  useFrame((state) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = state.clock.elapsedTime * 0.02;
      meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.05;
    }
  });

  return (
    <points ref={meshRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={particles.positions.length / 3}
          array={particles.positions}
          itemSize={3}
        />
        <bufferAttribute
          attach="attributes-color"
          count={particles.colors.length / 3}
          array={particles.colors}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.05}
        vertexColors
        transparent
        opacity={0.6}
        sizeAttenuation
      />
    </points>
  );
}

// Ballons flottants subtils
function FloatingBalls({ count = 5 }: { count?: number }) {
  const groupRef = useRef<THREE.Group>(null);

  const balls = useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      id: i,
      position: [
        (Math.random() - 0.5) * 15,
        (Math.random() - 0.5) * 10,
        (Math.random() - 0.5) * 5 - 3,
      ] as [number, number, number],
      scale: 0.1 + Math.random() * 0.15,
      speed: 0.2 + Math.random() * 0.3,
      offset: Math.random() * Math.PI * 2,
    }));
  }, [count]);

  useFrame((state) => {
    if (groupRef.current) {
      balls.forEach((ball, i) => {
        const mesh = groupRef.current?.children[i];
        if (mesh) {
          mesh.position.y += Math.sin(state.clock.elapsedTime * ball.speed + ball.offset) * 0.002;
          mesh.rotation.x += 0.002;
          mesh.rotation.y += 0.003;
        }
      });
    }
  });

  return (
    <group ref={groupRef}>
      {balls.map((ball) => (
        <group key={ball.id} position={ball.position} scale={ball.scale}>
          {/* Ballon blanc */}
          <mesh>
            <boxGeometry args={[1, 1, 1]} />
            <meshStandardMaterial color="#FFFFFF" transparent opacity={0.15} />
          </mesh>
          {/* Motif noir */}
          <mesh position={[0, 0, 0.51]}>
            <boxGeometry args={[0.3, 0.3, 0.02]} />
            <meshBasicMaterial color="#000000" transparent opacity={0.2} />
          </mesh>
          <mesh position={[0.51, 0, 0]}>
            <boxGeometry args={[0.02, 0.3, 0.3]} />
            <meshBasicMaterial color="#000000" transparent opacity={0.2} />
          </mesh>
        </group>
      ))}
    </group>
  );
}

// Terrain stylisé en bas
function StylizedField() {
  return (
    <group position={[0, -5, -5]} rotation={[-Math.PI / 6, 0, 0]}>
      {/* Lignes de terrain */}
      {Array.from({ length: 5 }).map((_, i) => (
        <mesh key={i} position={[0, i * 0.5 - 1, 0]}>
          <boxGeometry args={[20, 0.02, 0.1]} />
          <meshBasicMaterial color="#4CAF50" transparent opacity={0.3} />
        </mesh>
      ))}
      {/* Lignes verticales */}
      {Array.from({ length: 3 }).map((_, i) => (
        <mesh key={`v-${i}`} position={[(i - 1) * 8, 0, 0]}>
          <boxGeometry args={[0.1, 2, 0.1]} />
          <meshBasicMaterial color="#4CAF50" transparent opacity={0.3} />
        </mesh>
      ))}
    </group>
  );
}

// Éclairage doux
function SoftLighting() {
  return (
    <>
      <ambientLight intensity={0.3} />
      <directionalLight position={[5, 10, 5]} intensity={0.4} />
      <pointLight position={[-5, 5, -5]} intensity={0.2} color="#4CAF50" />
      <pointLight position={[5, -5, 5]} intensity={0.2} color="#2196F3" />
    </>
  );
}

export default function BackgroundScene() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas
        camera={{ position: [0, 0, 8], fov: 60 }}
        gl={{ antialias: true, alpha: true }}
        dpr={[1, 1.5]}
      >
        <color attach="background" args={['#0f172a']} />
        <SoftLighting />
        <FloatingParticles count={60} />
        <FloatingBalls count={6} />
        <StylizedField />
      </Canvas>
    </div>
  );
}
