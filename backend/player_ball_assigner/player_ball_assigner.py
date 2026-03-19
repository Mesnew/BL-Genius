import sys
sys.path.append('../')
import numpy as np
from utils import get_center_of_bbox, measure_distance


class PlayerBallAssigner():
    """
    Realistic ball possession assignment with hysteresis.

    Rules:
    - Only field players (team 1 or 2) can possess the ball
    - Referees (team 0) and off-field people (no position_transformed) are excluded
    - Sticky possession: current holder keeps ball unless another player is clearly closer
    - Ball in transit (far from everyone): no possession change, keep last team
    """

    def __init__(self):
        # Ground-based thresholds (meters on real field)
        self.acquire_distance = 2.5     # Max distance to GET the ball (new possession)
        self.keep_distance = 4.0        # Current holder loses ball if farther than this
        self.steal_distance = 1.5       # Another player must be THIS close to steal

        # Pixel-based thresholds (fallback when no field transform)
        self.acquire_distance_px = 100
        self.keep_distance_px = 160
        self.steal_distance_px = 50

        # Persistent state across frames
        self._current_holder = -1

    def assign_ball_to_player(self, players, ball_bbox, ball_position_transformed=None):
        """
        Assign ball to the player who realistically possesses it.

        Args:
            players: dict {player_id: {bbox, team, position_transformed, ...}}
            ball_bbox: [x1, y1, x2, y2] of the ball
            ball_position_transformed: (x, y) in meters on field (optional)

        Returns:
            player_id of possessing player, or -1 if ball is free
        """
        # Filter: only field players (not referees, not off-field)
        eligible = {}
        for pid, p in players.items():
            if p.get('team', 1) == 0:
                continue  # Skip referees
            eligible[pid] = p

        if not eligible:
            return -1

        # Prefer ground-distance (real meters) if available
        if ball_position_transformed is not None:
            on_field = {
                pid: p for pid, p in eligible.items()
                if p.get('position_transformed') is not None
            }
            if on_field:
                return self._assign_ground(on_field, ball_position_transformed)

        # Fallback: pixel distance
        if ball_bbox and len(ball_bbox) == 4:
            return self._assign_pixel(eligible, ball_bbox)

        return -1

    def _assign_ground(self, players, ball_pos):
        """Assign using real-world meter distances with hysteresis."""
        # Find closest player and current holder distance
        closest_id = -1
        closest_dist = float('inf')
        holder_dist = float('inf')

        for pid, p in players.items():
            pos = p['position_transformed']
            d = np.sqrt(
                (pos[0] - ball_pos[0]) ** 2 +
                (pos[1] - ball_pos[1]) ** 2
            )
            if d < closest_dist:
                closest_dist = d
                closest_id = pid
            if pid == self._current_holder:
                holder_dist = d

        # Case 1: Current holder still on field and close enough → sticky possession
        if self._current_holder != -1 and self._current_holder in players:
            if holder_dist <= self.keep_distance:
                # Only switch if another player is much closer (steal/tackle/pass received)
                if closest_id != self._current_holder and closest_dist < self.steal_distance:
                    self._current_holder = closest_id
                    return closest_id
                # Current holder keeps ball
                return self._current_holder

        # Case 2: No holder or holder too far → try to acquire
        if closest_dist <= self.acquire_distance:
            self._current_holder = closest_id
            return closest_id

        # Case 3: Ball in transit (far from everyone) → nobody has it
        self._current_holder = -1
        return -1

    def _assign_pixel(self, players, ball_bbox):
        """Fallback: assign using pixel distances with hysteresis."""
        ball_center = get_center_of_bbox(ball_bbox)

        closest_id = -1
        closest_dist = float('inf')
        holder_dist = float('inf')

        for pid, p in players.items():
            bbox = p['bbox']
            # Distance from player feet to ball center
            d_left = measure_distance((bbox[0], bbox[3]), ball_center)
            d_right = measure_distance((bbox[2], bbox[3]), ball_center)
            d = min(d_left, d_right)

            if d < closest_dist:
                closest_dist = d
                closest_id = pid
            if pid == self._current_holder:
                holder_dist = d

        # Sticky: current holder keeps unless steal
        if self._current_holder != -1 and self._current_holder in players:
            if holder_dist <= self.keep_distance_px:
                if closest_id != self._current_holder and closest_dist < self.steal_distance_px:
                    self._current_holder = closest_id
                    return closest_id
                return self._current_holder

        # Acquire new
        if closest_dist <= self.acquire_distance_px:
            self._current_holder = closest_id
            return closest_id

        self._current_holder = -1
        return -1
