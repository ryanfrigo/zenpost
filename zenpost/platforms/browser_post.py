"""Browser-based posting — no API keys needed.

Uses Playwright to automate posting through the actual website.
Your session stays logged in via saved browser profile.
You never see the feed — it navigates directly to the compose page.
"""
import subprocess
import sys
from pathlib import Path

PROFILE_DIR = Path.home() / ".zenpost" / "browser-profile"

# Direct compose/post URLs — skip the feed entirely
COMPOSE_URLS = {
    "x": "https://x.com/compose/post",
    "linkedin": "https://www.linkedin.com/feed/?shareActive=true",
}


def _ensure_playwright():
    """Install playwright if needed."""
    try:
        import playwright
    except ImportError:
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright"], check=True)
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)


def _get_browser_context():
    """Get a persistent browser context with saved login state."""
    from playwright.sync_api import sync_playwright
    
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    
    pw = sync_playwright().start()
    browser = pw.chromium.launch_persistent_context(
        str(PROFILE_DIR),
        headless=False,  # Need visible for first login, then can go headless
        viewport={"width": 1280, "height": 800},
    )
    return pw, browser


def login(platform: str):
    """Open browser to platform login page. User logs in manually once.
    Session is saved for future posts.
    """
    login_urls = {
        "x": "https://x.com/login",
        "linkedin": "https://www.linkedin.com/login",
    }
    
    if platform not in login_urls:
        raise ValueError(f"Unsupported platform: {platform}")
    
    _ensure_playwright()
    pw, browser = _get_browser_context()
    
    page = browser.new_page()
    page.goto(login_urls[platform])
    
    print(f"\n🔐 Log into {platform} in the browser window.")
    print("   Your session will be saved for future posts.")
    print("   Press Enter here when done...")
    input()
    
    browser.close()
    pw.stop()
    print(f"✅ {platform} session saved!")


def post(platform: str, text: str, image_path: str = None):
    """Post to platform via browser automation."""
    if platform not in COMPOSE_URLS:
        raise ValueError(f"Browser posting not supported for: {platform}")
    
    _ensure_playwright()
    pw, browser = _get_browser_context()
    
    page = browser.new_page()
    
    try:
        if platform == "x":
            return _post_x(page, text, image_path)
        elif platform == "linkedin":
            return _post_linkedin(page, text, image_path)
    finally:
        browser.close()
        pw.stop()


def _post_x(page, text: str, image_path: str = None) -> dict:
    """Post to X via browser."""
    # Go directly to compose — skip the feed
    page.goto("https://x.com/compose/post", wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Type into the compose box
    editor = page.locator('[data-testid="tweetTextarea_0"]')
    editor.click()
    editor.fill(text)
    
    # Upload image if provided
    if image_path:
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(image_path)
        page.wait_for_timeout(3000)  # Wait for upload
    
    # Click post button
    post_btn = page.locator('[data-testid="tweetButton"]')
    post_btn.click()
    page.wait_for_timeout(2000)
    
    return {"platform": "x", "text": text, "status": "posted"}


def _post_linkedin(page, text: str, image_path: str = None) -> dict:
    """Post to LinkedIn via browser."""
    # Go to feed with share dialog active
    page.goto("https://www.linkedin.com/feed/?shareActive=true", wait_until="networkidle")
    page.wait_for_timeout(2000)
    
    # Click "Start a post" if share dialog didn't auto-open
    try:
        start_post = page.locator('button:has-text("Start a post")')
        if start_post.is_visible(timeout=3000):
            start_post.click()
            page.wait_for_timeout(1000)
    except Exception:
        pass
    
    # Type into the editor
    editor = page.locator('[data-testid="share-creation__editor"]').or_(
        page.locator('.ql-editor')
    )
    editor.click()
    editor.fill(text)
    
    # Upload image if provided
    if image_path:
        # Click the image button
        img_btn = page.locator('button[aria-label="Add a photo"]').or_(
            page.locator('button[aria-label="Add media"]')
        )
        img_btn.click()
        page.wait_for_timeout(1000)
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(image_path)
        page.wait_for_timeout(3000)
    
    # Click Post button
    post_btn = page.locator('button:has-text("Post")')
    post_btn.click()
    page.wait_for_timeout(2000)
    
    return {"platform": "linkedin", "text": text, "status": "posted"}
