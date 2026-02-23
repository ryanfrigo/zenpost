"""System-level site blocking via /etc/hosts."""
import os
import re
import subprocess
import threading
import time
from pathlib import Path

from .config import PLATFORM_DOMAINS, API_DOMAINS, load_config, save_config

HOSTS_FILE = Path("/etc/hosts")
BLOCK_START = "# === ZENPOST BLOCK ==="
BLOCK_END = "# === END ZENPOST BLOCK ==="


def _read_hosts() -> str:
    """Read /etc/hosts content."""
    return HOSTS_FILE.read_text()


def _write_hosts(content: str):
    """Write /etc/hosts (requires sudo)."""
    # Write to temp file then move with sudo
    tmp = Path("/tmp/zenpost_hosts")
    tmp.write_text(content)
    subprocess.run(["sudo", "cp", str(tmp), str(HOSTS_FILE)], check=True)
    tmp.unlink()
    # Flush DNS cache
    subprocess.run(["sudo", "dscacheutil", "-flushcache"], check=False)
    subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=False)


def _remove_old_blocks(content: str) -> str:
    """Remove any existing zenpost blocks and old Orion blocks from hosts."""
    # Remove zenpost blocks
    pattern = re.compile(
        rf"^{re.escape(BLOCK_START)}.*?{re.escape(BLOCK_END)}\s*$",
        re.MULTILINE | re.DOTALL,
    )
    content = pattern.sub("", content)
    
    # Remove old Orion FOCUS BLOCK
    old_pattern = re.compile(
        r"^# === FOCUS BLOCK \(added by Orion\) ===.*?# === END FOCUS BLOCK ===\s*$",
        re.MULTILINE | re.DOTALL,
    )
    content = old_pattern.sub("", content)
    
    # Remove duplicate YouTube entries before the focus block
    lines = content.split("\n")
    cleaned = []
    seen_youtube = set()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("127.0.0.1") and any(yt in stripped for yt in ["youtube.com", "youtu.be"]):
            if stripped in seen_youtube:
                continue
            seen_youtube.add(stripped)
        cleaned.append(line)
    
    return "\n".join(cleaned)


def _get_all_blocked_domains(platforms: list[str]) -> list[str]:
    """Get all domains that should be blocked for given platforms."""
    domains = []
    for platform in platforms:
        platform = platform.lower()
        if platform in PLATFORM_DOMAINS:
            for domain in PLATFORM_DOMAINS[platform]:
                # Never block API domains
                api_doms = []
                for api_list in API_DOMAINS.values():
                    api_doms.extend(api_list)
                if domain not in api_doms:
                    domains.append(domain)
    return list(dict.fromkeys(domains))  # dedupe preserving order


def block(platforms: list[str]) -> list[str]:
    """Block specified platforms. Returns list of blocked domains."""
    config = load_config()
    current_blocked = set(config.get("blocked", []))
    new_platforms = [p.lower() for p in platforms]
    all_blocked = list(current_blocked | set(new_platforms))
    
    domains = _get_all_blocked_domains(all_blocked)
    
    if not domains:
        return []
    
    # Build hosts block
    lines = [BLOCK_START]
    for domain in domains:
        lines.append(f"127.0.0.1 {domain}")
    lines.append(BLOCK_END)
    block_text = "\n".join(lines) + "\n"
    
    # Update /etc/hosts
    content = _read_hosts()
    content = _remove_old_blocks(content)
    content = content.rstrip("\n") + "\n\n" + block_text
    _write_hosts(content)
    
    # Update config
    config["blocked"] = all_blocked
    save_config(config)
    
    return domains


def unblock(platforms: list[str], temporary_minutes: int = 0) -> list[str]:
    """Unblock specified platforms. Returns unblocked domains."""
    config = load_config()
    current_blocked = set(config.get("blocked", []))
    to_remove = set(p.lower() for p in platforms)
    remaining = list(current_blocked - to_remove)
    
    # Get domains being unblocked
    unblocked_domains = _get_all_blocked_domains(list(to_remove))
    
    if remaining:
        # Re-block remaining platforms
        config["blocked"] = remaining
        save_config(config)
        block(remaining)
    else:
        # Remove all blocks
        content = _read_hosts()
        content = _remove_old_blocks(content)
        _write_hosts(content)
        config["blocked"] = []
        save_config(config)
    
    if temporary_minutes > 0:
        # Schedule re-block after timeout
        def _reblock():
            time.sleep(temporary_minutes * 60)
            block(list(to_remove))
            print(f"\n⏰ Time's up! Re-blocked: {', '.join(to_remove)}")
        
        t = threading.Thread(target=_reblock, daemon=False)
        t.start()
    
    return unblocked_domains


def status() -> dict:
    """Get current blocking status."""
    config = load_config()
    blocked = config.get("blocked", [])
    
    # Also check /etc/hosts for any non-zenpost blocks
    content = _read_hosts()
    hosts_blocked = set()
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("127.0.0.1") and not line.startswith("127.0.0.1\tlocalhost"):
            parts = line.split()
            for domain in parts[1:]:
                # Find which platform this belongs to
                for platform, domains in PLATFORM_DOMAINS.items():
                    if domain in domains:
                        hosts_blocked.add(platform)
    
    return {
        "managed_by_zenpost": blocked,
        "detected_in_hosts": list(hosts_blocked),
    }


def migrate_existing_blocks() -> list[str]:
    """Migrate existing /etc/hosts blocks to zenpost management.
    
    Detects platforms already blocked in hosts file and brings them
    under zenpost management (removes old block sections, adds zenpost block).
    Returns list of migrated platforms.
    """
    stat = status()
    detected = stat["detected_in_hosts"]
    
    if not detected:
        return []
    
    # Also preserve non-platform blocks (custom user blocks)
    content = _read_hosts()
    
    # Remove ALL old block sections
    # Remove any existing block sections (# === SOMETHING === ... # === END SOMETHING ===)
    pattern = re.compile(
        r"^# === (?!ZENPOST)[A-Z].*?===.*?# === END .*?===\s*$",
        re.MULTILINE | re.DOTALL,
    )
    content = pattern.sub("", content)
    
    # Remove zenpost blocks too
    content = _remove_old_blocks(content)
    
    # Remove any remaining 127.0.0.1 lines (except localhost)
    lines = []
    for line in content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("127.0.0.1") and "localhost" not in stripped and "broadcasthost" not in stripped:
            continue
        lines.append(line)
    content = "\n".join(lines)
    
    # Now collect ALL domains we want to block — detected platforms + extra domains from old blocks
    all_platforms = list(set(detected))
    
    # Add non-platform domains from the old hosts file (custom user blocks)
    old_content = HOSTS_FILE.read_text()
    extra_domains = []
    for line in old_content.split("\n"):
        stripped = line.strip()
        if stripped.startswith("127.0.0.1") and "localhost" not in stripped and "broadcasthost" not in stripped:
            parts = stripped.split()
            for domain in parts[1:]:
                # Check if this domain is already covered by a platform
                is_platform = False
                for plat_domains in PLATFORM_DOMAINS.values():
                    if domain in plat_domains:
                        is_platform = True
                        break
                if not is_platform:
                    extra_domains.append(domain)
    
    extra_domains = list(dict.fromkeys(extra_domains))  # dedupe
    
    # Build new zenpost block with platform domains + extra domains
    platform_domains = _get_all_blocked_domains(all_platforms)
    all_domains = platform_domains + extra_domains
    
    block_lines = [BLOCK_START]
    block_lines.append("# Platforms")
    for domain in platform_domains:
        block_lines.append(f"127.0.0.1 {domain}")
    if extra_domains:
        block_lines.append("# Other blocked sites")
        for domain in extra_domains:
            block_lines.append(f"127.0.0.1 {domain}")
    block_lines.append(BLOCK_END)
    
    # Write clean hosts + zenpost block
    content = content.rstrip("\n") + "\n\n" + "\n".join(block_lines) + "\n"
    _write_hosts(content)
    
    # Update config
    config = load_config()
    config["blocked"] = all_platforms
    save_config(config)
    
    return all_platforms
