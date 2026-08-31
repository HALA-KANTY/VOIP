from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuration centralisee, lue depuis les variables d'environnement / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+asyncpg://voip_user:voip_password_secure@localhost:5432/voip_billing"

    ASTERISK_AMI_HOST: str = "localhost"
    ASTERISK_AMI_PORT: int = 5038
    ASTERISK_AMI_USER: str = "fastapi"
    ASTERISK_AMI_SECRET: str = ""

    # Chemin de la config Asterisk vue par le conteneur backend (monte en volume
    # Docker). Configurable pour que les tests n'ecrivent jamais sur le vrai
    # /etc/asterisk d'une machine de developpement.
    ASTERISK_CONFIG_DIR: str = "/etc/asterisk"

    AMI_ENDPOINTS_SECRET: str = "change_moi_secret_partage"

    JWT_SECRET_KEY: str = "change_moi_cle_secrete"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    TARIF_DEFAUT: Decimal = Decimal("1.0")

    CORS_ORIGINS: str = "http://localhost:5173"

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "change_moi_mot_de_passe"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
