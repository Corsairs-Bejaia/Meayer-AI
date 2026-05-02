from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    INTERNAL_API_KEY: str = "shared-secret-with-nestjs-backend"
    LOG_LEVEL: str = "info"
    SERVICE_NAME: str = "scraping-service"
    VERSION: str = "0.1.0"

    CNAS_BASE_URL: str = "https://teledeclaration.cnas.dz"
    CNAS_VERIFY_PATH: str = "/checkDECEMP.jsp"
    CNAS_CAPTCHA_PATH: str = "/simpleCaptcha.png"
    CNAS_RATE_LIMIT_SECONDS: int = 5
    CAPTCHA_MAX_RETRIES: int = 3

    BROWSER_POOL_SIZE: int = 2
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT_MS: int = 30000
    PAGE_LOAD_TIMEOUT_MS: int = 30000
    
    # Cloudflare R2 Storage Configuration
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_URL: str = ""

    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 86400

    CAPTCHA_FALLBACK_2CAPTCHA: bool = False
    TWO_CAPTCHA_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    CNAS_FORM_ATTESTATION_SELECTOR: str = 'input[name="numAttest"]'
    CNAS_FORM_EMPLOYER_SELECTOR: str = 'input[name="numCot"]'
    CNAS_FORM_CAPTCHA_SELECTOR: str = 'input[name="captchaValue"]'
    CNAS_SUBMIT_SELECTOR: str = 'input[type="submit"]'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
