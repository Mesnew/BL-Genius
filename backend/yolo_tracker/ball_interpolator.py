import numpy as np
from typing import Dict, List, Optional, Tuple
from scipy.interpolate import interp1d


class BallInterpolator:
    """
    Interpole la position du ballon quand il n'est pas détecté.
    Utilise l'interpolation linéaire entre les frames où le ballon est visible.
    """

    def __init__(self, max_gap: int = 10):
        """
        Args:
            max_gap: Nombre maximum de frames consécutives à interpoler
        """
        self.max_gap = max_gap

    def interpolate_ball_positions(self, tracks: Dict) -> Dict:
        """
        Interpole les positions du ballon manquantes.

        Args:
            tracks: Dictionnaire des tracks avec 'ball' key

        Returns:
            Tracks avec positions du ballon interpolées
        """
        ball_tracks = tracks["ball"]
        n_frames = len(ball_tracks)

        # Collecter les positions détectées
        detected_frames = []
        positions = []

        for frame_num, ball_dict in enumerate(ball_tracks):
            if ball_dict and 1 in ball_dict:  # Le ballon a track_id=1
                bbox = ball_dict[1]["bbox"]
                # Centre de la bounding box
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = (bbox[1] + bbox[3]) / 2
                detected_frames.append(frame_num)
                positions.append([center_x, center_y, bbox[0], bbox[1], bbox[2], bbox[3]])

        if len(detected_frames) < 2:
            print("⚠️ Pas assez de détections du ballon pour interpolation")
            return tracks

        print(f"🎯 Interpolation du ballon: {len(detected_frames)} détections sur {n_frames} frames")

        # Interpoler pour les gaps plus petits que max_gap
        for i in range(len(detected_frames) - 1):
            start_frame = detected_frames[i]
            end_frame = detected_frames[i + 1]
            gap = end_frame - start_frame

            if gap > 1 and gap <= self.max_gap:
                # Interpoler les positions entre start_frame et end_frame
                start_pos = positions[i]
                end_pos = positions[i + 1]

                for frame_num in range(start_frame + 1, end_frame):
                    # Interpolation linéaire
                    alpha = (frame_num - start_frame) / gap
                    interp_pos = [
                        start_pos[j] + alpha * (end_pos[j] - start_pos[j])
                        for j in range(6)
                    ]

                    # Créer la bbox interpolée
                    bbox = [
                        interp_pos[2],  # x1
                        interp_pos[3],  # y1
                        interp_pos[4],  # x2
                        interp_pos[5]   # y2
                    ]

                    # Ajouter au track avec flag 'interpolated'
                    tracks["ball"][frame_num][1] = {
                        "bbox": bbox,
                        "interpolated": True,
                        "confidence": 0.5  # Confiance réduite pour les positions interpolées
                    }

        # Compter les interpolations
        interpolated_count = sum(
            1 for frame in tracks["ball"]
            for track_id, data in frame.items()
            if data.get("interpolated", False)
        )

        print(f"✅ {interpolated_count} positions interpolées")

        return tracks

    def smooth_ball_trajectory(self, tracks: Dict, window_size: int = 5) -> Dict:
        """
        Lisse la trajectoire du ballon avec un filtre moyen mobile.

        Args:
            tracks: Tracks avec positions du ballon
            window_size: Taille de la fenêtre de lissage

        Returns:
            Tracks avec trajectoire lissée
        """
        ball_tracks = tracks["ball"]
        n_frames = len(ball_tracks)

        # Collecter toutes les positions (détectées + interpolées)
        centers_x = []
        centers_y = []
        valid_frames = []

        for frame_num, ball_dict in enumerate(ball_tracks):
            if ball_dict and 1 in ball_dict:
                bbox = ball_dict[1]["bbox"]
                centers_x.append((bbox[0] + bbox[2]) / 2)
                centers_y.append((bbox[1] + bbox[3]) / 2)
                valid_frames.append(frame_num)

        if len(valid_frames) < window_size:
            return tracks

        # Appliquer le lissage
        smoothed_x = self._moving_average(centers_x, window_size)
        smoothed_y = self._moving_average(centers_y, window_size)

        # Mettre à jour les positions
        for i, frame_num in enumerate(valid_frames):
            if i < len(smoothed_x):
                bbox = tracks["ball"][frame_num][1]["bbox"]
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                # Recalculer la bbox autour du centre lissé
                tracks["ball"][frame_num][1]["bbox"] = [
                    smoothed_x[i] - width / 2,
                    smoothed_y[i] - height / 2,
                    smoothed_x[i] + width / 2,
                    smoothed_y[i] + height / 2
                ]

        return tracks

    def _moving_average(self, data: List[float], window_size: int) -> List[float]:
        """Calcule la moyenne mobile"""
        result = []
        half_window = window_size // 2

        for i in range(len(data)):
            start = max(0, i - half_window)
            end = min(len(data), i + half_window + 1)
            window = data[start:end]
            result.append(sum(window) / len(window))

        return result
