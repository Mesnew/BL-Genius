'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { uploadVideo, analyzeVideo, getTaskStatus, downloadYouTube, Task } from '@/lib/api';

interface UploadVideoProps {
  onUploadComplete?: (taskId: string) => void;
  onVideoAnalyzed?: (taskId: string) => void;
}

export default function UploadVideo({ onUploadComplete, onVideoAnalyzed }: UploadVideoProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [task, setTask] = useState<Task | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [isDownloadingYoutube, setIsDownloadingYoutube] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Nettoyer l'intervalle quand le composant est démonté
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFile(files[0]);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFile(files[0]);
    }
  }, []);

  const pollStatus = useCallback(async (taskId: string) => {
    // Nettoyer l'ancien intervalle s'il existe
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    let progressValue = 50;

    // Vérifier immédiatement le statut
    try {
      const initialStatus = await getTaskStatus(taskId);
      setTask(initialStatus);

      if (initialStatus.status === 'completed') {
        setProgress(100);
        setIsUploading(false);
        onVideoAnalyzed?.(taskId);
        return;
      } else if (initialStatus.status === 'error') {
        setError(initialStatus.error || 'Erreur lors de l\'analyse');
        setIsUploading(false);
        return;
      }
    } catch (err) {
      console.error('Erreur polling initial:', err);
    }

    // Polling régulier
    intervalRef.current = setInterval(async () => {
      try {
        const status = await getTaskStatus(taskId);
        setTask(status);

        if (status.status === 'completed') {
          setProgress(100);
          setIsUploading(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
          onVideoAnalyzed?.(taskId);
        } else if (status.status === 'error') {
          setError(status.error || 'Erreur lors de l\'analyse');
          setIsUploading(false);
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        } else if (status.status === 'processing') {
          // Progression animée pendant le traitement
          progressValue = Math.min(progressValue + 2, 95);
          setProgress(progressValue);
        }
      } catch (err) {
        console.error('Erreur polling:', err);
      }
    }, 1000);
  }, [onVideoAnalyzed]);

  const handleFile = async (file: File) => {
    // Vérifier le format
    const validFormats = ['.mp4', '.avi', '.mov', '.mkv'];
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!validFormats.includes(ext)) {
      setError('Format non supporté. Utilisez MP4, AVI, MOV ou MKV');
      return;
    }

    setError(null);
    setIsUploading(true);
    setProgress(10);

    try {
      // Upload
      console.log('Début upload...');
      const uploadResult = await uploadVideo(file);
      console.log('Upload réussi:', uploadResult);
      setProgress(30);

      const newTask: Task = {
        id: uploadResult.task_id,
        status: 'uploaded',
        input_path: '',
        output_path: null,
        progress: 30,
      };

      setTask(newTask);
      onUploadComplete?.(uploadResult.task_id);

      // Lancer l'analyse
      console.log('Lancement analyse...');
      setProgress(50);
      const analyzeResult = await analyzeVideo(uploadResult.task_id);
      console.log('Analyse lancée:', analyzeResult);

      // Démarrer le polling immédiatement
      pollStatus(uploadResult.task_id);

    } catch (err) {
      console.error('Erreur upload/analyse:', err);
      setError(err instanceof Error ? err.message : 'Erreur inconnue');
      setIsUploading(false);
    }
  };

  const reset = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setTask(null);
    setError(null);
    setProgress(0);
    setIsUploading(false);
    setYoutubeUrl('');
    setIsDownloadingYoutube(false);
  };

  const handleYoutubeDownload = async () => {
    if (!youtubeUrl.trim()) {
      setError('Veuillez entrer une URL YouTube');
      return;
    }

    // Vérifier que c'est une URL YouTube valide
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
    if (!youtubeRegex.test(youtubeUrl)) {
      setError('URL YouTube invalide');
      return;
    }

    setError(null);
    setIsDownloadingYoutube(true);
    setProgress(10);

    try {
      // Télécharger depuis YouTube
      console.log('Téléchargement YouTube...');
      const result = await downloadYouTube(youtubeUrl);
      console.log('YouTube téléchargé:', result);
      setProgress(30);

      const newTask: Task = {
        id: result.task_id,
        status: 'uploaded',
        input_path: '',
        output_path: null,
        progress: 30,
      };

      setTask(newTask);
      onUploadComplete?.(result.task_id);

      // Lancer l'analyse
      console.log('Lancement analyse YouTube...');
      setProgress(50);
      await analyzeVideo(result.task_id);

      // Polling du statut
      pollStatus(result.task_id);

    } catch (err) {
      console.error('Erreur YouTube:', err);
      setError(err instanceof Error ? err.message : 'Erreur lors du téléchargement YouTube');
      setIsDownloadingYoutube(false);
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto relative z-10">
      {/* Zone d'upload */}
      {!task && (
        <div className="space-y-6">
          {/* Upload fichier */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={`
              relative border-2 border-dashed rounded-2xl p-12 text-center
              transition-all duration-300 cursor-pointer backdrop-blur-sm
              ${isDragging
                ? 'border-green-400 bg-green-400/20 shadow-lg shadow-green-400/20'
                : 'border-white/30 bg-black/20 hover:border-green-400/70 hover:bg-black/30'
              }
            `}
          >
            <input
              type="file"
              accept=".mp4,.avi,.mov,.mkv"
              onChange={handleFileInput}
              className="hidden"
              id="file-input"
            />

            <label htmlFor="file-input" className="cursor-pointer block">
              <div className="text-6xl mb-4 animate-bounce">📹</div>
              <h3 className="text-2xl font-bold mb-2 text-white">
                {isDragging ? 'Déposez la vidéo ici' : 'Glissez votre vidéo ici'}
              </h3>
              <p className="text-gray-300 mb-4">ou</p>

              <button className="
                bg-gradient-to-r from-green-400 to-cyan-400
                text-gray-900 font-bold py-3 px-8 rounded-full
                hover:scale-105 transition-transform shadow-lg
              ">
                Sélectionner un fichier
              </button>

              <p className="mt-4 text-sm text-gray-400">
                Formats supportés: MP4, AVI, MOV, MKV
              </p>
            </label>
          </div>

          {/* Séparateur */}
          <div className="flex items-center gap-4">
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent"></div>
            <span className="text-gray-400 font-medium">ou</span>
            <div className="flex-1 h-px bg-gradient-to-r from-transparent via-white/30 to-transparent"></div>
          </div>

          {/* YouTube URL */}
          <div className="bg-black/20 backdrop-blur-sm rounded-2xl p-8 border border-white/20">
            <div className="text-center mb-6">
              <div className="text-5xl mb-3">▶️</div>
              <h3 className="text-xl font-bold text-white">URL YouTube</h3>
              <p className="text-gray-300 text-sm mt-1">
                Téléchargez une vidéo directement depuis YouTube
              </p>
            </div>

            <div className="flex gap-3">
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="https://www.youtube.com/watch?v=..."
                className="flex-1 bg-white/10 border border-white/20 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-green-400 backdrop-blur-sm"
                disabled={isDownloadingYoutube}
              />
              <button
                onClick={handleYoutubeDownload}
                disabled={isDownloadingYoutube || !youtubeUrl.trim()}
                className="bg-gradient-to-r from-red-500 to-red-600 text-white font-bold py-3 px-6 rounded-lg hover:scale-105 transition-transform disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              >
                {isDownloadingYoutube ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Téléchargement...
                  </span>
                ) : (
                  'Télécharger'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Erreur */}
      {error && (
        <div className="mt-6 p-4 bg-red-500/20 border border-red-500 rounded-xl backdrop-blur-sm">
          <p className="text-red-400">❌ {error}</p>
          <button
            onClick={reset}
            className="mt-2 text-sm text-red-400 hover:text-red-300 underline"
          >
            Réessayer
          </button>
        </div>
      )}

      {/* Progression */}
      {task && (
        <div className="mt-6 p-6 bg-black/20 backdrop-blur-sm rounded-xl border border-white/20">
          <div className="flex justify-between items-center mb-4">
            <div>
              <h4 className="font-bold text-lg text-white">
                {task.status === 'uploaded' && '📤 Upload terminé'}
                {task.status === 'processing' && '🔬 Analyse en cours...'}
                {task.status === 'completed' && '✅ Analyse terminée!'}
                {task.status === 'error' && '❌ Erreur'}
              </h4>
              <p className="text-sm text-gray-300">
                {task.status === 'uploaded' && 'Préparation de l\'analyse...'}
                {task.status === 'processing' && 'YOLO détecte les joueurs et le ballon...'}
                {task.status === 'completed' && 'Votre vidéo est prête'}
              </p>
            </div>

            <span className={`
              px-3 py-1 rounded-full text-sm font-bold
              ${task.status === 'uploaded' && 'bg-yellow-400 text-gray-900'}
              ${task.status === 'processing' && 'bg-blue-400 text-gray-900'}
              ${task.status === 'completed' && 'bg-green-400 text-gray-900'}
              ${task.status === 'error' && 'bg-red-400 text-gray-900'}
            `}>
              {task.status}
            </span>
          </div>

          {/* Barre de progression */}
          <div className="w-full h-3 bg-gray-700/50 rounded-full overflow-hidden backdrop-blur-sm">
            <div
              className="h-full bg-gradient-to-r from-green-400 to-cyan-400 transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>

          <div className="flex justify-between mt-2 text-sm text-gray-300">
            <span>{progress}%</span>
            {(task.status === 'processing' || task.status === 'uploaded') && (
              <span className="flex items-center gap-2">
                <span className="w-4 h-4 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
                Traitement...
              </span>
            )}
          </div>

          {/* Résultats si terminé */}
          {task.status === 'completed' && task.analysis_result && (
            <div className="mt-4 p-4 bg-green-500/10 border border-green-500/30 rounded-lg backdrop-blur-sm">
              <h5 className="font-bold text-green-400 mb-2">📊 Résultats de l'analyse</h5>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-300">Frames analysées:</span>
                  <span className="text-white ml-2">{task.analysis_result.total_frames}</span>
                </div>
                <div>
                  <span className="text-gray-300">Joueurs détectés:</span>
                  <span className="text-white ml-2">{task.analysis_result.total_players}</span>
                </div>
                <div>
                  <span className="text-gray-300">Possession Équipe 1:</span>
                  <span className="text-white ml-2">{task.analysis_result.possession_team1?.toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-gray-300">Possession Équipe 2:</span>
                  <span className="text-white ml-2">{task.analysis_result.possession_team2?.toFixed(1)}%</span>
                </div>
              </div>
            </div>
          )}

          {/* Bouton reset */}
          {task.status === 'completed' && (
            <button
              onClick={reset}
              className="mt-4 text-sm text-gray-300 hover:text-white underline"
            >
              Analyser une autre vidéo
            </button>
          )}
        </div>
      )}
    </div>
  );
}
