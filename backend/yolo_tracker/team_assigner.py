import cv2
import numpy as np
from sklearn.cluster import KMeans
from typing import Dict, List, Tuple, Optional
import pickle
from pathlib import Path


class TeamAssigner:
    """
    Assigne les joueurs aux équipes en utilisant K-Means sur les couleurs des maillots.
    Basé sur la méthode du tutoriel de football analysis.
    """

    def __init__(self, n_teams: int = 2):
        """
        Args:
            n_teams: Nombre d'équipes (par défaut 2)
        """
        self.n_teams = n_teams
        self.kmeans: Optional[KMeans] = None
        self.team_colors: Dict[int, Tuple[int, int, int]] = {}
        self.is_fitted = False

    def extract_jersey_color(self, frame: np.ndarray, bbox: List[float]) -> np.ndarray:
        """
        Extrait la couleur du maillot d'un joueur à partir de sa bounding box.
        Prend la partie supérieure du joueur (torse) pour éviter les jambes.

        Args:
            frame: Image complète
            bbox: [x1, y1, x2, y2] bounding box

        Returns:
            Couleur moyenne du maillot (RGB)
        """
        x1, y1, x2, y2 = map(int, bbox)

        # Prendre seulement la partie supérieure (torse) - environ 40% du haut
        # et centré horizontalement pour éviter les bras
        height = y2 - y1
        width = x2 - x1

        # Région du torse (centre, partie supérieure)
        y_start = y1 + int(height * 0.1)  # Commencer un peu plus bas que le haut
        y_end = y1 + int(height * 0.5)    # Jusqu'à la moitié
        x_start = x1 + int(width * 0.2)   # Éviter les bras (20% de marge)
        x_end = x2 - int(width * 0.2)

        # S'assurer que les coordonnées sont valides
        y_start = max(0, y_start)
        y_end = min(frame.shape[0], y_end)
        x_start = max(0, x_start)
        x_end = min(frame.shape[1], x_end)

        if y_start >= y_end or x_start >= x_end:
            return np.array([0, 0, 0])

        # Extraire la région du torse
        torso = frame[y_start:y_end, x_start:x_end]

        if torso.size == 0:
            return np.array([0, 0, 0])

        # Convertir en RGB et calculer la couleur moyenne
        torso_rgb = cv2.cvtColor(torso, cv2.COLOR_BGR2RGB)
        mean_color = np.mean(torso_rgb, axis=(0, 1))

        return mean_color

    def fit(self, frames: List[np.ndarray], tracks: Dict) -> None:
        """
        Entraîne le modèle K-Means sur les couleurs des maillots des joueurs.
        Utilise les premières frames pour déterminer les couleurs des équipes.

        Args:
            frames: Liste des frames de la vidéo
            tracks: Dictionnaire des tracks (doit contenir 'players')
        """
        print("🎨 Analyse des couleurs des équipes...")

        colors = []

        # Utiliser les premières frames (jusqu'à 20) pour collecter les échantillons
        n_samples = min(20, len(frames))
        sample_indices = np.linspace(0, len(frames) - 1, n_samples, dtype=int)

        for frame_num in sample_indices:
            frame = frames[frame_num]
            player_dict = tracks["players"][frame_num]

            for track_id, player in player_dict.items():
                bbox = player["bbox"]
                color = self.extract_jersey_color(frame, bbox)

                # Ignorer les couleurs trop sombres (probablement ombres)
                if np.mean(color) > 30:
                    colors.append(color)

        if len(colors) < self.n_teams * 2:
            print("⚠️ Pas assez d'échantillons pour le clustering")
            self.is_fitted = False
            return

        # Appliquer K-Means
        colors_array = np.array(colors)
        self.kmeans = KMeans(n_clusters=self.n_teams, random_state=42, n_init=10)
        self.kmeans.fit(colors_array)

        # Stocker les couleurs des équipes (centres des clusters)
        for i in range(self.n_teams):
            center = self.kmeans.cluster_centers_[i]
            self.team_colors[i] = tuple(map(int, center))

        self.is_fitted = True
        print(f"✅ Équipes identifiées: {len(self.team_colors)} équipes")
        for team_id, color in self.team_colors.items():
            print(f"   Équipe {team_id}: RGB{color}")

    def get_player_team(self, frame: np.ndarray, bbox: List[float]) -> Tuple[int, float]:
        """
        Détermine l'équipe d'un joueur à partir de la couleur de son maillot.

        Args:
            frame: Image complète
            bbox: Bounding box du joueur

        Returns:
            (team_id, confidence)
        """
        if not self.is_fitted or self.kmeans is None:
            return 0, 0.0

        color = self.extract_jersey_color(frame, bbox)
        color_reshaped = color.reshape(1, -1)

        # Prédire l'équipe
        team_id = self.kmeans.predict(color_reshaped)[0]

        # Calculer la confiance (distance inverse au centre)
        distances = self.kmeans.transform(color_reshaped)[0]
        min_distance = distances[team_id]
        max_distance = np.max(distances) + 1e-6
        confidence = 1 - (min_distance / max_distance)

        return int(team_id), float(confidence)

    def assign_teams_to_tracks(self, frames: List[np.ndarray], tracks: Dict) -> Dict:
        """
        Assigne les équipes à tous les joueurs dans les tracks.

        Args:
            frames: Liste des frames
            tracks: Tracks des objets

        Returns:
            Tracks mis à jour avec l'information d'équipe
        """
        if not self.is_fitted:
            print("⚠️ TeamAssigner non entraîné, entraînement automatique...")
            self.fit(frames, tracks)

        if not self.is_fitted:
            print("❌ Impossible d'assigner les équipes")
            return tracks

        print("🏃 Assignation des équipes aux joueurs...")

        for frame_num, frame in enumerate(frames):
            player_dict = tracks["players"][frame_num]

            for track_id, player in player_dict.items():
                bbox = player["bbox"]
                team_id, confidence = self.get_player_team(frame, bbox)

                player["team"] = team_id
                player["team_confidence"] = confidence
                player["team_color"] = self.team_colors.get(team_id, (128, 128, 128))

        return tracks

    def save(self, path: str) -> None:
        """Sauvegarde le modèle K-Means entraîné"""
        if self.is_fitted and self.kmeans is not None:
            data = {
                "kmeans": self.kmeans,
                "team_colors": self.team_colors,
                "n_teams": self.n_teams
            }
            with open(path, "wb") as f:
                pickle.dump(data, f)
            print(f"💾 Modèle sauvegardé: {path}")

    def load(self, path: str) -> bool:
        """Charge un modèle K-Means entraîné"""
        try:
            with open(path, "rb") as f:
                data = pickle.load(f)
            self.kmeans = data["kmeans"]
            self.team_colors = data["team_colors"]
            self.n_teams = data["n_teams"]
            self.is_fitted = True
            print(f"✅ Modèle chargé: {path}")
            return True
        except Exception as e:
            print(f"⚠️ Erreur chargement modèle: {e}")
            return False
