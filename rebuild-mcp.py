"""Regenerate just the committed MCP artifact from the five route declarations."""

import os
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parent
ENDPOINTS = ",".join(f"GET {path}" for path in (
    "/parts", "/locations", "/bom/{part_id}", "/stock/{part_id}", "/incoming/{part_id}",
))


def main():
    npx = "npx.cmd" if os.name == "nt" else "npx"
    with TemporaryDirectory(prefix="kit-readiness-synapse-") as staging:
        target = Path(staging)
        shutil.copyfile(ROOT / "inventory_api.py", target / "inventory_api.py")
        subprocess.run([
            npx, "--yes", "@2ndbrainlabs-ai/synapse-cli@0.1.9", "build",
            "--local", "--provider", "ollama", "--auto",
            "--base-url", "http://127.0.0.1:8410", "--server-name", "kit-readiness",
            "--endpoints", ENDPOINTS,
        ], cwd=target, env={**os.environ, "SYNAPSE_TELEMETRY": "0"}, check=True)
        shutil.copyfile(target / "synapse_auto_server.py", ROOT / "synapse_auto_server.py")
    print(f"Generated {ROOT / 'synapse_auto_server.py'}")


if __name__ == "__main__":
    main()
