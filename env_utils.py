import os

ENV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def read_env_key(key):
    """Reads a key's value from the .env file (raw file read, not os.getenv).
    Returns the value as a string, or None if the key is not found.
    """
    if not os.path.exists(ENV_FILE):
        return None
    with open(ENV_FILE, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("#") or "=" not in stripped:
                continue
            k, _, v = stripped.partition("=")
            if k.strip() == key:
                return v.strip()
    return None


def update_env_key(key, value):
    """Updates or inserts a key in the .env file.
    If the key already exists, its line is replaced.
    If not, the key=value pair is appended.
    Creates the .env file if it does not exist.
    """
    lines = []
    found = False

    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            lines = f.readlines()

    new_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("#") and "=" in stripped:
            k, _, _ = stripped.partition("=")
            if k.strip() == key:
                new_lines.append(f"{key}={value}\n")
                found = True
                continue
        new_lines.append(line)

    if not found:
        # Ensure there's a newline before appending if file doesn't end with one
        if new_lines and not new_lines[-1].endswith("\n"):
            new_lines.append("\n")
        new_lines.append(f"{key}={value}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(new_lines)
