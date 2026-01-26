# windows_firewall_vibe

A demonstration repository for Windows Firewall configuration and Remote Desktop Protocol (RDP) setup on GitHub Actions runners.

## Overview

This repository contains two GitHub Actions workflows:

1. **Windows Firewall Demo** (`windows_test.yml`) - Demonstrates blocking/allowing outbound traffic
2. **RDP Access Setup** (`rdp_access.yml`) - Sets up Remote Desktop access to GitHub Actions Windows runners

## 🖥️ RDP Access Workflow

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

If you need to interact with a GitHub Actions Windows runner, consider these alternatives:

1. **Use a reverse tunnel service** like:
   - [ngrok](https://ngrok.com/) - Create a tunnel from the runner to your local machine
   - [CloudFlare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) - Similar tunneling service
   - [Tailscale](https://tailscale.com/) - Create a private network overlay

2. **Use GitHub Actions debugging features**:
   - Add shell commands to inspect the runner state
   - Use `upload-artifact` to save files/logs for inspection
   - Use `tmate` or similar SSH-based debugging tools

3. **Run the workflow on a self-hosted runner** where you control the network configuration

### 🚀 Running the Workflow

To run the RDP Access workflow:

1. Navigate to the **Actions** tab in this repository
2. Select **"RDP Access Setup"** workflow
3. Click **"Run workflow"** button
4. The workflow will display connection information in the logs and job summary
5. Note: Direct connections will fail due to GitHub's network restrictions (see above)

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

- [Windows Firewall Documentation](https://docs.microsoft.com/en-us/windows/security/threat-protection/windows-firewall/windows-firewall-with-advanced-security)
- [Remote Desktop Protocol Documentation](https://docs.microsoft.com/en-us/windows-server/remote/remote-desktop-services/clients/remote-desktop-clients)
- [GitHub Actions Network Configuration](https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners#networking)