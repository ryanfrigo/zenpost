# zenpost

**Post to social media without seeing the feed.**

Block distracting sites at the system level. Post content via APIs. Never open a browser, never see a timeline.

## Why

You want to be a creator, not a consumer. Block the feeds. Keep the megaphone.

## Install

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/ryanfrigo/zenpost/main/install.sh | bash

# or clone and install
git clone https://github.com/ryanfrigo/zenpost.git
cd zenpost
pip install -e .
```

## Quick Start

```bash
# Block social media feeds
sudo zenpost block x linkedin instagram youtube

# Log in once (saves your session — no API keys needed)
zenpost login x
zenpost login linkedin

# Post to X (Twitter) — never see the feed
zenpost post x "Just shipped zenpost — post without the feed."

# Post with an image
zenpost post x "Check this out" --image ./screenshot.png

# Post to LinkedIn
zenpost post linkedin "Excited to announce..." --image ./launch.png

# See what's blocked
zenpost status

# Temporary unblock (auto-reblocks after timer)
zenpost unblock x --for 10m
```

## Supported Platforms

| Platform  | Post Text | Post Image | Post Video | Block Feed |
|-----------|-----------|------------|------------|------------|
| X/Twitter | ✅        | ✅         | ✅         | ✅         |
| LinkedIn  | ✅        | ✅         | ❌         | ✅         |
| Instagram | 🔜        | 🔜         | 🔜         | ✅         |
| TikTok    | 🔜        | N/A        | 🔜         | ✅         |
| YouTube   | 🔜        | N/A        | 🔜         | ✅         |
| Bluesky   | 🔜        | 🔜         | 🔜         | ✅         |
| Threads   | 🔜        | 🔜         | 🔜         | ✅         |

## How It Works

1. **Blocking**: Adds entries to `/etc/hosts` to redirect social media domains to `127.0.0.1`. Your browser can't load the feed.
2. **Login once**: `zenpost login x` opens a browser — you log in, and your session is saved. No API keys, no developer accounts.
3. **Posting**: Opens a headless browser, navigates directly to the compose page (skipping the feed), types your post, hits publish, and closes. You never see a timeline.
4. **Auto-reblock**: If the platform was blocked, zenpost temporarily unblocks it for the post, then re-blocks immediately after.

No API keys. No developer accounts. No feed exposure. Just post and go.

## Philosophy

Social media is a megaphone, not a TV. Use it to broadcast, not consume.

## License

MIT
