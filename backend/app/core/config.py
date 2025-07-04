import secrets
import warnings
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    HttpUrl,
    PostgresDsn,
    computed_field,
    model_validator,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file=[".env.testing", "../.env"],
        env_ignore_empty=True,
        extra="ignore",
    )
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    # 60 minutes * 24 hours * 8 days = 8 days
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str = "http://localhost:5173"
    ENVIRONMENT: Literal["local", "staging", "production", "testing"] = "local"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    PROJECT_NAME: str
    SENTRY_DSN: HttpUrl | None = None
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""

    # Redis configuration
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    # Server configuration for microservices migration
    BACKEND_PORT: int = 8001  # Legacy backend port (moved from 8000)
    GATEWAY_PORT: int = 8000  # Kong gateway port (main entry point)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def REDIS_URL(self) -> str:
        """Build Redis URL from components with proper URL encoding."""
        from urllib.parse import quote_plus
        
        if self.REDIS_PASSWORD:
            # URL encode the password to handle special characters properly
            encoded_password = quote_plus(self.REDIS_PASSWORD)
            # Use proper Redis URL format: redis://username:password@host:port/db
            return f"redis://default:{encoded_password}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    # TODO: update type to EmailStr when sqlmodel supports it
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None

    @model_validator(mode="after")
    def _set_default_emails_from(self) -> Self:
        if not self.EMAILS_FROM_NAME:
            self.EMAILS_FROM_NAME = self.PROJECT_NAME
        return self

    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 48
    
    # Email service configuration for templates
    EMAIL_SERVICE: Literal["smtp", "sendgrid", "mailgun", "ses"] = "smtp"
    EMAIL_API_KEY: str = ""
    SENDGRID_API_KEY: str = ""
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    AWS_SES_REGION: str = "us-east-1"
    
    # Email template configuration
    EMAIL_TEMPLATE_CACHE_TTL: int = 3600  # 1 hour
    EMAIL_TEMPLATE_FALLBACK_ENABLED: bool = True
    MJML_CLI_ENABLED: bool = True  # MJML CLI installed and available

    @computed_field  # type: ignore[prop-decorator]
    @property
    def emails_enabled(self) -> bool:
        return bool(self.SMTP_HOST and self.EMAILS_FROM_EMAIL)

    # User configuration
    EMAIL_TEST_USER: str = "test@example.com"
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    # Security and rate limiting configuration
    RATE_LIMIT_ANONYMOUS: int = 20  # Requests per minute for anonymous users
    RATE_LIMIT_AUTHENTICATED: int = 200  # Requests per minute for authenticated users
    RATE_LIMIT_PERIOD: int = 60  # Period in seconds

    # Business configuration
    MIN_PRODUCT_PRICE: float = 10.00
    MAX_PRODUCT_PRICE: float = 99999.99
    MAX_SKU_LENGTH: int = 50

    # Payment Gateway Configuration
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    PAYPAL_CLIENT_ID: str = ""
    PAYPAL_CLIENT_SECRET: str = ""
    PAYPAL_MODE: Literal["sandbox", "live"] = "sandbox"

    # Security configuration
    BCRYPT_ROUNDS: int = 12
    SESSION_TIMEOUT_MINUTES: int = 30

    @model_validator(mode="after")
    def validate_security_settings(self) -> Self:
        """Validate security-related settings."""
        if self.ENVIRONMENT == "production":
            # Ensure strong security in production
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY must be at least 32 characters in production"
                )

            if (
                self.FIRST_SUPERUSER_PASSWORD
                and len(self.FIRST_SUPERUSER_PASSWORD) < 12
            ):
                raise ValueError(
                    "FIRST_SUPERUSER_PASSWORD must be at least 12 characters in production"
                )

            if not self.SENTRY_DSN:
                warnings.warn(
                    "SENTRY_DSN not configured for production environment", stacklevel=2
                )

        # Validate rate limiting settings
        if self.RATE_LIMIT_ANONYMOUS <= 0:
            raise ValueError("RATE_LIMIT_ANONYMOUS must be positive")

        if self.RATE_LIMIT_AUTHENTICATED <= 0:
            raise ValueError("RATE_LIMIT_AUTHENTICATED must be positive")

        if self.RATE_LIMIT_PERIOD <= 0:
            raise ValueError("RATE_LIMIT_PERIOD must be positive")

        # Validate business settings
        if self.MIN_PRODUCT_PRICE <= 0:
            raise ValueError("MIN_PRODUCT_PRICE must be positive")

        if self.MAX_PRODUCT_PRICE <= self.MIN_PRODUCT_PRICE:
            raise ValueError("MAX_PRODUCT_PRICE must be greater than MIN_PRODUCT_PRICE")

        return self

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret(
            "FIRST_SUPERUSER_PASSWORD", self.FIRST_SUPERUSER_PASSWORD
        )

        return self


settings = Settings()  # type: ignore
