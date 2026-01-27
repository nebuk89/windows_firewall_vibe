# windows_firewall_vibe

A demonstration repository for Windows Firewall configuration and Remote Desktop Protocol (RDP) access to GitHub Actions Windows runners using reverse tunnels.

## Overview

This repository contains several GitHub Actions workflows:

1. **Windows Firewall Demo** (`windows_test.yml`) - Demonstrates blocking/allowing outbound traffic
2. **RDP via Chrome Remote Desktop** (`rdp_chrome.yml`) - ✅ **Working RDP access** using Chrome Remote Desktop (easiest, no account required)
3. **RDP via ngrok** (`rdp_ngrok.yml`) - ✅ **Working RDP access** using ngrok reverse tunnel
4. **RDP via Cloudflare Tunnel** (`rdp_cloudflared.yml`) - ✅ **Working RDP access** using Cloudflare tunnel (best performance)
5. **RDP Access Setup** (`rdp_access.yml`) - Original demonstration (connections blocked by GitHub network)

## 🍎 Mac Users: All Solutions Work!

All three RDP access methods fully support Mac:

- **Chrome Remote Desktop** (Easiest) - Works in any browser (Safari, Chrome, Firefox). Just go to [remotedesktop.google.com/access](https://remotedesktop.google.com/access)
- **ngrok** - Use [Microsoft Remote Desktop](https://apps.apple.com/app/microsoft-remote-desktop/id1295203466) from the Mac App Store (free)
- **Cloudflare Tunnel** - Install cloudflared with `brew install cloudflared`, then use Microsoft Remote Desktop

👉 **Recommended for Mac**: Chrome Remote Desktop (no installation needed) or ngrok (traditional RDP experience)

## 🎉 Working RDP Access Workflows

### Option 1: Chrome Remote Desktop (Easiest - Recommended)

The `rdp_chrome.yml` workflow uses Google's Chrome Remote Desktop for browser-based access. **Only a Google account is needed** - no additional client software or tunnel services required.

#### Prerequisites
1. A Google account
2. Access to https://remotedesktop.google.com/headless

#### How to Use
1. Go to [https://remotedesktop.google.com/headless](https://remotedesktop.google.com/headless)
2. Click **"Begin"** and **"Next"**
3. Authorize with your Google account
4. Give your remote computer a name
5. Copy the entire command shown (the Windows command for setting up the remote desktop host)
6. Go to the **Actions** tab in this repository
7. Select **"RDP via Chrome Remote Desktop"** workflow
8. Click **"Run workflow"**
9. Paste the command in the **"authcode"** field
10. Enter a 6-digit PIN in the **"pincode"** field (you'll use this to connect)
11. Wait for the workflow to complete setup (about 2-3 minutes)
12. Go to [https://remotedesktop.google.com/access](https://remotedesktop.google.com/access)
13. Find your computer in the "Remote devices" section and click it
14. Enter your 6-digit PIN to connect
15. When done, cancel the workflow to stop the session

**Features:**
- ✅ **Easiest setup** - Just need a Google account
- ✅ **No client software** - Works in any web browser
- ✅ **Cross-platform** - Connect from Windows, Mac, Linux, ChromeOS, or mobile
- ✅ **Full desktop GUI** - Complete visual access to the Windows desktop
- ✅ **Very responsive** - Good performance for interactive work
- ❌ **No audio support** - Chrome Remote Desktop doesn't support audio streaming

### Option 2: RDP via ngrok

The `rdp_ngrok.yml` workflow uses ngrok to create a reverse tunnel, bypassing GitHub's network restrictions and enabling **actual RDP connectivity**.

#### Prerequisites
1. Create a free ngrok account at [https://dashboard.ngrok.com/signup](https://dashboard.ngrok.com/signup)
2. Get your auth token from [https://dashboard.ngrok.com/auth](https://dashboard.ngrok.com/auth)
3. Configure repository secrets:
   - `NGROK_AUTH_TOKEN` - Your ngrok authentication token
   - `PASSWORD` - Password for the RDP connection

#### How to Use
1. Go to the **Actions** tab in this repository
2. Select **"RDP via ngrok"** workflow
3. Click **"Run workflow"**
4. Select your preferred ngrok region (us, eu, ap, au, sa, jp, in)
5. Wait for the workflow to start (about 30 seconds)
6. The workflow logs will display connection information like: `tcp://0.tcp.ngrok.io:12345`
7. Open your RDP client and connect to the displayed address:
   - **Windows**: Remote Desktop Connection (mstsc.exe)
   - **Mac**: Microsoft Remote Desktop (download from [Mac App Store](https://apps.apple.com/app/microsoft-remote-desktop/id1295203466))
   - **Linux**: Remmina or other RDP client
8. Login with username `runneradmin` and your PASSWORD secret
9. When done, cancel the workflow to stop the session

**Features:**
- ✅ Simple setup with just an auth token
- ✅ Works immediately after workflow starts
- ✅ **Traditional RDP client** - Use Windows Remote Desktop Connection
- ✅ Multiple region options for better latency
- ❌ Requires ngrok account and configuration

### Option 3: RDP via Cloudflare Tunnel (Best Performance)

The `rdp_cloudflared.yml` workflow uses Cloudflare Tunnel for better performance and lower latency.

#### Prerequisites
1. Configure repository secret:
   - `PASSWORD` - Password for the RDP connection
2. Download cloudflared on your local machine (one-time setup)

#### How to Use
1. Go to the **Actions** tab in this repository
2. Select **"RDP via Cloudflare Tunnel"** workflow
3. Click **"Run workflow"**
4. Wait for the workflow to start and display the tunnel URL
5. On your local machine, download cloudflared:
   - **Windows**: [Download cloudflared-windows-amd64.exe](https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe)
   - **macOS**: `brew install cloudflared`
   - **Linux**: [See releases](https://github.com/cloudflare/cloudflared/releases/latest)
6. Run the local tunnel command (shown in workflow logs):
   ```bash
   cloudflared access rdp --hostname <tunnel-url> --url localhost:13389
   ```
7. Open your RDP client and connect to `localhost:13389`:
   - **Windows**: Remote Desktop Connection (mstsc.exe)
   - **Mac**: Microsoft Remote Desktop (download from [Mac App Store](https://apps.apple.com/app/microsoft-remote-desktop/id1295203466))
   - **Linux**: Remmina or other RDP client
8. Login with username `runneradmin` and your PASSWORD secret
9. When done, cancel the workflow to stop the session

**Features:**
- ✅ Better performance and lower latency than ngrok
- ✅ No account or authentication required
- ✅ Enterprise-grade Cloudflare infrastructure
- ✅ More stable connections for longer sessions

## 📋 Comparison

| Feature | Chrome Remote Desktop | ngrok | Cloudflare Tunnel |
|---------|----------------------|-------|-------------------|
| Setup Difficulty | ⭐ Easiest | ⭐⭐ Easy | ⭐⭐⭐ Moderate |
| Performance | Good | Good | Excellent |
| Authentication Required | Google account only | Yes (free tier) | No |
| Client Software | Browser only | RDP client | cloudflared + RDP client |
| Connection Method | Browser-based | Direct RDP | Local tunnel + RDP |
| **Mac Support** | ✅ **Yes (browser)** | ✅ **Yes (MS Remote Desktop)** | ✅ **Yes (MS Remote Desktop)** |
| Windows Support | ✅ Yes | ✅ Yes | ✅ Yes |
| Linux Support | ✅ Yes | ✅ Yes | ✅ Yes |
| Audio Support | ❌ No | ✅ Yes | ✅ Yes |
| Best For | Quick GUI access | Traditional RDP users | Extended sessions |

## 🖥️ Original RDP Workflow (Non-Working)

The `rdp_access.yml` workflow is designed to enable RDP access to a GitHub Actions Windows runner for debugging and exploration purposes.

### How It Works

The workflow performs the following steps:

1. **Enables Remote Desktop** on the Windows runner
   ```powershell
   Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
   ```

2. **Configures Windows Firewall** to allow RDP connections
   ```powershell
   Enable-NetFirewallRule -DisplayGroup "Remote Desktop"
   ```
   This enables the built-in Windows Firewall rule group for Remote Desktop, which includes:
   - `Remote Desktop - User Mode (TCP-In)` - Allows RDP traffic on port 3389
   - `Remote Desktop - User Mode (UDP-In)` - Allows UDP traffic for RDP

3. **Creates an RDP user** with a randomly generated password and adds them to:
   - `Remote Desktop Users` group (for RDP access)
   - `Administrators` group (for full system access during exploration)

4. **Displays connection information** including:
   - Public IP address
   - RDP credentials (username and password)
   - Connection instructions

5. **Waits for 5 minutes** to allow time for connection before cleaning up

### ⚠️ Important Limitations

**Direct RDP connections to GitHub Actions runners will NOT work** due to network-level restrictions:

1. **GitHub Network Policies**: GitHub Actions runners are hosted on Microsoft Azure infrastructure behind GitHub's network security policies. Inbound connections from the internet (including RDP on port 3389) are blocked at the network level.

2. **No Public Inbound Access**: While the runner has a public IP address, inbound traffic is blocked by GitHub's network infrastructure before it reaches the runner's Windows Firewall.

3. **Windows Firewall is Configured Correctly**: The workflow successfully enables the Windows Firewall rules for RDP, but this is not sufficient because the traffic is blocked upstream by GitHub's network.

### What Works and What Doesn't

✅ **What the workflow configures correctly:**
- Windows Remote Desktop service is enabled
- Windows Firewall rules for RDP are enabled (inbound on port 3389)
- RDP user account is created with proper permissions
- No additional firewall configuration is needed

❌ **Why connections fail:**
- GitHub's network infrastructure blocks inbound connections
- This is a security feature, not a bug
- No amount of Windows Firewall configuration will bypass this

### 🔧 Alternative Approaches

If you need other ways to interact with a GitHub Actions Windows runner:

1. **Use GitHub Actions debugging features**:
   - Add shell commands to inspect the runner state
   - Use `upload-artifact` to save files/logs for inspection
   - Use `tmate` or similar SSH-based debugging tools (see [action-tmate](https://github.com/mxschmitt/action-tmate))

2. **Run the workflow on a self-hosted runner** where you control the network configuration

### 🚀 Running the Original Workflow

To run the original (non-working) RDP Access workflow:

1. Navigate to the **Actions** tab in this repository
2. Select **"RDP Access Setup"** workflow
3. Click **"Run workflow"** button
4. The workflow will display connection information in the logs and job summary
5. Note: Direct connections will fail due to GitHub's network restrictions

**Important:** This workflow demonstrates the limitations. For actual working RDP access, use the ngrok or Cloudflare Tunnel workflows above.

### 📝 Security Notice

⚠️ This workflow displays RDP credentials in plaintext in the workflow logs. This is intentional for debugging/exploration purposes only. **Do NOT use this workflow with sensitive data or production systems.**

The workflow is designed for:
- Learning about Windows Firewall configuration
- Understanding RDP setup on Windows systems
- Exploring GitHub Actions Windows runners (with limitations noted above)

## 🛡️ Windows Firewall Workflow

The `windows_test.yml` workflow demonstrates how to:

1. Test internet connectivity before firewall changes
2. Block all outbound traffic using Windows Firewall
3. Verify that traffic is blocked
4. Restore original firewall configuration

This is a demonstration of outbound traffic control and is separate from the RDP inbound access topic.

## 📚 Additional Resources

- [Windows Firewall Documentation](https://learn.microsoft.com/en-us/windows/security/threat-protection/windows-firewall/windows-firewall-with-advanced-security)
- [Remote Desktop Protocol Documentation](https://learn.microsoft.com/en-us/windows-server/remote/remote-desktop-services/clients/remote-desktop-clients)
- [GitHub Actions Network Configuration](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#networking)