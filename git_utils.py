import subprocess

def get_current_commit():
    try:
        result = subprocess.check_output(["git", "rev-parse", "HEAD"])
        return result.decode().strip()
    except:
        return "no_git_repo"