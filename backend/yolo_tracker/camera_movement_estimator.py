import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class CameraMovementEstimator:
    """
    Estime le mouvement de la caméra entre les frames.
    Utilise l'optical flow pour compenser les mouvements de caméra.
    """

    def __init__(self, feature_params: Optional[Dict] = None, lk_params: Optional[Dict] = None):
        """
        Args:
            feature_params: Paramètres pour la détection de features
            lk_params: Paramètres pour Lucas-Kanade optical flow
        """
        self.feature_params = feature_params or {
            "maxCorners": 100,
            "qualityLevel": 0.3,
            "minDistance": 7,
            "blockSize": 7
        }

        self.lk_params = lk_params or {
            "winSize": (15, 15),
            "maxLevel": 2,
            "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        }

        self.prev_gray = None
        self.camera_movements = []

    def estimate_movement(self, frame: np.ndarray) -> Tuple[float, float]:
        """
        Estime le mouvement de la caméra par rapport à la frame précédente.

        Args:
            frame: Frame actuelle (BGR)

        Returns:
            (dx, dy) mouvement estimé de la caméra
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = gray
            return (0.0, 0.0)

        # Détecter les coins
        prev_corners = cv2.goodFeaturesToTrack(self.prev_gray, **self.feature_params)

        if prev_corners is None:
            self.prev_gray = gray
            return (0.0, 0.0)

        # Calculer l'optical flow
        next_corners, status, error = cv2.calcOpticalFlowPyrLK(
            self.prev_gray, gray, prev_corners, None, **self.lk_params
        )

        if next_corners is None:
            self.prev_gray = gray
            return (0.0, 0.0)

        # Filtrer les points valides
        good_prev = prev_corners[status == 1]
        good_next = next_corners[status == 1]

        if len(good_prev) < 5:
            self.prev_gray = gray
            return (0.0, 0.0)

        # Calculer le mouvement moyen
        movements = good_next - good_prev
        median_movement = np.median(movements, axis=0)

        self.prev_gray = gray

        return (float(median_movement[0]), float(median_movement[1]))

    def process_video(self, frames: List[np.ndarray]) -> List[Tuple[float, float]]:
        """
        Estime le mouvement de caméra pour toute la vidéo.

        Args:
            frames: Liste des frames

        Returns:
            Liste des mouvements (dx, dy) pour chaque frame
        """
        print("📹 Estimation du mouvement de caméra...")

        self.camera_movements = []
        self.prev_gray = None

        for i, frame in enumerate(frames):
            movement = self.estimate_movement(frame)
            self.camera_movements.append(movement)

            if i % 100 == 0:
                print(f"   Frame {i}/{len(frames)}")

        print(f"✅ Mouvement estimé pour {len(self.camera_movements)} frames")
        return self.camera_movements

    def adjust_positions(self, tracks: Dict, camera_movements: List[Tuple[float, float]]) -> Dict:
        """
        Ajuste les positions des objets en compensant le mouvement de caméra.

        Args:
            tracks: Tracks des objets
            camera_movements: Liste des mouvements de caméra

        Returns:
            Tracks avec positions ajustées
        """
        print("🔄 Compensation du mouvement de caméra...")

        # Cumuler les mouvements pour avoir la position relative à la première frame
        cumulative_movement = [(0.0, 0.0)]
        cum_x, cum_y = 0.0, 0.0

        for dx, dy in camera_movements[1:]:
            cum_x += dx
            cum_y += dy
            cumulative_movement.append((cum_x, cum_y))

        # Ajuster les positions des joueurs
        for frame_num in range(len(tracks["players"])):
            offset_x, offset_y = cumulative_movement[frame_num]

            for track_id, player in tracks["players"][frame_num].items():
                bbox = player["bbox"]
                player["adjusted_bbox"] = [
                    bbox[0] + offset_x,
                    bbox[1] + offset_y,
                    bbox[2] + offset_x,
                    bbox[3] + offset_y
                ]

        return tracks
