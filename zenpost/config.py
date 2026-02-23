"""Config management for zenpost."""
import json
import os
from pathlib import Path

CONFIG_DIR = Path.home() / ".zenpost"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "platforms": {
        "x": {
            "api_key": "",
            "api_secret": "",
            "access_token": "",
            "access_token_secret": "",
            "bearer_token": "",
        },
        "linkedin": {
            "access_token": "",
            "person_id": "",
        },
    },
    "blocked": [],
}

# Domains to block per platform (feed/consumption domains only)
PLATFORM_DOMAINS = {
    "x": ["twitter.com", "www.twitter.com", "x.com", "www.x.com", "mobile.twitter.com", "mobile.x.com"],
    "linkedin": ["linkedin.com", "www.linkedin.com", "mobile.linkedin.com"],
    "instagram": ["instagram.com", "www.instagram.com"],
    "facebook": ["facebook.com", "www.facebook.com", "m.facebook.com", "marketplace.facebook.com"],
    "tiktok": ["tiktok.com", "www.tiktok.com"],
    "youtube": ["youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"],
    "threads": ["threads.net", "www.threads.net"],
    "bluesky": ["bsky.app", "www.bsky.app"],
    "reddit": ["reddit.com", "www.reddit.com", "old.reddit.com"],
    "twitch": ["twitch.tv", "www.twitch.tv"],
    "hackernews": ["news.ycombinator.com"],
}

# API domains that must NOT be blocked (posting still works with hosts blocking)
API_DOMAINS = {
    "x": ["api.x.com", "api.twitter.com", "upload.twitter.com"],
    "linkedin": ["api.linkedin.com"],
    "instagram": ["graph.facebook.com", "graph.instagram.com"],
    "tiktok": ["open.tiktokapis.com"],
    "youtube": ["www.googleapis.com"],
    "bluesky": ["bsky.social"],
}


def load_config() -> dict:
    """Load config from ~/.zenpost/config.json."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config: dict):
    """Save config to ~/.zenpost/config.json."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)  # private — contains API keys


def get_platform_creds(platform: str) -> dict:
    """Get credentials for a platform."""
    config = load_config()
    return config.get("platforms", {}).get(platform, {})


def set_platform_creds(platform: str, creds: dict):
    """Set credentials for a platform."""
    config = load_config()
    if "platforms" not in config:
        config["platforms"] = {}
    config["platforms"][platform] = creds
    save_config(config)
