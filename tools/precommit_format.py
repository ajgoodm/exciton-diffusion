import fnmatch
import subprocess as sp

EXCLUDE_PATHS = []


def run():
    """
    This method unstages files in the `EXCLUDE_PATHS` before running the precommit formatting.
    Then, once the precommit is run, restages all the excluded files.
    """
    result = sp.run(
        ["git", "diff", "--name-only", "--cached"], capture_output=True, check=True
    )
    staged_files = result.stdout.decode("utf-8").split()
    exclude = set()
    for pattern in EXCLUDE_PATHS:
        exclude.update(fnmatch.filter(staged_files, pattern))
    for filename in exclude:
        sp.run(["git", "reset", "HEAD", filename], check=True)
   
    print("foo foo foo")

    for filename in exclude:
        sp.run(["git", "add", filename], check=True)
    if result.returncode != 0:
        exit(1)


if __name__ == "__main__":
    run()