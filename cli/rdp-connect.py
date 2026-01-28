#!/usr/bin/env python3
"""
rdp-connect: CLI tool to start and connect to a Cloudflare Tunnel RDP session
on a GitHub Actions Windows runner.

Prerequisites:
  - Python 3.8+
  - cloudflared installed locally (brew install cloudflared / winget install Cloudflare.cloudflared)
  - GitHub CLI (gh) authenticated, OR a GITHUB_TOKEN environment variable

Usage:
  ./cli/rdp-connect.py [--repo OWNER/REPO] [--local-port PORT]

Example:
  ./cli/rdp-connect.py --repo nebuk89/windows_firewall_vibe --local-port 13389
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_REPO = "nebuk89/windows_firewall_vibe"
DEFAULT_LOCAL_PORT = 13389
WORKFLOW_FILE = "rdp_cloudflared.yml"
POLL_INTERVAL_SECONDS = 10
MAX_WAIT_SECONDS = 600  # 10 minutes max to wait for tunnel URL


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def log(msg: str, level: str = "info"):
    symbols = {"info": "ℹ️ ", "ok": "✅ ", "warn": "⚠️ ", "err": "❌ ", "wait": "⏳ "}
    print(f"{symbols.get(level, '')}{msg}")


def run_gh(*args, capture=True) -> subprocess.CompletedProcess:
    """Run a GitHub CLI command."""
    cmd = ["gh"] + list(args)
    return subprocess.run(cmd, capture_output=capture, text=True)


def generate_rdp_file(host: str, port: int, username: str = "runneradmin") -> str:
    """Generate an RDP file and return the path."""
    rdp_content = f"""full address:s:{host}:{port}
username:s:{username}
screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
authentication level:i:0
prompt for credentials:i:1
negotiate security layer:i:1
remoteapplicationmode:i:0
alternate shell:s:
shell working directory:s:
gatewayhostname:s:
gatewayusagemethod:i:4
gatewaycredentialssource:i:4
gatewayprofileusagemethod:i:0
promptcredentialonce:i:0
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
drivestoredirect:s:
"""
    # Create a temp file that persists (user will need it)
    fd, rdp_path = tempfile.mkstemp(suffix=".rdp", prefix="github-rdp-")
    with os.fdopen(fd, "w") as f:
        f.write(rdp_content)
    return rdp_path


def open_rdp_file(rdp_path: str) -> bool:
    """Open the RDP file with the system's default handler."""
    system = platform.system()
    try:
        if system == "Darwin":  # macOS
            subprocess.run(["open", rdp_path], check=True)
        elif system == "Windows":
            os.startfile(rdp_path)
        else:  # Linux and others
            subprocess.run(["xdg-open", rdp_path], check=True)
        return True
    except Exception as e:
        log(f"Failed to open RDP file: {e}", "warn")
        return False


def get_token() -> str:
    """Return a GitHub token from env or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    result = run_gh("auth", "token")
    if result.returncode == 0:
        return result.stdout.strip()
    log("Could not get GitHub token. Run 'gh auth login' or set GITHUB_TOKEN.", "err")
    sys.exit(1)


def check_cloudflared() -> str:
    """Return path to cloudflared binary or exit."""
    path = shutil.which("cloudflared")
    if not path:
        log("cloudflared not found. Install it first:", "err")
        log("  macOS:   brew install cloudflared", "info")
        log("  Windows: winget install Cloudflare.cloudflared", "info")
        log("  Linux:   https://github.com/cloudflare/cloudflared/releases", "info")
        sys.exit(1)
    return path


# ─────────────────────────────────────────────────────────────────────────────
# GitHub API helpers (using gh CLI for simplicity)
# ─────────────────────────────────────────────────────────────────────────────
def trigger_workflow(repo: str, workflow: str) -> int:
    """Trigger workflow_dispatch and return the run ID."""
    log(f"Triggering workflow '{workflow}' in {repo}...", "wait")

    # Trigger the workflow
    result = run_gh("workflow", "run", workflow, "--repo", repo)
    if result.returncode != 0:
        log(f"Failed to trigger workflow: {result.stderr}", "err")
        sys.exit(1)

    # Wait a moment for GitHub to register the run
    time.sleep(3)

    # Get the most recent run for this workflow
    result = run_gh(
        "run", "list",
        "--repo", repo,
        "--workflow", workflow,
        "--limit", "1",
        "--json", "databaseId,status,createdAt"
    )
    if result.returncode != 0:
        log(f"Failed to list workflow runs: {result.stderr}", "err")
        sys.exit(1)

    runs = json.loads(result.stdout)
    if not runs:
        log("No workflow run found after trigger.", "err")
        sys.exit(1)

    run_id = runs[0]["databaseId"]
    log(f"Workflow run started: ID {run_id}", "ok")
    return run_id


def get_run_status(repo: str, run_id: int) -> dict:
    """Get workflow run status."""
    result = run_gh(
        "run", "view", str(run_id),
        "--repo", repo,
        "--json", "status,conclusion,jobs"
    )
    if result.returncode != 0:
        return {"status": "unknown", "conclusion": None, "jobs": []}
    return json.loads(result.stdout)


def get_job_logs(repo: str, run_id: int) -> str:
    """Fetch logs for the workflow run."""
    result = run_gh("run", "view", str(run_id), "--repo", repo, "--log")
    if result.returncode != 0:
        return ""
    return result.stdout


def extract_tunnel_url(logs: str) -> str | None:
    """Extract the Cloudflare tunnel URL from logs."""
    # Look for the tunnel URL pattern
    # The workflow outputs: "🌐 Tunnel URL: xxx.trycloudflare.com"
    # or the cloudflared command line
    patterns = [
        r"Tunnel URL:\s*([a-zA-Z0-9\-]+\.trycloudflare\.com)",
        r"--hostname\s+([a-zA-Z0-9\-]+\.trycloudflare\.com)",
        r"(https?://[a-zA-Z0-9\-]+\.trycloudflare\.com)",
    ]
    for pattern in patterns:
        match = re.search(pattern, logs)
        if match:
            url = match.group(1)
            # Clean up - remove https:// if present
            url = re.sub(r"^https?://", "", url)
            return url
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Start a Cloudflare Tunnel RDP session on a GitHub Actions Windows runner."
    )
    parser.add_argument(
        "--repo", "-r",
        default=DEFAULT_REPO,
        help=f"GitHub repository (default: {DEFAULT_REPO})"
    )
    parser.add_argument(
        "--local-port", "-p",
        type=int,
        default=DEFAULT_LOCAL_PORT,
        help=f"Local port to expose RDP on (default: {DEFAULT_LOCAL_PORT})"
    )
    parser.add_argument(
        "--run-id",
        type=int,
        default=None,
        help="Attach to an existing workflow run instead of starting a new one"
    )
    args = parser.parse_args()

    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║         🖥️  GitHub Actions RDP via Cloudflare Tunnel          ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

    # Preflight checks
    cloudflared_path = check_cloudflared()
    log(f"cloudflared found: {cloudflared_path}", "ok")

    # Ensure we have GitHub access
    get_token()
    log("GitHub authentication OK", "ok")

    # Trigger or attach to workflow
    if args.run_id:
        run_id = args.run_id
        log(f"Attaching to existing run: {run_id}", "info")
    else:
        run_id = trigger_workflow(args.repo, WORKFLOW_FILE)

    # Poll for tunnel URL
    log("Waiting for tunnel URL to appear in logs...", "wait")
    start_time = time.time()
    tunnel_url = None

    while time.time() - start_time < MAX_WAIT_SECONDS:
        status = get_run_status(args.repo, run_id)

        if status.get("conclusion") == "failure":
            log("Workflow failed! Check the run logs for details.", "err")
            log(f"  gh run view {run_id} --repo {args.repo} --log", "info")
            sys.exit(1)

        if status.get("conclusion") == "cancelled":
            log("Workflow was cancelled.", "warn")
            sys.exit(1)

        # Try to get logs
        logs = get_job_logs(args.repo, run_id)
        tunnel_url = extract_tunnel_url(logs)

        if tunnel_url:
            log(f"Found tunnel URL: {tunnel_url}", "ok")
            break

        elapsed = int(time.time() - start_time)
        print(f"\r⏳ Waiting for tunnel... ({elapsed}s elapsed)", end="", flush=True)
        time.sleep(POLL_INTERVAL_SECONDS)

    print()  # Clear the waiting line

    if not tunnel_url:
        log(f"Timed out waiting for tunnel URL after {MAX_WAIT_SECONDS}s", "err")
        log("Check the workflow run manually:", "info")
        log(f"  gh run view {run_id} --repo {args.repo} --log", "info")
        sys.exit(1)

    # Start cloudflared
    print()
    log(f"Starting cloudflared tunnel to {tunnel_url}...", "wait")

    cloudflared_cmd = [
        cloudflared_path,
        "access", "rdp",
        "--hostname", tunnel_url,
        "--url", f"localhost:{args.local_port}"
    ]

    # Start cloudflared in background
    cloudflared_proc = subprocess.Popen(
        cloudflared_cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Give it a moment to start
    time.sleep(2)

    if cloudflared_proc.poll() is not None:
        log("cloudflared exited unexpectedly. Check if the port is in use.", "err")
        sys.exit(1)

    # Generate and open RDP file
    rdp_path = generate_rdp_file("localhost", args.local_port)
    log(f"Generated RDP file: {rdp_path}", "ok")

    # Success!
    print()
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    🎉 SESSION READY!                          ║")
    print("╠═══════════════════════════════════════════════════════════════╣")
    print(f"║  📍 Connect to: localhost:{args.local_port:<26}          ║")
    print("║  👤 Username:   runneradmin                                   ║")
    print("║  🔑 Password:   (your PASSWORD secret)                        ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

    # Open RDP client
    log("Launching RDP client...", "wait")
    if open_rdp_file(rdp_path):
        log("RDP client launched! Enter your password when prompted.", "ok")
    else:
        log(f"Could not auto-launch RDP. Open manually: {rdp_path}", "warn")

    print()
    log("Press Ctrl+C to disconnect and stop the tunnel.", "info")
    print()

    # Keep running until user interrupts
    try:
        while True:
            if cloudflared_proc.poll() is not None:
                log("cloudflared process exited.", "warn")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        print()
        log("Shutting down tunnel...", "info")
        cloudflared_proc.terminate()
        try:
            cloudflared_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cloudflared_proc.kill()
        log("Tunnel stopped. Don't forget to cancel the workflow!", "ok")
        log(f"  gh run cancel {run_id} --repo {args.repo}", "info")


if __name__ == "__main__":
    main()
