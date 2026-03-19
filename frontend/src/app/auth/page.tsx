'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import PageTransition from '@/components/PageTransition';

const API_URL = '/api';

export default function AuthPage() {
  const router = useRouter();
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const { login, isAuthenticated } = useAuth();

  useEffect(() => {
    setMounted(true);
  }, []);

  // Rediriger vers la page 3D si déjà authentifié
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/home');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setIsLoading(true);

    console.log(`Tentative de ${isLogin ? 'connexion' : 'inscription'}...`);

    try {
      const endpoint = isLogin ? '/auth/login' : '/auth/register';
      const body = isLogin
        ? { username, password }
        : { email, username, password };

      console.log(`Envoi à ${API_URL}${endpoint}`, body);

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(body),
      });

      const data = await response.json();
      console.log('Réponse:', data);

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error(data.error || 'Trop de tentatives. Veuillez réessayer plus tard.');
        }
        throw new Error(data.detail || 'Erreur lors de l\'authentification');
      }

      // Afficher message de succès pour l'inscription
      if (!isLogin) {
        setSuccess('✅ Inscription réussie ! Connexion en cours...');
      }

      // Récupérer les infos utilisateur
      const userResponse = await fetch(`${API_URL}/auth/me`, {
        headers: {
          'Authorization': `Bearer ${data.access_token}`,
        },
      });

      if (userResponse.ok) {
        const userData = await userResponse.json();
        console.log('Utilisateur connecté:', userData);
        login(data.access_token, userData);
        // Rediriger vers la page 3D de sélection après connexion réussie
        router.push('/home');
      } else {
        throw new Error('Erreur lors de la récupération des informations utilisateur');
      }
    } catch (err) {
      console.error('Erreur:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setSuccess('');
    // Réinitialiser les champs
    setEmail('');
    setUsername('');
    setPassword('');
  };

  return (
    <PageTransition>
      <div className={`min-h-screen flex items-center justify-center px-4 transition-opacity duration-500 ${mounted ? 'opacity-100' : 'opacity-0'}`}>
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <span className="text-6xl">⚽</span>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-green-400 to-cyan-400 bg-clip-text text-transparent mt-4">
            BL Genius
          </h1>
          <p className="text-gray-400 mt-2">Analyse de matchs de football par IA</p>
        </div>

        {/* Formulaire */}
        <div className="bg-white/5 rounded-2xl p-8 border border-white/10">
          <h2 className="text-2xl font-bold text-white mb-6 text-center">
            {isLogin ? 'Connexion' : 'Inscription'}
          </h2>

          {error && (
            <div className="mb-4 p-3 bg-red-500/20 border border-red-500 rounded-lg">
              <p className="text-red-400 text-sm">❌ {error}</p>
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-500/20 border border-green-500 rounded-lg">
              <p className="text-green-400 text-sm">{success}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-1">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required={!isLogin}
                  className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-green-400"
                  placeholder="votre@email.com"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Nom d'utilisateur
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-green-400"
                placeholder="votre_nom"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1">
                Mot de passe
              </label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-green-400"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-green-400 to-cyan-400 text-gray-900 font-bold py-3 px-6 rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
                  Chargement...
                </span>
              ) : (
                isLogin ? 'Se connecter' : 'S\'inscrire'
              )}
            </button>
          </form>

          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={toggleMode}
              className="text-gray-400 hover:text-white text-sm underline"
            >
              {isLogin
                ? "Pas de compte ? S'inscrire"
                : 'Déjà un compte ? Se connecter'}
            </button>
          </div>
        </div>

        {/* Features */}
        <div className="mt-8 grid grid-cols-3 gap-4 text-center">
          <div className="bg-black/20 backdrop-blur-sm rounded-lg p-3">
            <div className="text-2xl mb-1">🏃</div>
            <div className="text-gray-300 text-xs font-medium">Tracking IA</div>
          </div>
          <div className="bg-black/20 backdrop-blur-sm rounded-lg p-3">
            <div className="text-2xl mb-1">📊</div>
            <div className="text-gray-300 text-xs font-medium">Statistiques</div>
          </div>
          <div className="bg-black/20 backdrop-blur-sm rounded-lg p-3">
            <div className="text-2xl mb-1">⚡</div>
            <div className="text-gray-300 text-xs font-medium">Rapide</div>
          </div>
        </div>
      </div>
    </div>
  </PageTransition>
  );
}
