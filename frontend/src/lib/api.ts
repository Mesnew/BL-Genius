// Utilise le proxy Next.js en dev, ou l'URL directe en production
const API_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

// Récupérer le token depuis localStorage (côté client uniquement)
function getToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('bl_genius_token');
  }
  return null;
}

export interface Task {
  id: string;
  status: 'uploaded' | 'processing' | 'completed' | 'error';
  input_path: string;
  output_path: string | null;
  progress: number;
  error?: string;
  analysis_result?: {
    total_frames: number;
    total_players: number;
    possession_team1: number;
    possession_team2: number;
  };
}

export async function uploadVideo(file: File): Promise<{ task_id: string; status: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}/upload`, {
    method: 'POST',
    headers,
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Erreur lors de l\'upload');
  }

  return response.json();
}

export async function analyzeVideo(taskId: string): Promise<Task> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}/analyze/${taskId}`, {
    method: 'POST',
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Erreur lors de l\'analyse');
  }

  return response.json();
}

export async function getTaskStatus(taskId: string): Promise<Task> {
  const token = getToken();
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}/status/${taskId}`, {
    headers,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Erreur lors de la récupération du statut');
  }

  return response.json();
}

export function getVideoDownloadUrl(taskId: string): string {
  const token = getToken();
  if (token) {
    return `${API_URL}/download/${taskId}?token=${encodeURIComponent(token)}`;
  }
  return `${API_URL}/download/${taskId}`;
}

export async function downloadYouTube(url: string): Promise<{ task_id: string; status: string; title: string }> {
  const token = getToken();
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}/youtube`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Erreur lors du téléchargement YouTube');
  }

  return response.json();
}
