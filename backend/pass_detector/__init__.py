import sys
sys.path.append('../')
import numpy as np
from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections import deque

@dataclass
class Pass:
    """Représente une passe détectée"""
    frame_start: int
    frame_end: int
    player_from: int
    player_to: int
    team: int
    distance_meters: float
    speed_kmh: float
    successful: bool  # True si le destinataire a reçu le ballon

class PassDetector:
    """
    Détecte les passes entre joueurs en analysant:
    - Qui contrôle le ballon à chaque frame
    - Les changements de contrôle du ballon
    - La distance et la vitesse de la passe
    """

    def __init__(self):
        self.min_pass_frames = 3  # Durée minimale d'une passe (frames)
        self.max_pass_frames = 60  # Durée maximale (2 secondes à 30fps)
        self.min_distance_meters = 2.0  # Distance minimale pour compter comme une passe
        self.possession_history = deque(maxlen=10)  # Historique récent du contrôle

    def detect_passes(self, tracks, team_ball_control) -> List[Pass]:
        """
        Détecte toutes les passes dans la séquence vidéo.

        Args:
            tracks: Dictionnaire des tracks avec players et ball
            team_ball_control: Liste de l'équipe qui contrôle le ballon par frame

        Returns:
            Liste des passes détectées
        """
        passes = []
        num_frames = len(tracks['players'])

        # Construire l'historique du contrôle du ballon
        ball_possession = []  # (frame_num, player_id, team, position)

        for frame_num in range(num_frames):
            # Trouver qui a le ballon dans cette frame
            player_with_ball = None
            team = team_ball_control[frame_num] if frame_num < len(team_ball_control) else 1

            for player_id, player_info in tracks['players'][frame_num].items():
                if player_info.get('has_ball', False):
                    # Récupérer la position transformée si disponible
                    position = player_info.get('position_transformed')
                    if position is None:
                        position = player_info.get('position', [0, 0])
                    player_with_ball = player_id
                    break

            ball_possession.append({
                'frame': frame_num,
                'player': player_with_ball,
                'team': team,
                'position': position if player_with_ball else None
            })

        # Détecter les changements de possession = passes
        current_pass_start = None

        for i, possession in enumerate(ball_possession):
            if possession['player'] is not None:
                if current_pass_start is None:
                    # Début d'une nouvelle possession
                    current_pass_start = i
                else:
                    # Vérifier si le joueur a changé
                    prev_player = ball_possession[current_pass_start]['player']
                    curr_player = possession['player']

                    if curr_player != prev_player:
                        # Changement de joueur = potentielle passe
                        pass_info = self._analyze_pass(
                            ball_possession, current_pass_start, i, tracks
                        )
                        if pass_info:
                            passes.append(pass_info)

                        # Nouvelle possession commence
                        current_pass_start = i
            else:
                # Ballon perdu (hors champ ou non détecté)
                if current_pass_start is not None:
                    # Vérifier si c'était une passe ou juste une perte
                    pass_info = self._analyze_pass(
                        ball_possession, current_pass_start, i, tracks, incomplete=True
                    )
                    if pass_info:
                        passes.append(pass_info)

                current_pass_start = None

        return passes

    def _analyze_pass(self, possession_history, start_idx, end_idx, tracks, incomplete=False) -> Optional[Pass]:
        """
        Analyse une séquence de changement de possession pour déterminer si c'est une passe.

        Args:
            possession_history: Liste des possessions par frame
            start_idx: Index de début de la possession
            end_idx: Index de fin
            tracks: Tracks des joueurs
            incomplete: True si la passe n'a pas été complétée (ballon perdu)

        Returns:
            Objet Pass si c'est une passe valide, None sinon
        """
        start_possession = possession_history[start_idx]
        end_possession = possession_history[end_idx - 1]  # Dernière frame avant changement

        player_from = start_possession['player']
        player_to = end_possession['player'] if not incomplete else None

        if player_from is None:
            return None

        # Calculer la distance de la passe
        pos_from = start_possession['position']
        pos_to = end_possession['position'] if end_possession['player'] else None

        if pos_from is None:
            return None

        if pos_to is not None:
            distance = np.sqrt((pos_to[0] - pos_from[0])**2 + (pos_to[1] - pos_from[1])**2)
        else:
            # Essayer d'estimer depuis les tracks du ballon
            distance = self._estimate_pass_distance(tracks, start_idx, end_idx)

        # Vérifier les critères de passe
        duration_frames = end_idx - start_idx

        if distance < self.min_distance_meters:
            return None  # Trop courte pour être une passe

        if duration_frames > self.max_pass_frames:
            return None  # Trop longue, probablement une course avec le ballon

        # Calculer la vitesse de la passe
        time_seconds = duration_frames / 24.0  # Supposons 24 fps
        speed_kmh = (distance / time_seconds) * 3.6 if time_seconds > 0 else 0

        return Pass(
            frame_start=start_idx,
            frame_end=end_idx,
            player_from=player_from,
            player_to=player_to if player_to else -1,
            team=start_possession['team'],
            distance_meters=distance,
            speed_kmh=speed_kmh,
            successful=not incomplete and player_to is not None
        )

    def _estimate_pass_distance(self, tracks, start_frame, end_frame) -> float:
        """
        Estime la distance d'une passe en utilisant les positions du ballon.
        """
        ball_positions = []

        for frame_num in range(start_frame, min(end_frame, len(tracks['ball']))):
            ball_dict = tracks['ball'][frame_num]
            if ball_dict and 1 in ball_dict:
                pos = ball_dict[1].get('position_transformed')
                if pos:
                    ball_positions.append(pos)

        if len(ball_positions) < 2:
            return 0.0

        # Distance totale parcourue par le ballon
        total_distance = 0.0
        for i in range(1, len(ball_positions)):
            dx = ball_positions[i][0] - ball_positions[i-1][0]
            dy = ball_positions[i][1] - ball_positions[i-1][1]
            total_distance += np.sqrt(dx**2 + dy**2)

        return total_distance

    def get_pass_statistics(self, passes: List[Pass]) -> dict:
        """
        Calcule les statistiques des passes.
        """
        if not passes:
            return {
                'total_passes': 0,
                'successful_passes': 0,
                'failed_passes': 0,
                'success_rate': 0,
                'avg_distance': 0,
                'max_distance': 0,
                'avg_speed': 0,
                'passes_by_team': {1: 0, 2: 0}
            }

        successful = [p for p in passes if p.successful]
        failed = [p for p in passes if not p.successful]

        distances = [p.distance_meters for p in passes]
        speeds = [p.speed_kmh for p in passes]

        passes_by_team = {1: 0, 2: 0}
        for p in passes:
            passes_by_team[p.team] = passes_by_team.get(p.team, 0) + 1

        return {
            'total_passes': len(passes),
            'successful_passes': len(successful),
            'failed_passes': len(failed),
            'success_rate': len(successful) / len(passes) * 100 if passes else 0,
            'avg_distance': np.mean(distances) if distances else 0,
            'max_distance': max(distances) if distances else 0,
            'avg_speed': np.mean(speeds) if speeds else 0,
            'passes_by_team': passes_by_team
        }

    def draw_passes_on_frame(self, frame, passes: List[Pass], current_frame: int, tracks):
        """
        Dessine les passes actives sur la frame (flèches entre joueurs).
        """
        import cv2

        for pass_event in passes:
            # Ne dessiner que les passes récentes (encore visibles)
            if pass_event.frame_end < current_frame - 30:  # Visible pendant 30 frames
                continue

            if pass_event.frame_start > current_frame:
                continue

            # Récupérer les positions des joueurs
            if pass_event.frame_start < len(tracks['players']):
                player_from_dict = tracks['players'][pass_event.frame_start]
                if pass_event.player_from in player_from_dict:
                    pos_from = player_from_dict[pass_event.player_from].get('position')
                    if pos_from:
                        # Dessiner point de départ
                        cv2.circle(frame, (int(pos_from[0]), int(pos_from[1])), 8, (255, 255, 0), -1)

            if pass_event.frame_end < len(tracks['players']):
                player_to_dict = tracks['players'][pass_event.frame_end]
                if pass_event.player_to in player_to_dict:
                    pos_to = player_to_dict[pass_event.player_to].get('position')
                    if pos_to:
                        # Dessiner point d'arrivée
                        color = (0, 255, 0) if pass_event.successful else (0, 0, 255)
                        cv2.circle(frame, (int(pos_to[0]), int(pos_to[1])), 8, color, -1)

                        # Dessiner flèche si on a les deux positions
                        if pos_from and pos_to:
                            cv2.arrowedLine(frame,
                                          (int(pos_from[0]), int(pos_from[1])),
                                          (int(pos_to[0]), int(pos_to[1])),
                                          color, 3, tipLength=0.3)

        return frame
