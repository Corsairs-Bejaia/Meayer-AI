import cv2
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    Utility for normalizing and enhancing document images before OCR/Analysis.
    """
    
    @staticmethod
    def preprocess(image_bytes: bytes, profile: str = "STANDARD") -> Dict[str, Any]:
        """
        Main entry point for image preprocessing.
        """
        # Load image
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

        # Apply pipeline based on profile
        if profile == "FAST":
            # Just resize if too large
            img = ImagePreprocessor.resize_to_target_dpi(img)
        elif profile == "STANDARD":
            img = ImagePreprocessor.rotate_if_needed(img, metadata)
            img = ImagePreprocessor.deskew(img, metadata)
            img = ImagePreprocessor.enhance_contrast(img)
            img = ImagePreprocessor.denoise(img)
        elif profile == "AGGRESSIVE":
            img = ImagePreprocessor.rotate_if_needed(img, metadata)
            img = ImagePreprocessor.deskew(img, metadata)
            img = ImagePreprocessor.shadow_removal(img)
            img = ImagePreprocessor.binarize(img)
            img = ImagePreprocessor.denoise(img)
            img = ImagePreprocessor.enhance_contrast(img)

        metadata["final_size"] = img.shape[:2]
        
        # Convert back to bytes for tools that need bytes
        _, buffer = cv2.imencode(".png", img)
        processed_bytes = buffer.tobytes()

        return {
            "image": img,
            "image_bytes": processed_bytes,
            "metadata": metadata
        }

    @staticmethod
    def estimate_quality(img: cv2.Mat) -> float:
        """
        Estimates image quality score (0-100) based on blur and contrast.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 1. Blur detection (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        blur_score = min(laplacian_var / 5.0, 50.0) # Cap at 50
        
        # 2. Contrast detection
        contrast_score = (gray.max() - gray.min()) / 255.0 * 50.0 # Cap at 50
        
        return float(blur_score + contrast_score)

    @staticmethod
    def rotate_if_needed(img: cv2.Mat, metadata: dict) -> cv2.Mat:
        # Simplification: rotation detection would normally use Tesseract OSD or deep learning
        # For now, we'll skip it or implement a simple orientation check
        return img

    @staticmethod
    def deskew(img: cv2.Mat, metadata: dict) -> cv2.Mat:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.bitwise_not(gray)
        thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        
        coords = np.column_stack(np.where(thresh > 0))
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
            
        return img

    @staticmethod
    def resize_to_target_dpi(img: cv2.Mat, target_width: int = 2000) -> cv2.Mat:
        h, w = img.shape[:2]
        if w > target_width:
            scale = target_width / w
            return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        return img

    @staticmethod
    def binarize(img: cv2.Mat) -> cv2.Mat:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    @staticmethod
    def denoise(img: cv2.Mat) -> cv2.Mat:
        return cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    @staticmethod
    def enhance_contrast(img: cv2.Mat) -> cv2.Mat:
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    @staticmethod
    def shadow_removal(img: cv2.Mat) -> cv2.Mat:
        rgb_planes = cv2.split(img)
        result_planes = []
        for plane in rgb_planes:
            dilated_img = cv2.dilate(plane, np.ones((7,7), np.uint8))
            bg_img = cv2.medianBlur(dilated_img, 21)
            diff_img = 255 - cv2.absdiff(plane, bg_img)
            norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
            result_planes.append(norm_img)
        return cv2.merge(result_planes)
