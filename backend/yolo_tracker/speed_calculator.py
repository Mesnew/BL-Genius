import cv2
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict


class SpeedCalculator:
    """
    Calcule la vitesse et la distance parcourue par les joueurs.
    """

    def __init__(self, fps: float = 25.0, field_width: float = 105.0, field_height: float = 68.0):
        """
        Args:
            fps: Framerate de la vidéo
            field_width: Largeur du terrain en mètres
            field_height: Hauteur du terrain en mètres
        """
        self.fps = fps
        self.field_width = field_width
        self.field_height = field_height
        self.frame_time = 1.0 / fps  # Temps entre deux frames en secondes

    def calculate_speeds(self, tracks: Dict) -> Dict:
        """
        Calcule la vitesse instantanée pour chaque joueur.

        Args:
            tracks: Tracks avec positions terrain

        Returns:
            Tracks avec vitesses ajoutées
        """
        print("⚡ Calcul des vitesses...")

        for frame_num in range(1, len(tracks["players"])):
            current_frame = tracks["players"][frame_num]
            prev_frame = tracks["players"][frame_num - 1]

            for track_id, player in current_frame.items():
                if "field_position" not in player:
                    continue

                # Récupérer la position précédente
                if track_id in prev_frame and "field_position" in prev_frame[track_id]:
                    prev_pos = prev_frame[track_id]["field_position"]
                    curr_pos = player["field_position"]

                    # Distance en mètres
                    distance = np.sqrt(
                        (curr_pos[0] - prev_pos[0]) ** 2 +
                        (curr_pos[1] - prev_pos[1]) ** 2
                    )

                    # Vitesse en km/h
                    speed_mps = distance / self.frame_time  # m/s
                    speed_kmh = speed_mps * 3.6  # km/h

                    player["speed_kmh"] = speed_kmh
                    player["distance_m"] = distance
                else:
                    player["speed_kmh"] = 0.0
                    player["distance_m"] = 0.0

        return tracks

    def calculate_total_distances(self, tracks: Dict) -> Dict[int, float]:
        """
        Calcule la distance totale parcourue par chaque joueur.

        Args:
            tracks: Tracks avec positions et vitesses

        Returns:
            Dictionnaire {track_id: distance_totale_en_mètres}
        """
        print("📏 Calcul des distances totales...")

        distances = defaultdict(float)

        for frame_num in range(len(tracks["players"])):
            for track_id, player in tracks["players"][frame_num].items():
                if "distance_m" in player:
                    distances[track_id] += player["distance_m"]

        # Convertir en km
        distances_km = {track_id: dist / 1000 for track_id, dist in distances.items()}

        print(f"✅ Distances calculées pour {len(distances_km)} joueurs")
        for track_id, dist in sorted(distances_km.items()):
            print(f"   Joueur {track_id}: {dist:.2f} km")

        return distances_km

    def get_max_speeds(self, tracks: Dict) -> Dict[int, float]:
        """
        Calcule la vitesse maximale atteinte par chaque joueur.

        Args:
            tracks: Tracks avec vitesses

        Returns:
            Dictionnaire {track_id: vitesse_max_kmh}
        """
        max_speeds = defaultdict(float)

        for frame_num in range(len(tracks["players"])):
            for track_id, player in tracks["players"][frame_num].items():
                if "speed_kmh" in player:
                    max_speeds[track_id] = max(max_speeds[track_id], player["speed_kmh"])

        return dict(max_speeds)

    def get_average_speeds(self, tracks: Dict) -> Dict[int, float]:
        """
        Calcule la vitesse moyenne de chaque joueur.

        Args:
            tracks: Tracks avec vitesses

        Returns:
            Dictionnaire {track_id: vitesse_moyenne_kmh}
        """
        speed_sums = defaultdict(float)
        speed_counts = defaultdict(int)

        for frame_num in range(len(tracks["players"])):
            for track_id, player in tracks["players"][frame_num].items():
                if "speed_kmh" in player and player["speed_kmh"] > 0:
                    speed_sums[track_id] += player["speed_kmh"]
                    speed_counts[track_id] += 1

        avg_speeds = {}
        for track_id in speed_sums:
            if speed_counts[track_id] > 0:
                avg_speeds[track_id] = speed_sums[track_id] / speed_counts[track_id]

        return avg_speeds

    def generate_stats_report(self, tracks: Dict) -> str:
        """
        Génère un rapport texte des statistiques.

        Args:
            tracks: Tracks complets

        Returns:
            Rapport formaté
        """
        distances = self.calculate_total_distances(tracks)
        max_speeds = self.get_max_speeds(tracks)
        avg_speeds = self.get_average_speeds(tracks)

        report = []
        report.append("=" * 50)
        report.append("📊 STATISTIQUES DES JOUEURS")
        report.append("=" * 50)

        for track_id in sorted(distances.keys()):
            report.append(f"\n🏃 Joueur #{track_id}:")
            report.append(f"   Distance totale: {distances[track_id]:.2f} km")
            if track_id in max_speeds:
                report.append(f"   Vitesse max: {max_speeds[track_id]:.1f} km/h")
            if track_id in avg_speeds:
                report.append(f"   Vitesse moyenne: {avg_speeds[track_id]:.1f} km/h")

        report.append("\n" + "=" * 50)

        return "\n".join(report)

    def draw_speed_on_frame(self, frame: np.ndarray, tracks: Dict, frame_num: int) -> np.ndarray:
        """
        Dessine la vitesse des joueurs sur la frame.

        Args:
            frame: Image
            tracks: Tracks avec vitesses
            frame_num: Numéro de la frame actuelle

        Returns:
            Frame annotée
        """
        if frame_num >= len(tracks["players"]):
            return frame

        frame_height, frame_width = frame.shape[:2]

        for track_id, player in tracks["players"][frame_num].items():
            if "speed_kmh" in player and "bbox" in player:
                bbox = player["bbox"]
                speed = player["speed_kmh"]

                # Filtrer les valeurs aberrantes (NaN, inf, ou vitesses impossibles > 45 km/h)
                if not isinstance(speed, (int, float)) or np.isnan(speed) or np.isinf(speed) or speed > 45 or speed < 0:
                    continue

                # Position du texte (au-dessus du joueur)
                x = int(bbox[0])
                y = int(bbox[1]) - 30

                # Vérifier les limites de l'image
                if x < 0 or x > frame_width - 80 or y < 20 or y > frame_height:
                    continue

                # Couleur selon la vitesse
                if speed < 10:
                    color = (0, 255, 0)  # Vert (lent)
                elif speed < 20:
                    color = (0, 255, 255)  # Jaune (moyen)
                else:
                    color = (0, 0, 255)  # Rouge (rapide)

                # Afficher la vitesse avec fond pour meilleure lisibilité
                text = f"{speed:.1f}"
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                thickness = 2

                (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)

                # Rectangle de fond semi-transparent
                cv2.rectangle(
                    frame,
                    (x - 2, y - text_height - 4),
                    (x + text_width + 4, y + 4),
                    (0, 0, 0),
                    cv2.FILLED
                )

                cv2.putText(frame, text, (x, y), font, font_scale, color, thickness)

        return frame
