"""Generate a separate Compose environment without changing an existing .env."""
import base64
from pathlib import Path
import secrets


def main():
    root = Path(__file__).resolve().parents[1]
    destination = root / ".env.compose"
    existing = destination.read_text(encoding="utf-8") if destination.exists() else ""
    existing_keys = {line.split("=", 1)[0] for line in existing.splitlines() if "=" in line and not line.startswith("#")}
    lines = []
    for line in (root / ".env.example").read_text(encoding="utf-8").splitlines():
        if existing and ("=" not in line or line.split("=", 1)[0] in existing_keys):
            continue
        if line.endswith("=GENERATE_ME"):
            key = line.split("=", 1)[0]
            value = (base64.urlsafe_b64encode(secrets.token_bytes(32)).decode()
                     if key == "AIRFLOW_FERNET_KEY" else secrets.token_hex(32))
            line = f"{key}={value}"
        lines.append(line)
    if lines:
        with destination.open("a" if existing else "x", encoding="utf-8", newline="\n") as handle:
            handle.write(("\n" if existing else "") + "\n".join(lines) + "\n")
    print(".env.compose is ready; existing credentials preserved. Keep this file private.")


if __name__ == "__main__":
    main()
