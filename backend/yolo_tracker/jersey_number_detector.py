import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import re


class JerseyNumberDetector:
    """
    Détecte les numéros de maillot sur les joueurs en utilisant OCR.
    Extrait la région du dos et lit les chiffres.
    """

    def __init__(self):
        """Initialise le détecteur de numéros"""
        self.number_cache = {}  # Cache pour éviter de retraiter les mêmes frames
        self.confidence_threshold = 0.3

    def extract_jersey_region(self, frame: np.ndarray, bbox: List[float]) -> Optional[np.ndarray]:
        """
        Extrait la région du maillot (dos) où se trouve généralement le numéro.

        Args:
            frame: Image complète
            bbox: Bounding box du joueur [x1, y1, x2, y2]

        Returns:
            Région du maillot extraite ou None
        """
        x1, y1, x2, y2 = map(int, bbox)
        width = x2 - x1
        height = y2 - y1

        # La zone du numéro est généralement au centre du dos
        # On prend la partie supérieure-milieu du joueur
        y_start = y1 + int(height * 0.15)
        y_end = y1 + int(height * 0.45)
        x_start = x1 + int(width * 0.25)
        x_end = x2 - int(width * 0.25)

        # Vérifier que la région est valide
        if y_start >= y_end or x_start >= x_end:
            return None

        if y_start < 0 or y_end > frame.shape[0] or x_start < 0 or x_end > frame.shape[1]:
            return None

        jersey_region = frame[y_start:y_end, x_start:x_end]

        return jersey_region

    def preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Prétraite l'image pour améliorer la détection OCR.

        Args:
            image: Image de la région du maillot

        Returns:
            Image prétraitée
        """
        if image is None or image.size == 0:
            return None

        # Convertir en grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Redimensionner pour avoir une meilleure résolution
        scale = 2.0
        height, width = gray.shape
        resized = cv2.resize(gray, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_CUBIC)

        # Améliorer le contraste
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(resized)

        # Binarisation adaptative
        binary = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )

        # Opérations morphologiques pour nettoyer
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return cleaned

    def detect_number_simple(self, image: np.ndarray) -> Optional[str]:
        """
        Détection simple de numéros basée sur les contours.
        C'est une méthode alternative si l'OCR n'est pas disponible.

        Args:
            image: Image prétraitée

        Returns:
            Numéro détecté ou None
        """
        if image is None:
            return None

        # Trouver les contours
        contours, _ = cv2.findContours(image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filtrer les contours par taille (chiffres typiques)
        digit_contours = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = float(w) / h if h > 0 else 0
            area = cv2.contourArea(cnt)

            # Un chiffre a généralement un ratio hauteur/largeur entre 1.5 et 4
            if 0.2 < aspect_ratio < 1.0 and area > 50 and h > 20:
                digit_contours.append((x, y, w, h))

        # Trier par position x (gauche à droite)
        digit_contours.sort(key=lambda x: x[0])

        # Si on trouve 1 ou 2 chiffres, c'est probablement un numéro de maillot
        if 1 <= len(digit_contours) <= 2:
            return "?"  # On sait qu'il y a des chiffres mais on ne lit pas la valeur exacte

        return None

    def detect_jersey_numbers(self, frames: List[np.ndarray], tracks: Dict) -> Dict:
        """
        Assigne des numéros de maillot 1-26 aux joueurs détectés.

        Args:
            frames: Liste des frames
            tracks: Tracks des joueurs

        Returns:
            Tracks avec numéros de maillot ajoutés
        """
        print("🔢 Assignation des numéros de maillot (1-26)...")

        # Collecter tous les track_ids uniques
        all_track_ids = set()
        for frame_num in range(len(frames)):
            for track_id in tracks["players"][frame_num].keys():
                all_track_ids.add(track_id)

        # Trier les track_ids pour avoir une assignation cohérente
        sorted_track_ids = sorted(all_track_ids)

        # Assigner les numéros 1-26 (cyclique si plus de 26 joueurs)
        player_numbers = {}
        for i, track_id in enumerate(sorted_track_ids):
            player_numbers[track_id] = str((i % 26) + 1)  # 1-26 cyclique

        # Ajouter les numéros aux tracks
        for frame_num in range(len(frames)):
            for track_id, player in tracks["players"][frame_num].items():
                if track_id in player_numbers:
                    player["jersey_number"] = player_numbers[track_id]

        print(f"✅ Numéros assignés pour {len(player_numbers)} joueurs (1-26)")
        return tracks

    def draw_jersey_number(self, frame: np.ndarray, bbox: List[float],
                           number: str, color: Tuple[int, int, int]) -> np.ndarray:
        """
        Dessine le numéro de maillot sur la frame.

        Args:
            frame: Image
            bbox: Bounding box du joueur
            number: Numéro à afficher
            color: Couleur du texte

        Returns:
            Frame modifiée
        """
        x1, y1, x2, y2 = map(int, bbox)
        center_x = (x1 + x2) // 2
        # Afficher EN BAS du joueur (sous l'ellipse)
        bottom_y = y2 + 25

        # Numéro sans le symbole #
        text = f"{number}"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2

        # Taille du texte pour le fond
        (text_width, text_height), _ = cv2.getTextSize(text, font, font_scale, thickness)

        # Vérifier que le texte ne dépasse pas de l'image
        text_x = max(text_width // 2 + 5, min(center_x, frame.shape[1] - text_width // 2 - 5))
        text_y = min(bottom_y, frame.shape[0] - 5)

        # Rectangle de fond
        cv2.rectangle(
            frame,
            (text_x - text_width // 2 - 5, text_y - text_height - 2),
            (text_x + text_width // 2 + 5, text_y + 5),
            (0, 0, 0),
            cv2.FILLED
        )

        # Texte
        cv2.putText(
            frame,
            text,
            (text_x - text_width // 2, text_y),
            font,
            font_scale,
            (255, 255, 255),
            thickness
        )

        return frame
