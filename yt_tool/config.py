"""Load and expose project configuration from config.toml."""

import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
_CONFIG_PATH = PROJECT_ROOT / "config.toml"


def load_config() -> dict:
    with open(_CONFIG_PATH, "rb") as f:
        return tomllib.load(f)


config = load_config()

# Resolve paths relative to project root
DB_FILE                  = str(PROJECT_ROOT / config["db_file"])
LOG_FILE                 = str(PROJECT_ROOT / config["log_file"])
LOG_LEVEL                = config.get("log_level", "INFO")
EXPORT_DIR               = str(PROJECT_ROOT / config.get("export_dir", "."))
SCHEDULER_INTERVAL_HOURS = int(config.get("scheduler_interval_hours", 24))
