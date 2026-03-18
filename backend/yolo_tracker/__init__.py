import torch
import warnings

# Patch torch.load pour PyTorch 2.6+ - désactiver weights_only par défaut
# car les modèles YOLO contiennent de nombreuses classes personnalisées
_original_torch_load = torch.load

def patched_torch_load(*args, **kwargs):
    if 'weights_only' not in kwargs:
        kwargs['weights_only'] = False
    return _original_torch_load(*args, **kwargs)

torch.load = patched_torch_load

# Supprimer les avertissements liés à weights_only
warnings.filterwarnings('ignore', message='.*weights_only.*', category=UserWarning)

from .tracker import FootballTracker
from .team_assigner import TeamAssigner
from .ball_interpolator import BallInterpolator
from .camera_movement_estimator import CameraMovementEstimator
from .perspective_transformer import PerspectiveTransformer
from .speed_calculator import SpeedCalculator
from .jersey_number_detector import JerseyNumberDetector

__all__ = [
    'FootballTracker',
    'TeamAssigner',
    'BallInterpolator',
    'CameraMovementEstimator',
    'PerspectiveTransformer',
    'SpeedCalculator',
    'JerseyNumberDetector'
]
