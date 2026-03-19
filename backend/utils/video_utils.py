import cv2
import subprocess
import os
from pathlib import Path

def read_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def save_video(output_video_frames, output_video_path, fps=24):
    """
    Sauvegarde une vidéo en utilisant FFmpeg pour encoder en H.264 (compatibilité navigateur).
    Fallback sur VideoWriter si FFmpeg échoue.
    """
    if not output_video_frames:
        print("❌ No frames to save")
        return False

    output_path = Path(output_video_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Dimensions
    height, width = output_video_frames[0].shape[:2]

    # Essayer d'abord avec FFmpeg pour H.264
    try:
        # Créer un fichier temporaire avec les frames en raw
        temp_dir = output_path.parent / "temp_frames"
        temp_dir.mkdir(exist_ok=True)

        # Sauvegarder les frames temporairement
        for i, frame in enumerate(output_video_frames):
            frame_file = temp_dir / f"frame_{i:06d}.png"
            cv2.imwrite(str(frame_file), frame)

        # Utiliser FFmpeg pour encoder en H.264
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-framerate', str(fps),
            '-i', str(temp_dir / 'frame_%06d.png'),
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',  # Compatibilité navigateur
            '-preset', 'fast',
            '-crf', '23',
            '-movflags', '+faststart',  # Pour le streaming
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        # Nettoyer les fichiers temporaires
        for f in temp_dir.glob('*.png'):
            f.unlink()
        temp_dir.rmdir()

        if result.returncode == 0:
            print(f"✅ Video saved with H.264: {output_path}")
            return True
        else:
            print(f"⚠️ FFmpeg failed, falling back to mp4v: {result.stderr[:200]}")

    except Exception as e:
        print(f"⚠️ FFmpeg error, falling back to mp4v: {e}")

    # Fallback: utiliser mp4v (moins compatible mais fonctionne)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    if not out.isOpened():
        print(f"❌ Failed to open VideoWriter")
        return False

    for frame in output_video_frames:
        out.write(frame)
    out.release()

    print(f"✅ Video saved with mp4v (fallback): {output_path}")
    return True
