"""Video processing utilities for frame extraction.

This module provides functionality to extract key frames from video files
for analysis by the Vision_Model.
"""
import base64
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class VideoFrame:
    """Represents an extracted video frame."""
    frame_number: int
    timestamp_seconds: float
    image_data: bytes  # Raw image bytes (JPEG encoded)
    
    @property
    def base64_data(self) -> str:
        """Get base64 encoded image data."""
        return base64.b64encode(self.image_data).decode('utf-8')


class VideoProcessor:
    """Extracts key frames from video files for AI analysis."""
    
    def __init__(
        self,
        max_frames: int = 5,
        frame_quality: int = 85,
        min_frame_interval: float = 2.0
    ):
        """
        Initialize the video processor.
        
        Args:
            max_frames: Maximum number of frames to extract (default 5).
            frame_quality: JPEG quality for extracted frames (1-100, default 85).
            min_frame_interval: Minimum seconds between extracted frames (default 2.0).
        """
        self.max_frames = max_frames
        self.frame_quality = frame_quality
        self.min_frame_interval = min_frame_interval
        self._cv2_available = self._check_cv2_available()
    
    def _check_cv2_available(self) -> bool:
        """Check if OpenCV is available."""
        try:
            import cv2
            return True
        except ImportError:
            logger.warning(
                "OpenCV (cv2) not available. Video frame extraction will be disabled. "
                "Install with: pip install opencv-python"
            )
            return False
    
    @property
    def is_available(self) -> bool:
        """Check if video processing is available."""
        return self._cv2_available
    
    def extract_frames(
        self,
        video_data: Union[bytes, str],
        filename: str = ""
    ) -> Tuple[List[VideoFrame], Optional[str]]:
        """
        Extract key frames from a video.
        
        Args:
            video_data: Video file bytes or path to video file.
            filename: Original filename for logging.
            
        Returns:
            Tuple of (list of VideoFrame objects, error message or None).
        """
        if not self._cv2_available:
            return [], "Video processing unavailable: OpenCV not installed"
        
        import cv2
        import numpy as np
        
        # Handle video data - write to temp file if bytes
        temp_file = None
        video_path = None
        
        try:
            if isinstance(video_data, bytes):
                # Write bytes to temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix='.mp4', delete=False
                )
                temp_file.write(video_data)
                temp_file.close()
                video_path = temp_file.name
            else:
                video_path = video_data
            
            # Open video file
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                return [], f"Failed to open video file: {filename}"
            
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(
                f"Processing video: {filename}, "
                f"frames={total_frames}, fps={fps:.2f}, duration={duration:.2f}s"
            )
            
            if total_frames == 0 or fps == 0:
                cap.release()
                return [], f"Invalid video file: {filename}"
            
            # Calculate frame positions to extract
            frame_positions = self._calculate_frame_positions(
                total_frames, fps, duration
            )
            
            # Extract frames
            frames = []
            for frame_num in frame_positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()
                
                if ret:
                    # Encode frame as JPEG
                    encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.frame_quality]
                    _, buffer = cv2.imencode('.jpg', frame, encode_params)
                    
                    timestamp = frame_num / fps
                    
                    frames.append(VideoFrame(
                        frame_number=frame_num,
                        timestamp_seconds=timestamp,
                        image_data=buffer.tobytes()
                    ))
                    
                    logger.debug(
                        f"Extracted frame {frame_num} at {timestamp:.2f}s"
                    )
            
            cap.release()
            
            if not frames:
                return [], f"No frames could be extracted from: {filename}"
            
            logger.info(f"Extracted {len(frames)} frames from {filename}")
            return frames, None
            
        except Exception as e:
            logger.error(f"Video frame extraction failed: {e}")
            return [], f"Video processing error: {str(e)}"
            
        finally:
            # Clean up temp file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception:
                    pass
    
    def _calculate_frame_positions(
        self,
        total_frames: int,
        fps: float,
        duration: float
    ) -> List[int]:
        """
        Calculate which frame positions to extract.
        
        Distributes frames evenly across the video duration,
        respecting the minimum interval between frames.
        
        Args:
            total_frames: Total number of frames in video.
            fps: Frames per second.
            duration: Video duration in seconds.
            
        Returns:
            List of frame numbers to extract.
        """
        if duration <= 0 or total_frames <= 0:
            return []
        
        # Calculate how many frames we can extract given min interval
        max_possible = int(duration / self.min_frame_interval) + 1
        num_frames = min(self.max_frames, max_possible, total_frames)
        
        if num_frames <= 1:
            # Just get the middle frame
            return [total_frames // 2]
        
        # Distribute frames evenly, avoiding first and last few frames
        # Start at 5% and end at 95% of the video
        start_frame = int(total_frames * 0.05)
        end_frame = int(total_frames * 0.95)
        
        if end_frame <= start_frame:
            start_frame = 0
            end_frame = total_frames - 1
        
        frame_range = end_frame - start_frame
        
        if num_frames == 1:
            return [(start_frame + end_frame) // 2]
        
        # Calculate evenly spaced positions
        positions = []
        for i in range(num_frames):
            pos = start_frame + int(frame_range * i / (num_frames - 1))
            positions.append(min(pos, total_frames - 1))
        
        return positions


# Global video processor instance
video_processor = VideoProcessor()
