import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Multi-frame voting: number of samples before finalizing a player's team
N_VOTES = 5

# If a player's color is farther than this from BOTH team centroids → referee
REFEREE_DISTANCE_THRESHOLD = 55.0


class TeamAssigner:
    """
    Assigns players to teams based on jersey color, with referee detection.

    Pipeline:
    1. _extract_jersey_color(): tight torso crop → K-Means k=2 → largest cluster = jersey
    2. assign_team_color(): calibrate 2 team centroids from sampled frames
    3. classify_all_players(): multi-frame voting for each player (5 samples)
       - If color far from both centroids → referee (team 0)
    4. get_player_team(): returns cached result
    """

    def __init__(self):
        self.team_colors = {}          # {0: yellow (referee), 1: BGR, 2: BGR}
        self.player_team_dict = {}     # finalized player_id -> team_id
        self.kmeans = None             # trained k=2 model

    # ------------------------------------------------------------------
    # Per-player jersey color extraction
    # ------------------------------------------------------------------
    def _extract_jersey_color(self, frame, bbox):
        """
        Extract dominant jersey color (HSV) from tight upper-torso crop.
        No grass masking — tight crop is almost entirely jersey.
        K-Means k=2 separates jersey from skin; returns largest cluster.
        """
        x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
        fh, fw = frame.shape[:2]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(fw, x2), min(fh, y2)

        player_img = frame[y1:y2, x1:x2]
        if player_img.size == 0:
            return None

        ph, pw = player_img.shape[:2]
        if ph < 10 or pw < 6:
            return None

        # Tight upper-torso: 15-45% vertical, 25-75% horizontal
        torso = player_img[int(ph * 0.15):int(ph * 0.45), int(pw * 0.25):int(pw * 0.75)]

        if torso.size == 0 or torso.shape[0] < 3 or torso.shape[1] < 3:
            return None

        hsv_pixels = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV).reshape(-1, 3).astype(np.float64)

        if len(hsv_pixels) < 10:
            return np.mean(hsv_pixels, axis=0)

        km = KMeans(n_clusters=2, init="k-means++", n_init=1, random_state=42)
        km.fit(hsv_pixels)
        counts = np.bincount(km.labels_)
        return km.cluster_centers_[np.argmax(counts)]

    # ------------------------------------------------------------------
    # Calibration: detect the 2 team colors
    # ------------------------------------------------------------------
    def assign_team_color(self, frame_or_frames, detections_or_tracks, n_calibration_frames=10):
        """Calibrate 2 team colors from sampled frames."""
        if isinstance(frame_or_frames, list):
            frames = frame_or_frames
            player_tracks = detections_or_tracks
        else:
            frames = [frame_or_frames]
            player_tracks = [detections_or_tracks]

        total = len(frames)
        if total == 0:
            return

        indices = np.linspace(0, total - 1, min(n_calibration_frames, total), dtype=int)

        all_colors = []
        for idx in indices:
            if idx >= len(player_tracks):
                continue
            frame = frames[idx]
            detections = player_tracks[idx]
            for pid, det in detections.items():
                bbox = det.get("bbox", [])
                if len(bbox) < 4:
                    continue
                bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
                if bw < 20 or bh < 40:
                    continue
                color = self._extract_jersey_color(frame, bbox)
                if color is not None:
                    all_colors.append(color)

        logger.info(f"Team calibration: {len(all_colors)} player color samples")

        if len(all_colors) < 4:
            logger.warning("Not enough color samples for team calibration")
            return

        colors = np.array(all_colors)

        # Referee filtering: k=3, remove smallest cluster if < 20%
        if len(colors) >= 8:
            km3 = KMeans(n_clusters=3, init="k-means++", n_init=10, random_state=42)
            km3.fit(colors)
            counts = np.bincount(km3.labels_, minlength=3)
            smallest = np.argmin(counts)
            if counts[smallest] < 0.20 * len(colors):
                c = km3.cluster_centers_[smallest]
                logger.info(
                    f"Removing referee cluster ({counts[smallest]}/{len(colors)} samples, "
                    f"HSV: H={c[0]:.0f} S={c[1]:.0f} V={c[2]:.0f})"
                )
                colors = colors[km3.labels_ != smallest]

        if len(colors) < 4:
            return

        # k=2 for the 2 teams
        self.kmeans = KMeans(n_clusters=2, init="k-means++", n_init=10, random_state=42)
        self.kmeans.fit(colors)

        c1, c2 = self.kmeans.cluster_centers_
        logger.info(f"Team 1 centroid HSV: H={c1[0]:.0f} S={c1[1]:.0f} V={c1[2]:.0f}")
        logger.info(f"Team 2 centroid HSV: H={c2[0]:.0f} S={c2[1]:.0f} V={c2[2]:.0f}")

        # Display colors
        self.team_colors[0] = (0, 255, 255)  # Referee = yellow BGR
        for team_id, centroid in [(1, c1), (2, c2)]:
            boosted = centroid.copy()
            boosted[1] = min(255, boosted[1] * 1.4)
            boosted[2] = min(255, max(80, boosted[2] * 1.1))
            pixel_hsv = np.uint8([[[
                int(np.clip(boosted[0], 0, 179)),
                int(np.clip(boosted[1], 0, 255)),
                int(np.clip(boosted[2], 0, 255))
            ]]])
            bgr = cv2.cvtColor(pixel_hsv, cv2.COLOR_HSV2BGR)[0][0]
            self.team_colors[team_id] = tuple(int(c) for c in bgr)

        logger.info(f"Team 1 display BGR: {self.team_colors[1]}")
        logger.info(f"Team 2 display BGR: {self.team_colors[2]}")

    # ------------------------------------------------------------------
    # Pre-classify all players with multi-frame voting + referee detection
    # ------------------------------------------------------------------
    def classify_all_players(self, frames, player_tracks):
        """
        Pre-classify every player using multi-frame voting.
        For each player, sample up to N_VOTES frames, extract jersey color,
        vote team 1/2 or referee (0). Majority wins.
        """
        if self.kmeans is None:
            logger.warning("Cannot classify players: no team model calibrated")
            return

        # Collect all appearances per player: {pid: [(frame_idx, bbox), ...]}
        player_appearances = {}
        for frame_num, detections in enumerate(player_tracks):
            for pid, det in detections.items():
                bbox = det.get("bbox", [])
                if len(bbox) < 4:
                    continue
                if pid not in player_appearances:
                    player_appearances[pid] = []
                player_appearances[pid].append((frame_num, bbox))

        n_referees = 0
        n_team1 = 0
        n_team2 = 0

        for pid, appearances in player_appearances.items():
            # Sample up to N_VOTES spread appearances
            n_sample = min(N_VOTES, len(appearances))
            sample_indices = np.linspace(0, len(appearances) - 1, n_sample, dtype=int)

            votes = []
            for si in sample_indices:
                frame_num, bbox = appearances[si]
                # Skip tiny bboxes
                bw, bh = bbox[2] - bbox[0], bbox[3] - bbox[1]
                if bw < 15 or bh < 30:
                    continue

                color = self._extract_jersey_color(frames[frame_num], bbox)
                if color is None:
                    continue

                # Check if referee: color far from both team centroids
                d1 = np.linalg.norm(color - self.kmeans.cluster_centers_[0])
                d2 = np.linalg.norm(color - self.kmeans.cluster_centers_[1])

                if min(d1, d2) > REFEREE_DISTANCE_THRESHOLD:
                    votes.append(0)  # referee
                else:
                    label = self.kmeans.predict(color.reshape(1, -1))[0]
                    votes.append(int(label) + 1)

            if votes:
                final_team = Counter(votes).most_common(1)[0][0]
            else:
                final_team = 1  # fallback

            self.player_team_dict[pid] = final_team

            if final_team == 0:
                n_referees += 1
            elif final_team == 1:
                n_team1 += 1
            else:
                n_team2 += 1

        logger.info(
            f"Player classification: {n_team1} team 1, {n_team2} team 2, "
            f"{n_referees} referees (total {len(player_appearances)} players)"
        )

    # ------------------------------------------------------------------
    # Assign a player to a team (uses cache from classify_all_players)
    # ------------------------------------------------------------------
    def get_player_team(self, frame, player_bbox, player_id):
        # Return cached result (set by classify_all_players or previous call)
        if player_id in self.player_team_dict:
            return self.player_team_dict[player_id]

        # Fallback for players not pre-classified
        if self.kmeans is None:
            team_id = 1 if player_id % 2 == 0 else 2
            self.player_team_dict[player_id] = team_id
            return team_id

        color = self._extract_jersey_color(frame, player_bbox)
        if color is None:
            team_id = 1
        else:
            d1 = np.linalg.norm(color - self.kmeans.cluster_centers_[0])
            d2 = np.linalg.norm(color - self.kmeans.cluster_centers_[1])
            if min(d1, d2) > REFEREE_DISTANCE_THRESHOLD:
                team_id = 0  # referee
            else:
                label = self.kmeans.predict(color.reshape(1, -1))[0]
                team_id = int(label) + 1

        self.player_team_dict[player_id] = team_id
        return team_id

    def get_team_display_color(self, team_id):
        """Return BGR display color. Team 0 = referee (yellow)."""
        return self.team_colors.get(team_id, (0, 255, 0))
