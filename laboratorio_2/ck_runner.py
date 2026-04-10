"""Clone Java repositories and run the CK static-analysis tool on them."""

import shutil
import subprocess
from pathlib import Path
from typing import Optional

from config import Config


# CK CLI positional arguments:
#   <project_path> <use_jars> <max_files_per_partition> <variables_and_fields> <output_dir>
_CK_USE_JARS = "false"
_CK_MAX_FILES_PER_PARTITION = "0"
_CK_VARIABLES_AND_FIELDS = "false"

_CLONE_TIMEOUT_SECONDS = 60 * 30  # 30 minutes
_CK_TIMEOUT_SECONDS = 60 * 30     # 30 minutes


def _run(cmd: list, cwd: Optional[Path] = None, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a subprocess command and return the completed process."""
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _clone_repository(owner: str, name: str, target_dir: Path) -> bool:
    """
    Shallow-clone *owner/name* into *target_dir*.

    Returns True on success, False otherwise. If *target_dir* already exists
    and is non-empty, assume a previous clone succeeded and return True.
    """
    if target_dir.exists() and any(target_dir.iterdir()):
        return True

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/{owner}/{name}.git"
    try:
        result = _run(
            ["git", "clone", "--depth", "1", url, str(target_dir)],
            timeout=_CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"    [ERROR] git clone timed out for {owner}/{name}")
        return False

    if result.returncode != 0:
        print(f"    [ERROR] git clone failed for {owner}/{name}: {result.stderr.strip()[:200]}")
        return False

    return True


def _run_ck(project_path: Path, ck_output_dir: Path) -> bool:
    """
    Execute the CK JAR against *project_path*, writing CSVs into *ck_output_dir*.

    CK writes files named like ``class.csv``, ``method.csv`` directly in the
    output directory, so *ck_output_dir* must exist beforehand.
    Returns True on success.
    """
    ck_jar = Path(Config.CK_JAR_PATH)
    if not ck_jar.is_file():
        print(f"    [ERROR] CK jar not found at {ck_jar}")
        return False

    ck_output_dir.mkdir(parents=True, exist_ok=True)

    # CK expects an output prefix; trailing separator keeps files inside the dir.
    output_prefix = f"{ck_output_dir}/"

    try:
        result = _run(
            [
                "java",
                "-jar",
                str(ck_jar),
                str(project_path),
                _CK_USE_JARS,
                _CK_MAX_FILES_PER_PARTITION,
                _CK_VARIABLES_AND_FIELDS,
                output_prefix,
            ],
            timeout=_CK_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(f"    [ERROR] CK timed out for {project_path}")
        return False

    if result.returncode != 0:
        print(f"    [ERROR] CK failed for {project_path}: {result.stderr.strip()[:200]}")
        return False

    class_csv = ck_output_dir / Config.CK_CLASS_FILE
    if not class_csv.is_file():
        print(f"    [ERROR] CK produced no {Config.CK_CLASS_FILE} in {ck_output_dir}")
        return False

    return True


def _safe_rmtree(path: Path) -> None:
    """Remove *path* recursively, ignoring missing directories and errors."""
    if not path.exists():
        return
    shutil.rmtree(path, ignore_errors=True)


def clone_and_run_ck(
    owner: str,
    name: str,
    repos_base: Path,
    ck_base: Path,
    keep_clone: bool = False,
) -> Optional[Path]:
    """
    Clone *owner/name* and run CK on it.

    Creates ``<repos_base>/<owner>__<name>`` for the clone and
    ``<ck_base>/<owner>__<name>`` for the CK CSV outputs. On success,
    returns the CK output directory. On any failure, returns None.

    When *keep_clone* is False (default), the clone directory is removed
    after CK finishes to save disk space.
    """
    safe_key = f"{owner}__{name}"
    clone_dir = repos_base / safe_key
    ck_output_dir = ck_base / safe_key

    if not _clone_repository(owner, name, clone_dir):
        _safe_rmtree(clone_dir)
        return None

    success = _run_ck(clone_dir, ck_output_dir)

    if not keep_clone:
        _safe_rmtree(clone_dir)

    return ck_output_dir if success else None
