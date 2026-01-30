"""Configuration management for CaptionFoundry."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Project root directory (where this package is located)
PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class DatabaseConfig(BaseModel):
    """Database configuration."""
    path: str = "data/database.db"


class VisionPreprocessingConfig(BaseModel):
    """Vision model preprocessing configuration."""
    max_resolution: int = 1024
    maintain_aspect_ratio: bool = True
    resize_quality: int = 95
    format: str = "jpeg"


class VisionConfig(BaseModel):
    """Vision model configuration."""
    backend: str = "ollama"
    ollama_url: str = "http://localhost:11434"
    lmstudio_url: str = "http://localhost:1234"
    default_model: str = "qwen2.5-vl:7b"
    timeout_seconds: int = 120
    max_retries: int = 2
    max_tokens: int = 4096  # num_predict for Ollama - increase if model exhausts tokens during thinking
    preprocessing: VisionPreprocessingConfig = Field(default_factory=VisionPreprocessingConfig)


class ThumbnailConfig(BaseModel):
    """Thumbnail generation configuration."""
    max_size: int = 256
    quality: int = 85
    format: str = "webp"
    cache_path: str = "data/thumbnails"


class ExportConfig(BaseModel):
    """Export configuration."""
    default_format: str = "jpeg"
    default_quality: int = 95
    default_padding: int = 6
    staging_path: str = "data/exports"


class ImageProcessingConfig(BaseModel):
    """Image processing configuration."""
    supported_formats: list[str] = Field(
        default=["jpg", "jpeg", "png", "webp", "gif", "bmp"]
    )
    max_file_size_mb: int = 100


class ServerConfig(BaseModel):
    """Server configuration."""
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    debug: bool = False


class Settings(BaseModel):
    """Application settings."""
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    thumbnails: ThumbnailConfig = Field(default_factory=ThumbnailConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    image_processing: ImageProcessingConfig = Field(default_factory=ImageProcessingConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)


class ConfigLoader:
    """Load and manage application configuration."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or PROJECT_ROOT / "config"
        self._settings: Optional[Settings] = None
    
    def load_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load a YAML file with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return data if data is not None else {}
        except FileNotFoundError:
            logger.warning(f"Config file not found: {file_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {file_path}: {e}")
            raise
    
    def load_settings(self, file_path: Optional[Path] = None) -> Settings:
        """Load application settings from YAML file."""
        if file_path is None:
            file_path = self.config_dir / "settings.yaml"
        
        if not file_path.exists():
            # Try template if settings.yaml doesn't exist
            template_path = self.config_dir / "settings.yaml.template"
            if template_path.exists():
                logger.info(f"Using template config: {template_path}")
                file_path = template_path
            else:
                logger.info("No config file found, using defaults")
                return Settings()
        
        data = self.load_yaml(file_path)
        settings = Settings(**data)
        logger.info(f"Loaded settings from {file_path}")
        return settings
    
    @property
    def settings(self) -> Settings:
        """Get cached settings, loading if necessary."""
        if self._settings is None:
            self._settings = self.load_settings()
        return self._settings
    
    def reload(self) -> Settings:
        """Force reload settings from disk."""
        self._settings = None
        return self.settings


# Global config loader instance
_config_loader: Optional[ConfigLoader] = None


def get_config_loader() -> ConfigLoader:
    """Get the global config loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_settings() -> Settings:
    """Get application settings."""
    return get_config_loader().settings
