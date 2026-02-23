"""X/Twitter posting via API v2."""
import tweepy
from ..config import get_platform_creds


def _get_client() -> tweepy.Client:
    """Get authenticated X API v2 client."""
    creds = get_platform_creds("x")
    if not creds.get("api_key"):
        raise click.ClickException(
            "X not configured. Run: zenpost auth x"
        )
    return tweepy.Client(
        consumer_key=creds["api_key"],
        consumer_secret=creds["api_secret"],
        access_token=creds["access_token"],
        access_token_secret=creds["access_token_secret"],
    )


def _get_api_v1() -> tweepy.API:
    """Get v1.1 API for media uploads."""
    creds = get_platform_creds("x")
    auth = tweepy.OAuth1UserHandler(
        creds["api_key"],
        creds["api_secret"],
        creds["access_token"],
        creds["access_token_secret"],
    )
    return tweepy.API(auth)


def post(text: str, image_path: str = None, video_path: str = None) -> dict:
    """Post a tweet, optionally with media."""
    client = _get_client()
    media_ids = []
    
    if image_path or video_path:
        api_v1 = _get_api_v1()
        if image_path:
            media = api_v1.media_upload(image_path)
            media_ids.append(media.media_id)
        if video_path:
            media = api_v1.media_upload(video_path, media_category="tweet_video")
            media_ids.append(media.media_id)
    
    response = client.create_tweet(
        text=text,
        media_ids=media_ids if media_ids else None,
    )
    
    tweet_id = response.data["id"]
    return {
        "id": tweet_id,
        "url": f"https://x.com/i/status/{tweet_id}",
        "text": text,
    }


import click  # noqa: E402 — needed for error messages
