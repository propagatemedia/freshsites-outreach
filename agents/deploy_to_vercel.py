#!/usr/bin/env python3
"""
Vercel Deployment + Transfer Script
Deploys a demo page to a new Vercel project, creates a temp domain,
and prepares transfer to new owner.

Usage:
    PYTHONPATH="" ./.venv/bin/python3.11 agents/deploy_to_vercel.py demos/welshpool-autofit.html --transfer-to owner@email.com
"""

import os
import sys
from pathlib import Path
import subprocess
import json
import shutil

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

VERCEL_TOKEN = os.environ.get("VERCEL_API_TOKEN", "")


def check_vercel_cli():
    """Check if vercel CLI is installed."""
    vercel_path = Path.home() / ".local" / "bin" / "vercel"
    if vercel_path.exists():
        return str(vercel_path)
    # Try system path
    result = subprocess.run(["which", "vercel"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def create_deployment_package(html_path: Path, project_name: str):
    """Create a temporary deployment directory with the HTML as index.html."""
    deploy_dir = Path("/tmp") / f"freshsites-deploy-{project_name}"
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    deploy_dir.mkdir(parents=True)
    
    # Copy HTML as index.html
    shutil.copy(html_path, deploy_dir / "index.html")
    
    # Copy assets/images so they work on Vercel
    repo_root = Path(__file__).parent.parent
    src_assets = repo_root / "docs" / "assets"
    if src_assets.exists():
        dst_assets = deploy_dir / "assets"
        shutil.copytree(src_assets, dst_assets)
    
    # Create vercel.json for clean routing
    vercel_config = {
        "version": 2,
        "routes": [
            {"src": "/assets/(.*)", "dest": "/assets/$1"},
            {"src": "/(.*)", "dest": "/index.html"}
        ]
    }
    (deploy_dir / "vercel.json").write_text(json.dumps(vercel_config, indent=2))
    
    return deploy_dir


def deploy_to_vercel(deploy_dir: Path, project_name: str, token: str = ""):
    """Deploy to Vercel and return deployment URL."""
    vercel = check_vercel_cli()
    if not vercel:
        print("ERROR: Vercel CLI not found. Install with: npm i -g vercel")
        sys.exit(1)
    
    # Check if we have a token
    if not token:
        print("WARNING: No Vercel token. Will try to use existing login.")
        print("Run: vercel login")
    
    cmd = [vercel, "--yes", "--prod", "--cwd", str(deploy_dir)]
    if token:
        cmd.extend(["--token", token])
    
    print(f"Deploying {project_name} to Vercel...")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(deploy_dir)
    )
    
    if result.returncode != 0:
        print(f"Deploy failed: {result.stderr}")
        return None
    
    # Extract deployment URL from output
    output = result.stdout
    print(output)
    
    # Try to find the deployment URL
    for line in output.splitlines():
        if "https://" in line and ".vercel.app" in line:
            url = line.strip().split()[-1]
            print(f"Deployed to: {url}")
            return url
    
    return None


def generate_transfer_email(project_name: str, deploy_url: str, customer_email: str):
    """Generate email content for transferring ownership."""
    return f"""Subject: Your Welshpool Autofit website is live
To: {customer_email}
From: freshsites@sites.propagate.media

Hi there,

Your new website is live and ready:
{deploy_url}

WHAT WAS DELIVERED:
- Complete website deployed to Vercel
- Temporary domain: {deploy_url}
- Full source code included
- Mobile responsive, fast loading

NEXT STEPS:
1. Review your site at the link above
2. Set up your free Vercel account (takes 2 minutes)
3. We will transfer the project to your account
4. Connect your own custom domain (optional)

CONNECT A CUSTOM DOMAIN:
- Add your domain in Vercel dashboard
- Update DNS records (we will guide you)
- Takes about 5 minutes

QUESTIONS?
Just reply to this email or contact us at freshsites@sites.propagate.media

Best regards,
FreshSites Team
"""


def main():
    if len(sys.argv) < 2:
        print("Usage: deploy_to_vercel.py <html_file> [--transfer-to email@domain.com]")
        sys.exit(1)
    
    html_path = Path(sys.argv[1])
    if not html_path.exists():
        print(f"ERROR: File not found: {html_path}")
        sys.exit(1)
    
    # Parse args
    transfer_email = None
    if "--transfer-to" in sys.argv:
        idx = sys.argv.index("--transfer-to")
        if idx + 1 < len(sys.argv):
            transfer_email = sys.argv[idx + 1]
    
    # Determine project name from HTML filename
    project_name = html_path.stem.replace("-demo", "").replace("-", "-")
    safe_name = project_name.lower().replace("_", "-").replace(" ", "-")[:50]
    
    print(f"=" * 60)
    print(f"FreshSites Vercel Deploy")
    print(f"=" * 60)
    print(f"Source: {html_path}")
    print(f"Project: {safe_name}")
    print(f"Token: {'Set' if VERCEL_TOKEN else 'Not set (will use login)'}")
    print(f"Transfer: {transfer_email or 'Not requested'}")
    
    # Create deployment package
    deploy_dir = create_deployment_package(html_path, safe_name)
    print(f"\nCreated deploy package: {deploy_dir}")
    
    # Deploy
    deploy_url = deploy_to_vercel(deploy_dir, safe_name, VERCEL_TOKEN)
    
    if not deploy_url:
        print("\nDeploy failed. Check output above.")
        sys.exit(1)
    
    print(f"\n{'=' * 60}")
    print(f"DEPLOYED SUCCESSFULLY")
    print(f"{'=' * 60}")
    print(f"URL: {deploy_url}")
    
    if transfer_email:
        email = generate_transfer_email(safe_name, deploy_url, transfer_email)
        print(f"\nTransfer email prepared for: {transfer_email}")
        print("---")
        print(email)
        print("---")
        print("\nSend this email to the customer.")
    
    print(f"\nTo transfer ownership:")
    print(f"1. Customer creates Vercel account")
    print(f"2. Invite them to the project")
    print(f"3. They accept and we remove our access")
    print(f"\nDone.")


if __name__ == "__main__":
    main()
