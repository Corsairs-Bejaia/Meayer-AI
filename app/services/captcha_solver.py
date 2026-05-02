import io
import logging
import pytesseract
from PIL import Image, ImageOps, ImageFilter
from app.config import settings

logger = logging.getLogger(__name__)

async def solve_captcha(image_bytes: bytes) -> str:
    try:
        img = Image.open(io.BytesIO(image_bytes))
        
        img = img.convert('L')
        
        width, height = img.size
        img = img.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
        
        threshold = 140
        img = img.point(lambda p: 255 if p > threshold else 0)
        
        img = img.filter(ImageFilter.MedianFilter(size=3))
        
        
        custom_config = r'--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
        
        captcha_text = pytesseract.image_to_string(img, config=custom_config)
        
        captcha_text = captcha_text.strip()
        captcha_text = ''.join(e for e in captcha_text if e.isalnum())
        
        corrections = {
            '0': 'O',
            '1': 'I',
            '5': 'S',
            '8': 'B'
        }
        
        logger.info(f"Solved CAPTCHA: {captcha_text}")
        return captcha_text

    except Exception as e:
        logger.error(f"Error solving CAPTCHA: {str(e)}")
        raise e

async def solve_captcha_with_fallback(image_bytes: bytes, attempts: int = 1) -> str:
    for i in range(attempts):
        try:
            result = await solve_captcha(image_bytes)
            if result and len(result) >= 4:
                return result
        except Exception:
            if i == attempts - 1:
                raise
            continue
    return ""
