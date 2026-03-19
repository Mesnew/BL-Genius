from ultralytics import YOLO
import supervision as sv
import pickle
import os
import numpy as np
import pandas as pd
import cv2
import sys 
sys.path.append('../')
from utils import get_center_of_bbox, get_bbox_width, get_foot_position

class Tracker:
    def __init__(self, model_path):
        self.model = YOLO(model_path) 
        self.tracker = sv.ByteTrack()

    def add_position_to_tracks(self,tracks):
        for object, object_tracks in tracks.items():
            for frame_num, track in enumerate(object_tracks):
                for track_id, track_info in track.items():
                    bbox = track_info.get('bbox', [])
                    # Skip if bbox is empty or invalid
                    if not bbox or len(bbox) != 4:
                        continue
                    # Skip if any coordinate is NaN
                    if any(pd.isna(v) for v in bbox):
                        continue
                    try:
                        if object == 'ball':
                            position = get_center_of_bbox(bbox)
                        else:
                            position = get_foot_position(bbox)
                        tracks[object][frame_num][track_id]['position'] = position
                    except (ValueError, TypeError):
                        # Skip if position calculation fails
                        continue

    def interpolate_ball_positions(self, ball_positions):
        """
        Interpole les positions de la balle entre les détections.
        Utilise une interpolation linéaire simple pour suivre la balle précisément.
        """
        # Extract bboxes and track which frames have valid detections
        valid_frames = []
        valid_bboxes = []

        for idx, x in enumerate(ball_positions):
            bbox = x.get(1, {}).get('bbox', [])
            if len(bbox) == 4 and all(v != 0 and not pd.isna(v) for v in bbox):
                valid_frames.append(idx)
                valid_bboxes.append(bbox)

        # If no valid detections, return original
        if len(valid_frames) == 0:
            return ball_positions

        # If only one detection, use it for nearby frames
        if len(valid_frames) == 1:
            result = []
            detection_frame = valid_frames[0]
            bbox = valid_bboxes[0]
            for i in range(len(ball_positions)):
                # Only use detection for frames within 5 frames
                if abs(i - detection_frame) <= 5:
                    result.append({1: {"bbox": bbox}})
                else:
                    result.append({})
            return result

        # Build result with linear interpolation between detections
        result = []
        last_valid_idx = 0
        last_valid_bbox = valid_bboxes[0]

        for i in range(len(ball_positions)):
            if i in valid_frames:
                # Use actual detection
                idx = valid_frames.index(i)
                result.append({1: {"bbox": valid_bboxes[idx]}})
                last_valid_idx = i
                last_valid_bbox = valid_bboxes[idx]
            else:
                # Find next valid detection
                next_valid_idx = None
                next_valid_bbox = None
                for vf, vb in zip(valid_frames, valid_bboxes):
                    if vf > i:
                        next_valid_idx = vf
                        next_valid_bbox = vb
                        break

                if next_valid_idx is not None and (next_valid_idx - last_valid_idx) <= 10:
                    # Interpolate between last and next valid
                    alpha = (i - last_valid_idx) / (next_valid_idx - last_valid_idx)
                    interp_bbox = [
                        last_valid_bbox[0] + alpha * (next_valid_bbox[0] - last_valid_bbox[0]),
                        last_valid_bbox[1] + alpha * (next_valid_bbox[1] - last_valid_bbox[1]),
                        last_valid_bbox[2] + alpha * (next_valid_bbox[2] - last_valid_bbox[2]),
                        last_valid_bbox[3] + alpha * (next_valid_bbox[3] - last_valid_bbox[3])
                    ]
                    result.append({1: {"bbox": interp_bbox}})
                elif (i - last_valid_idx) <= 5:
                    # Use last valid if within 5 frames
                    result.append({1: {"bbox": last_valid_bbox}})
                else:
                    result.append({})

        return result

    def detect_frames(self, frames):
        batch_size=20 
        detections = [] 
        for i in range(0,len(frames),batch_size):
            detections_batch = self.model.predict(frames[i:i+batch_size],conf=0.1)
            detections += detections_batch
        return detections

    def get_object_tracks(self, frames, read_from_stub=False, stub_path=None):

        if read_from_stub and stub_path is not None and os.path.exists(stub_path):
            with open(stub_path,'rb') as f:
                tracks = pickle.load(f)
            return tracks

        detections = self.detect_frames(frames)

        tracks={
            "players":[],
            "referees":[],
            "ball":[]
        }

        for frame_num, detection in enumerate(detections):
            cls_names = detection.names
            cls_names_inv = {v:k for k,v in cls_names.items()}

            # Covert to supervision Detection format
            detection_supervision = sv.Detections.from_ultralytics(detection)

            # Convert GoalKeeper to player object (for fine-tuned model)
            for object_ind , class_id in enumerate(detection_supervision.class_id):
                if cls_names[class_id] == "goalkeeper":
                    if "player" in cls_names_inv:
                        detection_supervision.class_id[object_ind] = cls_names_inv["player"]

            # Track Objects
            detection_with_tracks = self.tracker.update_with_detections(detection_supervision)

            tracks["players"].append({})
            tracks["referees"].append({})
            tracks["ball"].append({})

            # Get class IDs - support both COCO and fine-tuned models
            # COCO: person=0, sports ball=32
            # Fine-tuned: player=0, ball=1, goalkeeper=2, referee=3
            player_cls_id = cls_names_inv.get('player') or cls_names_inv.get('person')
            referee_cls_id = cls_names_inv.get('referee')
            ball_cls_id = cls_names_inv.get('ball') or cls_names_inv.get('sports ball')

            for frame_detection in detection_with_tracks:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]
                track_id = frame_detection[4]

                if player_cls_id is not None and cls_id == player_cls_id:
                    tracks["players"][frame_num][track_id] = {"bbox":bbox}

                if referee_cls_id is not None and cls_id == referee_cls_id:
                    tracks["referees"][frame_num][track_id] = {"bbox":bbox}

            for frame_detection in detection_supervision:
                bbox = frame_detection[0].tolist()
                cls_id = frame_detection[3]

                if ball_cls_id is not None and cls_id == ball_cls_id:
                    tracks["ball"][frame_num][1] = {"bbox":bbox}

        if stub_path is not None:
            with open(stub_path,'wb') as f:
                pickle.dump(tracks,f)

        return tracks
    
    def draw_ellipse(self,frame,bbox,color,track_id=None):
        y2 = int(bbox[3])
        x_center, _ = get_center_of_bbox(bbox)
        width = get_bbox_width(bbox)

        cv2.ellipse(
            frame,
            center=(x_center,y2),
            axes=(int(width), int(0.35*width)),
            angle=0.0,
            startAngle=-45,
            endAngle=235,
            color = color,
            thickness=2,
            lineType=cv2.LINE_4
        )

        rectangle_width = 40
        rectangle_height=20
        x1_rect = x_center - rectangle_width//2
        x2_rect = x_center + rectangle_width//2
        y1_rect = (y2- rectangle_height//2) +15
        y2_rect = (y2+ rectangle_height//2) +15

        if track_id is not None:
            cv2.rectangle(frame,
                          (int(x1_rect),int(y1_rect) ),
                          (int(x2_rect),int(y2_rect)),
                          color,
                          cv2.FILLED)
            
            x1_text = x1_rect+12
            if track_id > 99:
                x1_text -=10
            
            cv2.putText(
                frame,
                f"{track_id}",
                (int(x1_text),int(y1_rect+15)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0,0,0),
                2
            )

        return frame

    def draw_traingle(self,frame,bbox,color, track_id=None):
        # Utiliser le centre de la bbox pour un meilleur positionnement
        x, y_center = get_center_of_bbox(bbox)
        y = int(y_center)  # Centre vertical au lieu du haut

        triangle_points = np.array([
            [x,y],           # Pointe du triangle au centre
            [x-10,y-15],     # Base gauche
            [x+10,y-15],     # Base droite
        ])
        cv2.drawContours(frame, [triangle_points],0,color, cv2.FILLED)
        cv2.drawContours(frame, [triangle_points],0,(0,0,0), 2)

        return frame

    def draw_team_ball_control(self, frame, frame_num, team_ball_control):
        # Affichage avec noms d'équipe basés sur les couleurs
        team_ball_control_till_frame = team_ball_control[:frame_num+1]

        if len(team_ball_control_till_frame) == 0:
            return frame

        # Get the number of time each team had ball control
        team_1_num_frames = (team_ball_control_till_frame == 1).sum()
        team_2_num_frames = (team_ball_control_till_frame == 2).sum()
        total = team_1_num_frames + team_2_num_frames

        if total == 0:
            return frame

        team_1_pct = team_1_num_frames / total * 100
        team_2_pct = team_2_num_frames / total * 100

        # Fond semi-transparent pour la lisibilité
        overlay = frame.copy()
        cv2.rectangle(overlay, (1350, 850), (1920, 980), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Team Rouge (Team A)
        cv2.putText(frame, f"Team Rouge (A): {team_1_pct:.1f}%", (1380, 900),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        # Team Bleue (Team B)
        cv2.putText(frame, f"Team Bleue (B): {team_2_pct:.1f}%", (1380, 950),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

        return frame

    def draw_annotations(self,video_frames, tracks,team_ball_control, player_speeds=None):
        output_video_frames= []

        # Couleurs fixes pour les équipes (Team A = Rouge, Team B = Bleu)
        TEAM_COLORS = {
            1: (0, 0, 255),    # Rouge en BGR
            2: (255, 0, 0),    # Bleu en BGR
        }

        # Mapper les track_id à des numéros de maillot 1-26
        player_number_map = {}
        all_player_ids = set()
        for frame_tracks in tracks["players"]:
            all_player_ids.update(frame_tracks.keys())

        # Trier les IDs et assigner des numéros 1-26
        sorted_ids = sorted(all_player_ids)
        for idx, player_id in enumerate(sorted_ids):
            player_number_map[player_id] = (idx % 26) + 1  # Numéros 1-26 cycliques

        for frame_num, frame in enumerate(video_frames):
            frame = frame.copy()

            player_dict = tracks["players"][frame_num]
            ball_dict = tracks["ball"][frame_num]
            referee_dict = tracks["referees"][frame_num]

            # Draw Players avec couleurs d'équipe fixes et numéros 1-26
            for track_id, player in player_dict.items():
                team = player.get("team", 1)
                # Utiliser la couleur assignée dans main.py, sinon fallback sur TEAM_COLORS
                color = player.get("team_color", TEAM_COLORS.get(team, (0, 255, 0)))
                jersey_number = player_number_map.get(track_id, track_id)
                frame = self.draw_ellipse(frame, player["bbox"], color, jersey_number)

                if player.get('has_ball',False):
                    frame = self.draw_traingle(frame, player["bbox"], (0, 0, 255))

            # Draw Referee (jaune)
            for _, referee in referee_dict.items():
                frame = self.draw_ellipse(frame, referee["bbox"], (0, 255, 255))

            # Draw ball - cercle au lieu de triangle pour plus de visibilité
            for track_id, ball in ball_dict.items():
                bbox = ball.get("bbox", [])
                if len(bbox) == 4 and all(bbox):
                    # Dessiner un cercle au centre de la balle
                    x, y = get_center_of_bbox(bbox)
                    cv2.circle(frame, (int(x), int(y)), 8, (0, 255, 0), -1)  # Cercle plein vert
                    cv2.circle(frame, (int(x), int(y)), 10, (0, 0, 0), 2)    # Bordure noire

            # Draw Team Ball Control avec noms d'équipe basés sur les couleurs
            frame = self.draw_team_ball_control(frame, frame_num, team_ball_control)

            # Draw speed ranking si disponible
            if player_speeds and frame_num == 0:  # Afficher sur la première frame
                frame = self.draw_speed_ranking(frame, player_speeds)

            output_video_frames.append(frame)

        return output_video_frames

    def draw_speed_ranking(self, frame, player_speeds):
        """Affiche le classement des joueurs par vitesse"""
        # Trier par vitesse décroissante
        sorted_speeds = sorted(player_speeds.items(), key=lambda x: x[1], reverse=True)

        # Afficher top 5
        y_start = 100
        cv2.putText(frame, "TOP SPEEDS:", (50, y_start), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        for i, (player_id, speed) in enumerate(sorted_speeds[:5]):
            y_pos = y_start + 30 + (i * 25)
            text = f"#{player_id}: {speed:.1f} km/h"
            cv2.putText(frame, text, (50, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return frame