"""zenpost CLI — Post to social media without seeing the feed."""
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from . import __version__
from .config import PLATFORM_DOMAINS, load_config, save_config, set_platform_creds

console = Console()

SUPPORTED_PLATFORMS = list(PLATFORM_DOMAINS.keys())


@click.group()
@click.version_option(version=__version__)
def cli():
    """Post to social media without seeing the feed. 🧘"""
    pass


# ── block / unblock ──────────────────────────────────────────────

@cli.command()
@click.argument("platforms", nargs=-1, required=True)
def block(platforms):
    """Block platforms from being accessed in the browser.
    
    Examples:
        zenpost block x linkedin instagram
        zenpost block all
    """
    from .blocker import block as do_block
    
    if "all" in platforms:
        platforms = SUPPORTED_PLATFORMS
    
    invalid = [p for p in platforms if p.lower() not in SUPPORTED_PLATFORMS]
    if invalid:
        console.print(f"[red]Unknown platforms: {', '.join(invalid)}[/red]")
        console.print(f"Available: {', '.join(SUPPORTED_PLATFORMS)}")
        return
    
    domains = do_block(list(platforms))
    console.print(f"\n[green]✅ Blocked {len(platforms)} platform(s):[/green]")
    for p in platforms:
        console.print(f"  🚫 {p}")
    console.print(f"\n[dim]{len(domains)} domains redirected to 127.0.0.1[/dim]")
    console.print("[dim]API endpoints left open for posting[/dim]")


@cli.command()
@click.argument("platforms", nargs=-1, required=True)
@click.option("--for", "duration", default=None, help="Temporary unblock (e.g. 5m, 1h)")
def unblock(platforms, duration):
    """Temporarily or permanently unblock platforms.
    
    Examples:
        zenpost unblock x --for 10m
        zenpost unblock linkedin
    """
    from .blocker import unblock as do_unblock
    
    if "all" in platforms:
        platforms = SUPPORTED_PLATFORMS
    
    minutes = 0
    if duration:
        if duration.endswith("m"):
            minutes = int(duration[:-1])
        elif duration.endswith("h"):
            minutes = int(duration[:-1]) * 60
        else:
            minutes = int(duration)
    
    domains = do_unblock(list(platforms), temporary_minutes=minutes)
    
    if minutes:
        console.print(f"\n[yellow]⏱️  Temporarily unblocked for {duration}:[/yellow]")
    else:
        console.print(f"\n[green]🔓 Unblocked:[/green]")
    
    for p in platforms:
        console.print(f"  ✅ {p}")
    
    if minutes:
        console.print(f"\n[dim]Will auto-reblock in {duration}. Keep this terminal open.[/dim]")


# ── status ───────────────────────────────────────────────────────

@cli.command()
def status():
    """Show what's currently blocked and configured."""
    from .blocker import status as get_status
    
    stat = get_status()
    config = load_config()
    
    table = Table(title="zenpost status", show_header=True)
    table.add_column("Platform", style="bold")
    table.add_column("Blocked", justify="center")
    table.add_column("API Configured", justify="center")
    
    for platform in SUPPORTED_PLATFORMS:
        is_blocked = platform in stat["managed_by_zenpost"] or platform in stat["detected_in_hosts"]
        has_creds = bool(config.get("platforms", {}).get(platform, {}).get("access_token") or 
                        config.get("platforms", {}).get(platform, {}).get("api_key"))
        
        blocked_str = "🚫 Yes" if is_blocked else "✅ Open"
        creds_str = "🔑 Yes" if has_creds else "❌ No"
        
        table.add_row(platform, blocked_str, creds_str)
    
    console.print()
    console.print(table)
    console.print()


# ── post ─────────────────────────────────────────────────────────

@cli.command()
@click.argument("platform")
@click.argument("text")
@click.option("--image", "-i", help="Path to image file")
@click.option("--video", "-v", help="Path to video file")
@click.option("--api", is_flag=True, help="Use API mode instead of browser (requires credentials)")
def post(platform, text, image, video, api):
    """Post content to a platform.
    
    Uses browser automation by default (no API keys needed).
    First time: run `zenpost login <platform>` to save your session.
    
    Examples:
        zenpost post x "Hello world!"
        zenpost post x "Check this out" --image photo.jpg
        zenpost post linkedin "Excited to share..."
        zenpost post x "Tweet" --api  (use API instead of browser)
    """
    platform = platform.lower()
    
    if api:
        # API mode — requires credentials
        if platform == "x":
            from .platforms.x import post as x_post
            with console.status("Posting to X via API..."):
                result = x_post(text, image_path=image, video_path=video)
            console.print(f"\n[green]✅ Posted to X![/green]")
            console.print(f"   {result['url']}")
        elif platform == "linkedin":
            from .platforms.linkedin import post as li_post
            with console.status("Posting to LinkedIn via API..."):
                result = li_post(text, image_path=image)
            console.print(f"\n[green]✅ Posted to LinkedIn![/green]")
            console.print(f"   {result['url']}")
        else:
            console.print(f"[red]API posting to {platform} not yet supported.[/red]")
    else:
        # Browser mode — no API keys needed
        from .platforms.browser_post import post as browser_post
        
        # Temporarily unblock the platform for posting
        from .blocker import unblock, block
        config = load_config()
        was_blocked = platform in config.get("blocked", [])
        
        if was_blocked:
            console.print(f"[dim]Temporarily unblocking {platform} for posting...[/dim]")
            unblock([platform])
        
        try:
            with console.status(f"Posting to {platform} via browser..."):
                result = browser_post(platform, text, image_path=image)
            console.print(f"\n[green]✅ Posted to {platform}![/green]")
        finally:
            if was_blocked:
                block([platform])
                console.print(f"[dim]Re-blocked {platform}[/dim]")


@cli.command()
@click.argument("platform")
def login(platform):
    """Log into a platform in the browser. Session is saved for future posts.
    
    Only needed once per platform. After login, `zenpost post` works without
    any API keys.
    
    Examples:
        zenpost login x
        zenpost login linkedin
    """
    from .platforms.browser_post import login as browser_login
    
    platform = platform.lower()
    
    # Temporarily unblock for login
    from .blocker import unblock, block
    config = load_config()
    was_blocked = platform in config.get("blocked", [])
    
    if was_blocked:
        console.print(f"[dim]Temporarily unblocking {platform} for login...[/dim]")
        unblock([platform])
    
    try:
        browser_login(platform)
    finally:
        if was_blocked:
            block([platform])
            console.print(f"[dim]Re-blocked {platform}[/dim]")


# ── auth ─────────────────────────────────────────────────────────

@cli.command()
@click.argument("platform")
def auth(platform):
    """Configure API credentials for a platform.
    
    Examples:
        zenpost auth x
        zenpost auth linkedin
    """
    platform = platform.lower()
    
    if platform == "x":
        console.print(Panel(
            "[bold]X/Twitter API Setup[/bold]\n\n"
            "1. Go to https://developer.x.com/en/portal/dashboard\n"
            "2. Create a project & app (Free tier works)\n"
            "3. Enable OAuth 1.0a with Read+Write permissions\n"
            "4. Generate API keys and access tokens",
            title="🐦 X Setup",
        ))
        api_key = click.prompt("API Key (Consumer Key)")
        api_secret = click.prompt("API Secret (Consumer Secret)")
        access_token = click.prompt("Access Token")
        access_secret = click.prompt("Access Token Secret")
        
        set_platform_creds("x", {
            "api_key": api_key,
            "api_secret": api_secret,
            "access_token": access_token,
            "access_token_secret": access_secret,
        })
        console.print("[green]✅ X credentials saved![/green]")
    
    elif platform == "linkedin":
        console.print(Panel(
            "[bold]LinkedIn API Setup[/bold]\n\n"
            "1. Go to https://www.linkedin.com/developers/apps\n"
            "2. Create an app\n"
            "3. Request 'Share on LinkedIn' and 'Sign In with LinkedIn v2' products\n"
            "4. Generate an OAuth 2.0 access token with w_member_social scope",
            title="💼 LinkedIn Setup",
        ))
        access_token = click.prompt("Access Token")
        person_id = click.prompt("Person ID (from /v2/userinfo 'sub' field, or leave blank)", default="")
        
        set_platform_creds("linkedin", {
            "access_token": access_token,
            "person_id": person_id,
        })
        console.print("[green]✅ LinkedIn credentials saved![/green]")
    
    else:
        console.print(f"[red]Auth not yet supported for {platform}[/red]")


# ── migrate ──────────────────────────────────────────────────────

@cli.command()
def migrate():
    """Migrate existing /etc/hosts blocks to zenpost management.
    
    If you already have sites blocked in /etc/hosts (manually or by another tool),
    this command brings them under zenpost control.
    """
    from .blocker import migrate_existing_blocks
    
    console.print("\n[bold]Migrating existing blocks to zenpost...[/bold]\n")
    
    platforms = migrate_existing_blocks()
    
    if platforms:
        console.print(f"[green]✅ Migrated {len(platforms)} platform(s):[/green]")
        for p in platforms:
            console.print(f"  🚫 {p}")
        console.print("\n[dim]Old block sections removed. All blocks now managed by zenpost.[/dim]")
        console.print("[dim]Custom blocks (news, shopping, etc.) preserved.[/dim]")
    else:
        console.print("[yellow]No existing blocks detected to migrate.[/yellow]")


if __name__ == "__main__":
    cli()
