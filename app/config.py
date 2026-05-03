from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    
    INTERNAL_API_KEY: str = "shared-secret-with-nestjs-backend"
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LOG_LEVEL: str = "info"
    SERVICE_NAME: str = "ai-service"
    VERSION: str = "0.1.0"

    
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = ""
    R2_PUBLIC_URL: str = ""

    
    DEFAULT_CONFIDENCE_THRESHOLD: float = 0.7
    ENABLE_GPT4O_FALLBACK: bool = False
    ENABLE_GEMINI_FALLBACK: bool = True
    MAX_SELF_CORRECTION_RETRIES: int = 2

    # Scraping Settings
    CNAS_BASE_URL: str = "https://teledeclaration.cnas.dz"
    CNAS_VERIFY_PATH: str = "/checkDECEMP.jsp"
    CNAS_CAPTCHA_PATH: str = "/simpleCaptcha.png"
    CNAS_RATE_LIMIT_SECONDS: int = 5
    CAPTCHA_MAX_RETRIES: int = 3

    BROWSER_POOL_SIZE: int = 1
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT_MS: int = 30000
    PAGE_LOAD_TIMEOUT_MS: int = 30000

    CNAS_FORM_ATTESTATION_SELECTOR: str = 'input[name="numAttest"]'
    CNAS_FORM_EMPLOYER_SELECTOR: str = 'input[name="numCot"]'
    CNAS_FORM_CAPTCHA_SELECTOR: str = 'input[name="captchaValue"]'
    CNAS_SUBMIT_SELECTOR: str = 'input[type="submit"]'

    model_config = SettingsConfigDict(env_file=[".env", "../.env"], extra="ignore")

settings = Settings()
