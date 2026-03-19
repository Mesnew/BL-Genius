import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Output standalone pour Docker
  output: 'standalone',

  // Configuration des images
  images: {
    unoptimized: true,
  },

  // Turbopack root for Docker volume mounts
  turbopack: {
    root: '/app',
  },

  // Configuration CORS pour l'API
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://backend:8000/:path*',
      },
    ];
  },

  // Variables d'environnement publiques
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
};

export default nextConfig;
