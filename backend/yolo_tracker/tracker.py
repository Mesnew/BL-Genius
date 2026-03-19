import cv2
import numpy as np
from ultralytics import YOLO
import supervision as sv
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import pickle

from .team_assigner import TeamAssigner
from .ball_interpolator import BallInterpolator
from .camera_movement_estimator import CameraMovementEstimator
from .perspective_transformer import PerspectiveTransformer
from .speed_calculator import SpeedCalculator
from .jersey_number_detector import JerseyNumberDetector

class FootballTracker:
    """Tracker de football basé sur YOLO fine-tuné et ByteTrack"""

    # Classes du modèle fine-tuné Roboflow
    # 0: ball, 1: goalkeeper, 2: player, 3: referee
    CLASS_NAMES = {
        0: "ball",
        1: "goalkeeper",
        2: "player",
        3: "referee"
    }

    # Couleurs pour chaque classe (BGR format)
    COLORS = {
        "ball": (0, 0, 255),        # Rouge
        "goalkeeper": (0, 165, 255), # Orange
        "player": (0, 255, 0),      # Vert
        "referee": (0, 255, 255)    # Jaune
    }

    def __init__(self, model_path: str = "yolov8m.pt"):
        """
        Args:
            model_path: Chemin vers le modèle YOLO (.pt)
                       Si best.pt existe, utilise le modèle fine-tuné
                       Sinon utilise le modèle COCO standard
        """
        # Vérifier si le modèle fine-tuné existe
        models_dir = Path(__file__).parent.parent / "models"
        fine_tuned_path = models_dir / "best.pt"

        if fine_tuned_path.exists():
            print(f"✅ Utilisation du modèle fine-tuné: {fine_tuned_path}")
            self.model = YOLO(str(fine_tuned_path))
            self.using_fine_tuned = True
        else:
            print(f"⚠️ Modèle fine-tuné non trouvé, utilisation de: {model_path}")
            self.model = YOLO(model_path)
            self.using_fine_tuned = False

        # Initialiser le tracker ByteTrack
        self.tracker = sv.ByteTrack(
            track_thresh=0.1,
            track_buffer=30,
            match_thresh=0.8,
            frame_rate=24
        )

        # Initialiser les modules
        self.team_assigner = TeamAssigner(n_teams=2)
        self.ball_interpolator = BallInterpolator(max_gap=10)
        self.camera_estimator = CameraMovementEstimator()
        self.perspective_transformer = PerspectiveTransformer()
        self.speed_calculator = None  # Sera initialisé avec le FPS
        self.jersey_detector = JerseyNumberDetector()  # Détecteur de numéros

    def detect_frames(self, frames: List[np.ndarray], batch_size: int = 20) -> List:
        """Détecter les objets sur une liste de frames"""
        detections = []

        for i in range(0, len(frames), batch_size):
            batch = frames[i:i + batch_size]
            results = self.model.predict(batch, conf=0.1)
            detections.extend(results)

        return detections

    def get_object_tracks(self, frames: List[np.ndarray]) -> Dict:
        """
        Tracker les objets (joueurs, ballon, arbitres) sur toutes les frames
        """
        detections = self.detect_frames(frames)

        tracks = {
            "players": [],
            "goalkeepers": [],  # Séparé des joueurs
            "referees": [],
            "ball": []
        }

        for frame_num, detection in enumerate(detections):
            # Convertir en format supervision
            sv_detections = sv.Detections.from_ultralytics(detection)

            # Tracker
            sv_detections = self.tracker.update_with_detections(sv_detections)

            # Initialiser les dictionnaires pour cette frame
            for key in tracks.keys():
                tracks[key].append({})

            for i, class_id in enumerate(sv_detections.class_id):
                bbox = sv_detections.xyxy[i].tolist()
                track_id = sv_detections.tracker_id[i] if sv_detections.tracker_id is not None else None

                if self.using_fine_tuned:
                    # Modèle fine-tuné: 0: ball, 1: goalkeeper, 2: player, 3: referee
                    if class_id == 0:  # ball
                        tracks["ball"][frame_num][1] = {"bbox": bbox}
                    elif class_id == 1:  # goalkeeper
                        if track_id is not None:
                            tracks["goalkeepers"][frame_num][track_id] = {"bbox": bbox}
                    elif class_id == 2:  # player
                        if track_id is not None:
                            tracks["players"][frame_num][track_id] = {"bbox": bbox}
                    elif class_id == 3:  # referee
                        if track_id is not None:
                            tracks["referees"][frame_num][track_id] = {"bbox": bbox}
                else:
                    # Modèle COCO standard: 0: person, 32: sports ball
                    if class_id == 0:  # person -> player (on ne distingue pas gardien/arbitre sans fine-tuning)
                        if track_id is not None:
                            tracks["players"][frame_num][track_id] = {"bbox": bbox}
                    elif class_id == 32:  # sports ball
                        tracks["ball"][frame_num][1] = {"bbox": bbox}

        return tracks

    def draw_annotations(self, frames: List[np.ndarray], tracks: Dict,
                         camera_movements: List[Tuple[float, float]] = None) -> List[np.ndarray]:
        """Dessiner les annotations sur les frames"""
        output_frames = []

        for frame_num, frame in enumerate(frames):
            frame = frame.copy()

            # Récupérer les tracks pour cette frame
            player_dict = tracks["players"][frame_num]
            goalkeeper_dict = tracks["goalkeepers"][frame_num]
            referee_dict = tracks["referees"][frame_num]
            ball_dict = tracks["ball"][frame_num]

            # Dessiner les joueurs (ellipses avec couleur d'équipe)
            for track_id, player in player_dict.items():
                bbox = player["bbox"]
                # Utiliser la couleur d'équipe si disponible, sinon vert par défaut
                if "team_color" in player:
                    # Convertir RGB en BGR pour OpenCV
                    team_color_rgb = player["team_color"]
                    color = (team_color_rgb[2], team_color_rgb[1], team_color_rgb[0])
                else:
                    color = self.COLORS["player"]
                frame = self._draw_ellipse(frame, bbox, color, track_id)

                # Afficher le numéro de maillot si détecté
                if "jersey_number" in player:
                    frame = self.jersey_detector.draw_jersey_number(
                        frame, bbox, player["jersey_number"], (255, 255, 255)
                    )

            # Dessiner les gardiens (ellipses oranges)
            for track_id, goalkeeper in goalkeeper_dict.items():
                bbox = goalkeeper["bbox"]
                frame = self._draw_ellipse(frame, bbox, self.COLORS["goalkeeper"], track_id)

            # Dessiner les arbitres (ellipses jaunes)
            for track_id, referee in referee_dict.items():
                bbox = referee["bbox"]
                frame = self._draw_ellipse(frame, bbox, self.COLORS["referee"], track_id)

            # Dessiner le ballon (triangle rouge)
            for track_id, ball in ball_dict.items():
                bbox = ball["bbox"]
                # Couleur différente si interpolé
                if ball.get("interpolated", False):
                    color = (128, 128, 128)  # Gris pour positions interpolées
                else:
                    color = self.COLORS["ball"]
                frame = self._draw_triangle(frame, bbox, color)

            # Dessiner les vitesses si disponibles
            if self.speed_calculator:
                frame = self.speed_calculator.draw_speed_on_frame(frame, tracks, frame_num)

            # Ajouter une légende
            frame = self._draw_legend(frame, tracks)

            # Ajouter info sur le mouvement de caméra
            if camera_movements and frame_num < len(camera_movements):
                dx, dy = camera_movements[frame_num]
                if abs(dx) > 1 or abs(dy) > 1:
                    cv2.putText(frame, f"Cam: ({dx:.1f}, {dy:.1f})", (10, frame.shape[0] - 20),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            output_frames.append(frame)

        return output_frames

    def _draw_ellipse(self, frame: np.ndarray, bbox: List[float],
                      color: Tuple[int, int, int], track_id: Optional[int] = None) -> np.ndarray:
        """Dessiner une ellipse sous un joueur"""
        x1, y1, x2, y2 = map(int, bbox)

        # Centre de l'ellipse (bas du bbox)
        center_x = (x1 + x2) // 2
        center_y = y2

        # Rayons
        radius_x = (x2 - x1) // 2
        radius_y = int(radius_x * 0.35)

        # Dessiner l'ellipse
        cv2.ellipse(
            frame,
            center=(center_x, center_y),
            axes=(radius_x, radius_y),
            angle=0.0,
            startAngle=-45,
            endAngle=235,
            color=color,
            thickness=2,
            lineType=cv2.LINE_4
        )

        # Ajouter le track_id
        if track_id is not None:
            rect_width = 40
            rect_height = 20
            x1_rect = center_x - rect_width // 2
            y1_rect = center_y + 15
            x2_rect = x1_rect + rect_width
            y2_rect = y1_rect + rect_height

            cv2.rectangle(
                frame,
                (x1_rect, y1_rect),
                (x2_rect, y2_rect),
                color,
                cv2.FILLED
            )

            text_x = x1_rect + 12
            if track_id > 99:
                text_x -= 10

            cv2.putText(
                frame,
                str(track_id),
                (text_x, y1_rect + 15),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 0),
                2
            )

        return frame

    def _draw_triangle(self, frame: np.ndarray, bbox: List[float],
                        color: Tuple[int, int, int]) -> np.ndarray:
        """Dessiner un triangle au-dessus du ballon"""
        x1, y1, x2, y2 = map(int, bbox)

        center_x = (x1 + x2) // 2
        center_y = y1

        # Points du triangle
        triangle_points = np.array([
            [center_x, center_y],
            [center_x - 10, center_y - 20],
            [center_x + 10, center_y - 20]
        ], dtype=np.int32)

        # Triangle rempli
        cv2.drawContours(frame, [triangle_points], 0, color, cv2.FILLED)
        # Bordure
        cv2.drawContours(frame, [triangle_points], 0, (0, 0, 0), 2)

        return frame

    def _draw_legend(self, frame: np.ndarray, tracks: Dict = None) -> np.ndarray:
        """Dessiner une légende des couleurs"""
        legend_items = [
            ("Gardien", self.COLORS["goalkeeper"]),
            ("Arbitre", self.COLORS["referee"]),
            ("Ballon", self.COLORS["ball"])
        ]

        x = 10
        y = 30

        # Ajouter les équipes si disponibles
        if self.team_assigner.is_fitted and self.team_assigner.team_colors:
            for team_id, color_rgb in self.team_assigner.team_colors.items():
                # Convertir RGB en BGR
                color_bgr = (color_rgb[2], color_rgb[1], color_rgb[0])
                legend_items.insert(0, (f"Équipe {team_id + 1}", color_bgr))
        else:
            legend_items.insert(0, ("Joueur", self.COLORS["player"]))

        for label, color in legend_items:
            # Rectangle de couleur
            cv2.rectangle(frame, (x, y - 15), (x + 20, y), color, cv2.FILLED)
            # Texte
            cv2.putText(frame, label, (x + 25, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            y += 25

        return frame

    def process_video(self, input_path: str, output_path: str) -> str:
        """
        Traiter une vidéo complète

        Args:
            input_path: Chemin de la vidéo d'entrée
            output_path: Chemin de la vidéo de sortie

        Returns:
            Chemin de la vidéo analysée
        """
        print(f"🎬 Lecture de la vidéo: {input_path}")

        # Lire la vidéo
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir la vidéo: {input_path}")

        # Récupérer les propriétés
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📊 Vidéo: {width}x{height} @ {fps}fps ({total_frames} frames)")

        # Lire toutes les frames
        frames = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)

        cap.release()
        print(f"✅ {len(frames)} frames lues")

        # Tracker
        print("🔍 Tracking des objets...")
        tracks = self.get_object_tracks(frames)

        # Détection des numéros de maillot
        print("🔢 Détection des numéros de maillot...")
        tracks = self.jersey_detector.detect_jersey_numbers(frames, tracks)

        # Assigner les équipes (K-Means)
        print("🏃 Assignation des équipes...")
        tracks = self.team_assigner.assign_teams_to_tracks(frames, tracks)

        # Interpolation du ballon
        print("🎯 Interpolation du ballon...")
        tracks = self.ball_interpolator.interpolate_ball_positions(tracks)
        tracks = self.ball_interpolator.smooth_ball_trajectory(tracks)

        # Estimation du mouvement de caméra
        print("📹 Estimation du mouvement de caméra...")
        camera_movements = self.camera_estimator.process_video(frames)
        tracks = self.camera_estimator.adjust_positions(tracks, camera_movements)

        # Transformation de perspective (utiliser les 4 coins du terrain si possible)
        print("🗺️ Configuration de la perspective...")
        # Détection automatique des keypoints sur la première frame
        keypoints = self.perspective_transformer.auto_detect_keypoints(frames[0])
        if keypoints and len(keypoints) >= 4:
            self.perspective_transformer.set_transform_from_keypoints(keypoints[:4])
            tracks = self.perspective_transformer.transform_tracks(tracks)

        # Calcul des vitesses
        print("⚡ Calcul des vitesses...")
        self.speed_calculator = SpeedCalculator(fps=fps)
        tracks = self.speed_calculator.calculate_speeds(tracks)

        # Compter les objets détectés
        total_players = sum(len(f) for f in tracks["players"])
        total_goalkeepers = sum(len(f) for f in tracks["goalkeepers"])
        total_referees = sum(len(f) for f in tracks["referees"])
        total_balls = sum(len(f) for f in tracks["ball"])

        print(f"📈 Détections:")
        print(f"   - Joueurs: {total_players}")
        print(f"   - Gardiens: {total_goalkeepers}")
        print(f"   - Arbitres: {total_referees}")
        print(f"   - Ballons: {total_balls}")

        # Générer le rapport de statistiques
        if self.speed_calculator:
            stats_report = self.speed_calculator.generate_stats_report(tracks)
            print(stats_report)

        # Annoter
        print("🎨 Annotation des frames...")
        output_frames = self.draw_annotations(frames, tracks, camera_movements)

        # Sauvegarder
        print(f"💾 Sauvegarde vers: {output_path}")
        # Utiliser la fonction save_video qui gère H.264 via FFmpeg
        from utils.video_utils import save_video
        save_video(output_frames, output_path, fps)
        print("✅ Terminé!")

        return output_path
