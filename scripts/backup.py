"""Consistent database + photos backup with a short API maintenance window.

Run from the repository: python scripts/backup.py --directory /secure/backups
Copy the resulting directory to encrypted off-host storage. No retention/deletes.
"""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ["docker", "compose", "-f", str(ROOT / "compose.yaml")]


def run(args, **kwargs):
    return subprocess.run(COMPOSE + args, cwd=ROOT, check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", required=True)
    args = parser.parse_args()
    # Backups contain personal data and password hashes. Do not rely on the
    # host's common 022 umask, which makes new files readable to other users.
    os.umask(0o077)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = Path(args.directory).resolve() / f"velour-{stamp}"
    target.mkdir(parents=True, exist_ok=False, mode=0o700)
    running = run(["ps", "--status", "running", "--services"], capture_output=True, text=True).stdout.splitlines()
    if "api" not in running:
        raise SystemExit("A API deve estar ativa antes do backup; nenhuma alteração foi feita.")
    stopped = False
    try:
        run(["stop", "api"])
        stopped = True
        with (target / "database.dump").open("wb") as output:
            run(["exec", "-T", "db", "pg_dump", "-U", "velour", "-d", "velour", "-Fc"], stdout=output)
        with (target / "uploads.tar.gz").open("wb") as output:
            run(["run", "--rm", "--no-deps", "-T", "api", "tar", "-C", "/data/uploads", "-czf", "-", "."], stdout=output)
        manifest = {"created_at": stamp, "files": {}}
        for name in ("database.dump", "uploads.tar.gz"):
            with (target / name).open("rb") as stream:
                manifest["files"][name] = hashlib.file_digest(stream, "sha256").hexdigest()
        (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        print(f"Backup completo: {target}. Copie para armazenamento externo criptografado.")
    finally:
        if stopped:
            run(["start", "api"])


if __name__ == "__main__":
    main()
