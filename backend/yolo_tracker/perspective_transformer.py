import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional


class PerspectiveTransformer:
    """
    Transforme les coordonnées de la vue caméra en coordonnées terrain (vue du dessus).
    Utilise une homographie basée sur les keypoints du terrain.
    """

    # Dimensions standard d'un terrain de football (en mètres)
    FIELD_WIDTH = 105.0  # Longueur
    FIELD_HEIGHT = 68.0  # Largeur

    # Keypoints du terrain (coins et marquages importants)
    DEFAULT_KEYPOINTS = {
        # Coins du terrain
        "top_left": (0, 0),
        "top_right": (FIELD_WIDTH, 0),
        "bottom_left": (0, FIELD_HEIGHT),
        "bottom_right": (FIELD_WIDTH, FIELD_HEIGHT),
        # Centre
        "center": (FIELD_WIDTH / 2, FIELD_HEIGHT / 2),
        # Points de penalty
        "penalty_left": (11, FIELD_HEIGHT / 2),
        "penalty_right": (FIELD_WIDTH - 11, FIELD_HEIGHT / 2),
    }

    def __init__(self, field_width: float = 105.0, field_height: float = 68.0):
        """
        Args:
            field_width: Largeur du terrain en mètres (longueur)
            field_height: Hauteur du terrain en mètres (largeur)
        """
        self.field_width = field_width
        self.field_height = field_height
        self.transform_matrix: Optional[np.ndarray] = None
        self.inverse_matrix: Optional[np.ndarray] = None
        self.scale_x: float = 1.0
        self.scale_y: float = 1.0

    def set_transform_from_keypoints(
        self,
        image_points: List[Tuple[float, float]],
        field_points: Optional[List[Tuple[float, float]]] = None
    ) -> bool:
        """
        Calcule la matrice de transformation à partir de points correspondants.

        Args:
            image_points: Points dans l'image (coins du terrain visibles) [(x, y), ...]
            field_points: Points correspondants sur le terrain en mètres

        Returns:
            True si la transformation a été calculée avec succès
        """
        if field_points is None:
            # Utiliser les coins par défaut
            field_points = [
                (0, 0),
                (self.field_width, 0),
                (self.field_width, self.field_height),
                (0, self.field_height)
            ]

        if len(image_points) < 4 or len(field_points) < 4:
            print("❌ Au moins 4 points sont nécessaires pour la transformation")
            return False

        # Convertir en numpy arrays
        src_points = np.array(image_points, dtype=np.float32)
        dst_points = np.array(field_points, dtype=np.float32)

        # Calculer l'homographie
        self.transform_matrix = cv2.findHomography(src_points, dst_points)[0]
        self.inverse_matrix = cv2.findHomography(dst_points, src_points)[0]

        if self.transform_matrix is not None:
            print("✅ Matrice de perspective calculée")
            return True

        return False

    def auto_detect_keypoints(self, frame: np.ndarray) -> Optional[List[Tuple[float, float]]]:
        """
        Détecte automatiquement les keypoints du terrain.
        Simplifié - utilise les lignes blanches du terrain.

        Args:
            frame: Image du terrain

        Returns:
            Liste des points détectés ou None
        """
        # Convertir en grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Détecter les lignes avec Hough
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=100,
                                minLineLength=100, maxLineGap=10)

        if lines is None or len(lines) < 4:
            return None

        # Trouver les intersections des lignes (coins du terrain)
        # Simplifié: on prend les extrémités des lignes détectées
        points = []
        for line in lines[:10]:  # Limiter à 10 lignes
            x1, y1, x2, y2 = line[0]
            points.append((x1, y1))
            points.append((x2, y2))

        # Clustering simple pour trouver les coins principaux
        if len(points) >= 4:
            # Prendre les points aux extrémités
            points = sorted(points, key=lambda p: p[0] + p[1])
            return points[:4]

        return None

    def image_to_field(self, image_point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Convertit un point de l'image en coordonnées terrain.

        Args:
            image_point: (x, y) dans l'image

        Returns:
            (x, y) en mètres sur le terrain
        """
        if self.transform_matrix is None:
            return None

        # Appliquer la transformation
        point = np.array([[image_point[0], image_point[1], 1]], dtype=np.float32).T
        transformed = self.transform_matrix @ point

        # Normaliser - extraire les valeurs scalaires
        if transformed[2, 0] != 0:
            field_x = transformed[0, 0] / transformed[2, 0]
            field_y = transformed[1, 0] / transformed[2, 0]
            return (float(field_x), float(field_y))

        return None

    def field_to_image(self, field_point: Tuple[float, float]) -> Optional[Tuple[float, float]]:
        """
        Convertit un point du terrain en coordonnées image.

        Args:
            field_point: (x, y) en mètres

        Returns:
            (x, y) dans l'image
        """
        if self.inverse_matrix is None:
            return None

        point = np.array([[field_point[0], field_point[1], 1]], dtype=np.float32).T
        transformed = self.inverse_matrix @ point

        if transformed[2, 0] != 0:
            img_x = transformed[0, 0] / transformed[2, 0]
            img_y = transformed[1, 0] / transformed[2, 0]
            return (float(img_x), float(img_y))

        return None

    def transform_tracks(self, tracks: Dict) -> Dict:
        """
        Transforme toutes les positions des tracks en coordonnées terrain.

        Args:
            tracks: Tracks avec positions des objets

        Returns:
            Tracks avec positions terrain ajoutées
        """
        if self.transform_matrix is None:
            print("⚠️ Matrice de transformation non définie")
            return tracks

        print("🗺️ Transformation des coordonnées en vue terrain...")

        for frame_num in range(len(tracks["players"])):
            for track_id, player in tracks["players"][frame_num].items():
                bbox = player.get("adjusted_bbox", player["bbox"])
                center_x = (bbox[0] + bbox[2]) / 2
                center_y = bbox[3]  # Bas de la bbox (pieds du joueur)

                field_pos = self.image_to_field((center_x, center_y))
                if field_pos:
                    player["field_position"] = field_pos

        return tracks

    def create_field_view(self, tracks: Dict, frame_shape: Tuple[int, int]) -> np.ndarray:
        """
        Crée une vue 2D du terrain avec les positions des joueurs.

        Args:
            tracks: Tracks avec positions terrain
            frame_shape: (height, width) de la frame originale

        Returns:
            Image de la vue terrain
        """
        # Créer une image du terrain (ratio 105:68)
        field_img_height = 680
        field_img_width = int(field_img_height * (self.field_width / self.field_height))

        field_img = np.zeros((field_img_height, field_img_width, 3), dtype=np.uint8)

        # Dessiner le terrain (lignes blanches)
        cv2.rectangle(field_img, (50, 50), (field_img_width - 50, field_img_height - 50), (255, 255, 255), 2)
        cv2.line(field_img, (field_img_width // 2, 50), (field_img_width // 2, field_img_height - 50), (255, 255, 255), 2)
        cv2.circle(field_img, (field_img_width // 2, field_img_height // 2), 50, (255, 255, 255), 2)

        # Échelle pour convertir mètres en pixels
        scale_x = (field_img_width - 100) / self.field_width
        scale_y = (field_img_height - 100) / self.field_height

        # Dessiner les positions des joueurs (dernière frame)
        if tracks["players"]:
            last_frame = tracks["players"][-1]
            for track_id, player in last_frame.items():
                if "field_position" in player:
                    fx, fy = player["field_position"]
                    px = int(50 + fx * scale_x)
                    py = int(50 + fy * scale_y)

                    # Couleur selon l'équipe
                    if "team" in player:
                        team_id = player["team"]
                        color = (0, 0, 255) if team_id == 0 else (255, 0, 0)
                    else:
                        color = (0, 255, 0)

                    cv2.circle(field_img, (px, py), 8, color, -1)
                    cv2.putText(field_img, str(track_id), (px - 10, py - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return field_img
