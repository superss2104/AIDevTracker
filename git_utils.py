import subprocess


def get_current_commit():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"]
        ).decode("utf-8").strip()
        return commit
    except:
        return "No Git Repo"