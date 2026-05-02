import cv2
import numpy as np
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    @staticmethod
    def preprocess(image_bytes: bytes) -> Dict[str, Any]:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Could not decode image")

        metadata = {
            "original_size": img.shape[:2],
            "was_rotated": False,
            "rotation_angle": 0.0,
            "was_deskewed": False,
            "deskew_angle": 0.0,
            "quality_score": ImagePreprocessor.estimate_quality(img)
        }

        # 1. Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 2. Deskewing
        coords = np.column_stack(np.where(gray > 0))
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        if abs(angle) > 0.5:
            (h, w) = img.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            metadata["was_deskewed"] = True
            metadata["deskew_angle"] = angle

        # 3. Resizing if too small
        if img.shape[1] < 1000:
            scale = 1000 / img.shape[1]
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

        _, buffer = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        processed_bytes = buffer.tobytes()

        return {
            "image": img,
            "bytes": processed_bytes,
            "metadata": metadata
        }

    @staticmethod
    def estimate_quality(img: np.ndarray) -> float:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        # Scale variance to a 0-1 score (simple heuristic)
        return min(1.0, variance / 1000.0)
