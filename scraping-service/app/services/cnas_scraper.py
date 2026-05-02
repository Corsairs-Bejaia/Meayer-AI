import asyncio
import logging
import time
import os
from datetime import datetime
from typing import Optional
from playwright.async_api import Page
from app.config import settings
from app.services.browser_pool import browser_pool
from app.services.captcha_solver import solve_captcha
from app.services.result_parser import parse_cnas_result
from app.utils.rate_limiter import cnas_rate_limiter

logger = logging.getLogger(__name__)


async def scrape_cnas(
    attestation_number: str, employer_number: str, ssn: Optional[str] = None
):
    start_time = time.monotonic()
    attempts = 0
    max_attempts = settings.CAPTCHA_MAX_RETRIES

    if not await cnas_rate_limiter.acquire():
        return {
            "valid": None,
            "status": "rate_limited",
            "error": "Rate limit exceeded",
            "attempts": 0,
            "processing_time_ms": int((time.monotonic() - start_time) * 1000),
        }

    context = await browser_pool.acquire_context()
    page = await context.new_page()

    try:
        while attempts < max_attempts:
            attempts += 1
            logger.info(
                f"CNAS Verification Attempt {attempts} for {attestation_number}"
            )

            try:
                url = f"{settings.CNAS_BASE_URL}{settings.CNAS_VERIFY_PATH}"
                await page.goto(
                    url, timeout=settings.PAGE_LOAD_TIMEOUT_MS, wait_until="networkidle"
                )

                captcha_img = await page.wait_for_selector(
                    'img[src*="simpleCaptcha.png"]', timeout=5000
                )
                if not captcha_img:
                    raise Exception("CAPTCHA image not found")

                captcha_bytes = await captcha_img.screenshot()

                captcha_text = await solve_captcha(captcha_bytes)
                if not captcha_text:
                    logger.warning("CAPTCHA solve returned empty text, retrying...")
                    continue

                await page.fill(
                    settings.CNAS_FORM_ATTESTATION_SELECTOR, attestation_number
                )
                await page.fill(settings.CNAS_FORM_EMPLOYER_SELECTOR, employer_number)
                await page.fill(settings.CNAS_FORM_CAPTCHA_SELECTOR, captcha_text)

                await page.click(settings.CNAS_SUBMIT_SELECTOR)

                await page.wait_for_load_state("networkidle")

                html_content = await page.content()
                result = parse_cnas_result(html_content, ssn_to_find=ssn)

                if result["status"] == "captcha_failed":
                    logger.warning(
                        f"CAPTCHA failed on site (attempt {attempts}), retrying..."
                    )
                    continue

                processing_time_ms = int((time.monotonic() - start_time) * 1000)
                return {
                    **result,
                    "raw_response": html_content
                    if settings.LOG_LEVEL == "debug"
                    else None,
                    "attempts": attempts,
                    "processing_time_ms": processing_time_ms,
                }

            except Exception as e:
                logger.error(f"Error during attempt {attempts}: {str(e)}")
                if attempts >= max_attempts:
                    raise e
                await asyncio.sleep(2)

        return {
            "valid": None,
            "status": "error",
            "error": "Max attempts reached",
            "attempts": attempts,
            "processing_time_ms": int((time.monotonic() - start_time) * 1000),
        }

    except Exception as e:
        screenshot_path = await capture_failure_screenshot(page, "cnas_error")
        return {
            "valid": None,
            "status": "error",
            "error": str(e),
            "attempts": attempts,
            "processing_time_ms": int((time.monotonic() - start_time) * 1000),
            "screenshot_path": screenshot_path,
        }
    finally:
        await page.close()
        await browser_pool.release_context(context)


async def capture_failure_screenshot(page: Page, error_type: str) -> str:
    try:
        os.makedirs("/tmp/scraping-errors", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"/tmp/scraping-errors/{timestamp}_{error_type}.png"
        await page.screenshot(path=path, full_page=True)
        return path
    except Exception as e:
        logger.error(f"Failed to capture screenshot: {e}")
        return ""
