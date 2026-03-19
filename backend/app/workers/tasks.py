# ============================================
# CELERY TASKS - BL Genius
# Tâches asynchrones pour le traitement vidéo
# ============================================

import os
import sys
from pathlib import Path
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ajout du répertoire parent au path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.database import SessionLocal
from app.models.video import Video

# Import des modules de tracking
from trackers.tracker import Tracker
from team_assigner.team_assigner import TeamAssigner
from player_ball_assigner.player_ball_assigner import PlayerBallAssigner
from camera_movement_estimator.camera_movement_estimator import CameraMovementEstimator
from view_transformer.view_transformer import ViewTransformer
from speed_and_distance_estimator.speed_and_distance_estimator import SpeedAndDistance_Estimator as SpeedAndDistanceEstimator
from utils.video_utils import read_video, save_video

# Configuration
VIDEO_OUTPUT_DIR = Path(os.getenv('VIDEO_OUTPUT_DIR', '/app/data/videos'))
MODELS_DIR = Path('/app/models')
YOLO_MODEL = os.getenv('YOLO_MODEL_PATH', 'yolov8m.pt')


@shared_task(bind=True, max_retries=3, soft_time_limit=3300, time_limit=3600)
def process_video(self, video_id: str):
    """
    Tâche Celery principale pour analyser une vidéo

    Args:
        video_id: L'identifiant de la vidéo à traiter

    Returns:
        dict: Résultats de l'analyse
    """
    db = SessionLocal()

    try:
        # Récupération des informations de la vidéo
        video = db.query(Video).filter(Video.task_id == video_id).first()

        if not video:
            raise Exception(f"Vidéo {video_id} non trouvée en base de données")

        logger.info(f"🎬 Démarrage analyse vidéo: {video_id}")

        # Mise à jour du statut
        video.status = 'processing'
        db.commit()

        # Chemin de la vidéo
        input_path = video.storage_path
        output_path = VIDEO_OUTPUT_DIR / 'processed' / f"{video_id}_analyzed.mp4"

        if not Path(input_path).exists():
            raise Exception(f"Fichier vidéo non trouvé: {input_path}")

        # =====================================================
        # ÉTAPE 1: Lecture de la vidéo
        # =====================================================
        logger.info(f"📖 Lecture de la vidéo: {input_path}")
        video_frames = read_video(input_path)
        logger.info(f"✅ {len(video_frames)} frames lus")

        self.update_state(
            state='PROGRESS',
            meta={'current': 1, 'total': 10, 'status': 'Lecture terminée'}
        )

        # =====================================================
        # ÉTAPE 2: Tracking YOLO
        # =====================================================
        logger.info("🔍 Tracking des objets...")
        model_path = str(MODELS_DIR / "best.pt") if (MODELS_DIR / "best.pt").exists() else YOLO_MODEL
        tracker = Tracker(model_path)

        tracks = tracker.get_object_tracks(
            video_frames,
            read_from_stub=False,
            stub_path=str(VIDEO_OUTPUT_DIR / 'stubs' / f"{video_id}_tracks.pkl")
        )
        logger.info("✅ Tracking terminé")

        self.update_state(
            state='PROGRESS',
            meta={'current': 3, 'total': 10, 'status': 'Tracking terminé'}
        )

        # =====================================================
        # ÉTAPE 3: Interpolation du ballon (AVANT d'ajouter les positions)
        # =====================================================
        logger.info("🎯 Interpolation du ballon...")
        tracks["ball"] = tracker.interpolate_ball_positions(tracks["ball"])
        logger.info("✅ Interpolation du ballon terminée")

        # PUIS ajouter les positions à tous les tracks
        tracker.add_position_to_tracks(tracks)

        # =====================================================
        # ÉTAPE 4: Estimation mouvement caméra
        # =====================================================
        logger.info("📹 Estimation du mouvement de caméra...")
        camera_estimator = CameraMovementEstimator(video_frames[0])
        camera_movements = camera_estimator.get_camera_movement(
            video_frames,
            read_from_stub=False,
            stub_path=str(VIDEO_OUTPUT_DIR / 'stubs' / f"{video_id}_camera.pkl")
        )
        camera_estimator.add_adjust_positions_to_tracks(tracks, camera_movements)
        logger.info("✅ Mouvement de caméra estimé")

        self.update_state(
            state='PROGRESS',
            meta={'current': 5, 'total': 10, 'status': 'Mouvement caméra estimé'}
        )

        # =====================================================
        # ÉTAPE 5: Transformation de perspective
        # =====================================================
        logger.info("🗺️ Transformation de perspective...")
        view_transformer = ViewTransformer()
        view_transformer.add_transformed_position_to_tracks(tracks)
        logger.info("✅ Transformation de perspective appliquée")

        self.update_state(
            state='PROGRESS',
            meta={'current': 6, 'total': 10, 'status': 'Perspective transformée'}
        )

        # =====================================================
        # ÉTAPE 6: Calcul vitesse et distance
        # =====================================================
        logger.info("⚡ Calcul de la vitesse et distance...")
        speed_estimator = SpeedAndDistanceEstimator()
        speed_estimator.add_speed_and_distance_to_tracks(tracks)
        logger.info("✅ Vitesse et distance calculées")

        self.update_state(
            state='PROGRESS',
            meta={'current': 7, 'total': 10, 'status': 'Vitesse calculée'}
        )

        # =====================================================
        # ÉTAPE 7: Assignation des équipes
        # =====================================================
        logger.info("🏃 Assignation des équipes...")
        team_assigner = TeamAssigner()
        team_assigner.assign_team_color(video_frames[0], tracks['players'][0])

        for frame_num, player_track in enumerate(tracks['players']):
            for player_id, track in player_track.items():
                team = team_assigner.get_player_team(
                    video_frames[frame_num],
                    track['bbox'],
                    player_id
                )
                tracks['players'][frame_num][player_id]['team'] = team
                tracks['players'][frame_num][player_id]['team_color'] = team_assigner.team_colors[team]

        logger.info("✅ Équipes assignées")

        self.update_state(
            state='PROGRESS',
            meta={'current': 8, 'total': 10, 'status': 'Équipes assignées'}
        )

        # =====================================================
        # ÉTAPE 8: Assignation du contrôle du ballon
        # =====================================================
        logger.info("⚽ Assignation du contrôle du ballon...")
        player_assigner = PlayerBallAssigner()
        team_ball_control = []

        for frame_num, player_track in enumerate(tracks['players']):
            ball_bbox = tracks['ball'][frame_num][1]['bbox']

            # Utiliser la position transformée du ballon si disponible (plus précis)
            ball_position_transformed = None
            if 'position_transformed' in tracks['ball'][frame_num][1]:
                ball_position_transformed = tracks['ball'][frame_num][1]['position_transformed']
                logger.debug(f"Frame {frame_num}: Ball position transformed: {ball_position_transformed}")

            # Assigner le ballon au joueur le plus proche (avec coordonnées terrain si dispo)
            assigned_player = player_assigner.assign_ball_to_player(
                player_track,
                ball_bbox,
                ball_position_transformed=ball_position_transformed
            )

            if assigned_player != -1:
                tracks['players'][frame_num][assigned_player]['has_ball'] = True
                team_ball_control.append(tracks['players'][frame_num][assigned_player]['team'])
            else:
                if team_ball_control:
                    team_ball_control.append(team_ball_control[-1])
                else:
                    team_ball_control.append(1)

        import numpy as np
        team_ball_control = np.array(team_ball_control)
        logger.info("✅ Contrôle du ballon assigné")

        self.update_state(
            state='PROGRESS',
            meta={'current': 9, 'total': 10, 'status': 'Contrôle ballon assigné'}
        )

        # =====================================================
        # ÉTAPE 9: Génération de la vidéo annotée
        # =====================================================
        logger.info("🎨 Annotation des frames...")
        output_video_frames = tracker.draw_annotations(video_frames, tracks, team_ball_control)
        output_video_frames = camera_estimator.draw_camera_movement(output_video_frames, camera_movements)
        output_video_frames = speed_estimator.draw_speed_and_distance(output_video_frames, tracks)

        # Création du répertoire de sortie
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Sauvegarde de la vidéo
        save_video(output_video_frames, str(output_path))
        logger.info(f"✅ Vidéo sauvegardée: {output_path}")

        # =====================================================
        # Mise à jour BDD
        # =====================================================
        video.status = 'completed'
        video.output_path = str(output_path)
        video.analysis_result = {
            'total_frames': len(video_frames),
            'total_players': sum(len(f) for f in tracks['players']),
            'possession_team1': float((team_ball_control == 1).sum() / len(team_ball_control) * 100),
            'possession_team2': float((team_ball_control == 2).sum() / len(team_ball_control) * 100),
            'processing_time': 'completed'
        }
        db.commit()

        logger.info(f"✅ Analyse terminée pour {video_id}")

        return {
            'status': 'success',
            'video_id': video_id,
            'output_path': str(output_path),
            'stats': video.analysis_result
        }

    except SoftTimeLimitExceeded:
        logger.error(f"⏱️ Timeout pour la vidéo {video_id}")
        video.status = 'error'
        video.analysis_result = {'error': 'Timeout - traitement trop long'}
        db.commit()
        raise

    except Exception as exc:
        logger.error(f"❌ Erreur lors de l'analyse de {video_id}: {exc}")

        # Mise à jour du statut d'erreur
        try:
            video.status = 'error'
            video.analysis_result = {'error': str(exc)}
            db.commit()
        except:
            pass

        # Retry si possible
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retry {self.request.retries + 1}/{self.max_retries} pour {video_id}")
            raise self.retry(exc=exc, countdown=60)
        else:
            logger.error(f"❌ Échec définitif pour {video_id}")
            raise

    finally:
        db.close()


@shared_task
def cleanup_old_videos(days: int = 7):
    """
    Tâche de nettoyage des vieilles vidéos

    Args:
        days: Nombre de jours avant suppression
    """
    logger.info(f"🧹 Nettoyage des vidéos de plus de {days} jours")
    # Implémentation du nettoyage...
    pass


@shared_task
def generate_stats_report(video_id: str):
    """
    Génère un rapport de statistiques détaillé

    Args:
        video_id: ID de la vidéo
    """
    logger.info(f"📊 Génération du rapport pour {video_id}")
    # Implémentation de la génération de rapport...
    pass
