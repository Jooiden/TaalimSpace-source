"""Export reviewed source directories only; never export local data or credentials."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parent.parent
DIRECTORIES = ("app", "src", "shared", "public", "migrations", "tests", "scripts", "docs")
FILES = ("Dockerfile", ".dockerignore", ".gitignore", ".env.example", "render.yaml",
    "vercel.json", "package.json", "pnpm-lock.yaml", "pnpm-workspace.yaml", "requirements.txt",
    "requirements-dev.txt", "index.html", "tsconfig.json", "vite.config.ts", "alembic.ini",
    "README.md", "SPEC.md", "AGENTS.md")


def main() -> None:
    from app.config import get_settings
    settings = get_settings()
    secrets = [settings.database_url] + [getattr(settings, key).get_secret_value() for key in (
        "groq_api_key", "brevo_api_key", "auth_secret", "smtp_password", "vapid_private_key",
        "stripe_secret_key", "stripe_webhook_secret")]
    needles = [value.encode() for value in secrets if len(value) >= 12]
    paths = [ROOT / name for name in FILES]
    for directory in DIRECTORIES:
        paths.extend(path for path in (ROOT / directory).rglob("*") if path.is_file()
            and "__pycache__" not in path.parts and path.suffix not in {".pyc", ".pyo"}
            and not path.name.startswith(".env"))
    for path in paths:
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"Invalid release entry: {path.relative_to(ROOT)}")
        if any(secret in path.read_bytes() for secret in needles):
            raise RuntimeError(f"Credential detected; export stopped: {path.relative_to(ROOT)}")
    target = ROOT / "artifacts" / "TaalimSpace-source.zip"
    target.parent.mkdir(exist_ok=True)
    with ZipFile(target, "w", ZIP_DEFLATED) as archive:
        for path in sorted(set(paths)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Release: {target.name}; {len(set(paths))} files; {target.stat().st_size} bytes. Credential scan passed.")


if __name__ == "__main__":
    main()
