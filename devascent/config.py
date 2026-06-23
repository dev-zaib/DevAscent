"""Assessment configuration.

Follows Hermes convention: secrets in .env, settings in config.yaml.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

from devascent_constants import get_devascent_home

load_dotenv(get_devascent_home() / ".env")


class AssessmentConfig:
    @property
    def database_url(self) -> str:
        return os.getenv(
            "DATABASE_URL",
            "postgresql+asyncpg://devascent:devascent@localhost:5432/devascent",
        )

    @property
    def redis_url(self) -> str:
        return os.getenv("REDIS_URL", "redis://localhost:6379/0")

    @property
    def openai_api_key(self) -> str | None:
        return os.getenv("OPENAI_API_KEY")

    @property
    def anthropic_api_key(self) -> str | None:
        return os.getenv("ANTHROPIC_API_KEY")

    @property
    def embedding_model(self) -> str:
        return os.getenv("DEVASCENT_EMBEDDING_MODEL", "text-embedding-3-small")

    @property
    def evaluation_model(self) -> str:
        return os.getenv(
            "DEVASCENT_EVALUATION_MODEL", "anthropic/claude-sonnet-4"
        )

    @property
    def escalation_model(self) -> str:
        return os.getenv(
            "DEVASCENT_ESCALATION_MODEL", "anthropic/claude-opus-4"
        )

    @property
    def sandbox_timeout(self) -> int:
        return int(os.getenv("DEVASCENT_SANDBOX_TIMEOUT", "30"))

    @property
    def max_submissions_per_hour(self) -> int:
        return int(os.getenv("DEVASCENT_MAX_SUBMISSIONS_PER_HOUR", "10"))


assessment_config = AssessmentConfig()
