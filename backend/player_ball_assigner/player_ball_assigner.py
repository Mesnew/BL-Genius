import sys
sys.path.append('../')
import numpy as np
from utils import get_center_of_bbox, measure_distance

class PlayerBallAssigner():
    def __init__(self):
        # Distance maximale en pixels (ancienne méthode)
        self.max_player_ball_distance = 70
        # Distance maximale en mètres sur le terrain (nouvelle méthode)
        self.max_ground_distance_meters = 0.5

    def assign_ball_to_player(self, players, ball_bbox, ball_position_transformed=None):
        """
        Assigne le ballon au joueur le plus proche.

        Args:
            players: dict des joueurs avec leurs données
            ball_bbox: bounding box du ballon [x1, y1, x2, y2]
            ball_position_transformed: position transformée (x, y) sur le terrain en mètres (optionnel)

        Returns:
            player_id du joueur qui possède le ballon, ou -1 si personne
        """
        miniumum_distance = 99999
        assigned_player = -1

        # Utiliser la position transformée si disponible (plus précis)
        if ball_position_transformed is not None:
            return self._assign_by_ground_distance(players, ball_position_transformed)

        # Sinon utiliser la méthode par pixels (ancienne méthode)
        ball_position = get_center_of_bbox(ball_bbox)

        for player_id, player in players.items():
            player_bbox = player['bbox']

            distance_left = measure_distance((player_bbox[0], player_bbox[-1]), ball_position)
            distance_right = measure_distance((player_bbox[2], player_bbox[-1]), ball_position)
            distance = min(distance_left, distance_right)

            if distance < self.max_player_ball_distance:
                if distance < miniumum_distance:
                    miniumum_distance = distance
                    assigned_player = player_id

        return assigned_player

    def _assign_by_ground_distance(self, players, ball_position_transformed):
        """
        Assigne le ballon basé sur la distance réelle sur le terrain (en mètres).
        Plus précis que la distance en pixels.

        Args:
            players: dict des joueurs avec position_transformed
            ball_position_transformed: (x, y) position du ballon en mètres

        Returns:
            player_id du joueur qui possède le ballon, ou -1
        """
        minimum_distance = float('inf')
        assigned_player = -1

        for player_id, player in players.items():
            # Vérifier si le joueur a une position transformée
            if 'position_transformed' not in player:
                continue

            player_pos = player['position_transformed']

            # Calculer la distance euclidienne sur le terrain (en mètres)
            distance = np.sqrt(
                (player_pos[0] - ball_position_transformed[0])**2 +
                (player_pos[1] - ball_position_transformed[1])**2
            )

            # Seuil de 0.5m - un joueur doit être à moins de 50cm du ballon
            if distance < self.max_ground_distance_meters:
                if distance < minimum_distance:
                    minimum_distance = distance
                    assigned_player = player_id

        return assigned_player