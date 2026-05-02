import io
import logging
import pytesseract
from PIL import Image, ImageEnhance
from google import genai
from app.config import settings

logger = logging.getLogger(__name__)


async def solve_captcha(image_bytes: bytes) -> str:
    try:
        original_img = Image.open(io.BytesIO(image_bytes))

        thresholds = [100, 130, 160]
        psm_modes = [7, 8]
        best_text = ""

        for psm in psm_modes:
            for threshold in thresholds:
                img = original_img.convert("L")

                
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(2.0)

                width, height = img.size
                img = img.resize((width * 4, height * 4), Image.Resampling.LANCZOS)

                img = img.point(lambda p: 255 if p > threshold else 0)

                custom_config = f"--psm {psm} -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyz0123456789"

                captcha_text = pytesseract.image_to_string(img, config=custom_config)
                captcha_text = captcha_text.strip().lower()
                captcha_text = "".join(e for e in captcha_text if e.isalnum())

                if len(captcha_text) == 5 or len(captcha_text) == 6:
                    best_text = captcha_text
                    break

                if not best_text or abs(len(captcha_text) - 5) < abs(
                    len(best_text) - 5
                ):
                    best_text = captcha_text
            if len(best_text) == 5 or len(best_text) == 6:
                break

        logger.info(f"Solved CAPTCHA: {best_text} (Tesseract)")
        return best_text

    except Exception as e:
        logger.error(f"Error solving CAPTCHA: {str(e)}")
        raise e


async def solve_captcha_gemini(image_bytes: bytes) -> str:
    if not settings.GEMINI_API_KEY:
        return ""

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[
                ,
                image_bytes,
            ],
        )
        captcha_text = response.text.strip()
        logger.info(f"Solved CAPTCHA with Gemini: {captcha_text}")
        return captcha_text
    except Exception as e:
        logger.error(f"Gemini OCR error: {e}")
        return ""


async def solve_captcha_with_fallback(image_bytes: bytes, attempts: int = 1) -> str:
    try:
        result = await solve_captcha(image_bytes)
        if result and len(result) >= 4:
            return result
    except Exception:
        pass

    if settings.GEMINI_API_KEY:
        result = await solve_captcha_gemini(image_bytes)
        if result:
            return result

    return ""
