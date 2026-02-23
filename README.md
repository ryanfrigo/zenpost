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
# Block social media (keeps API access working)
sudo zenpost block x linkedin instagram youtube

# Post to X (Twitter)
zenpost post x "Just shipped zenpost — post without the feed."

# Post to X with an image
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

## Setup API Keys

```bash
# X/Twitter — get keys at https://developer.x.com
zenpost auth x

# LinkedIn — get keys at https://developer.linkedin.com
zenpost auth linkedin
```

Keys are stored in `~/.zenpost/config.json`.

## How It Works

1. **Blocking**: Adds entries to `/etc/hosts` to redirect social media domains to `127.0.0.1`. Your browser can't load the feed.
2. **Posting**: Uses official platform APIs to publish content. APIs don't go through `/etc/hosts` — they resolve directly to API endpoints (`api.x.com`, `api.linkedin.com`).
3. **You stay focused**: No feed. No algorithm. No doom-scrolling. Just your content going out.

## Philosophy

Social media is a megaphone, not a TV. Use it to broadcast, not consume.

## License

MIT
