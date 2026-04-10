"""Clone Java repositories and run the CK static-analysis tool on them."""

import os
import shutil
import stat
import subprocess
from pathlib import Path
from typing import Optional, Tuple

from config import Config


# CK CLI positional arguments:
#   <project_path> <use_jars> <max_files_per_partition> <variables_and_fields> <output_dir>
_CK_USE_JARS = "false"
_CK_MAX_FILES_PER_PARTITION = "0"
_CK_VARIABLES_AND_FIELDS = "false"

_CLONE_TIMEOUT_SECONDS = 60 * 30  # 30 minutes
_CK_TIMEOUT_SECONDS = 60 * 30     # 30 minutes

# Maximum number of characters of subprocess stderr to surface as a reason.
# Keeps the failures.csv readable and avoids 10 KB stack traces in rows.
_MAX_REASON_CHARS = 300

# Type alias for "did it work + why not if it failed"
RunResult = Tuple[bool, Optional[str]]


def _run(cmd: list, cwd: Optional[Path] = None, timeout: Optional[int] = None) -> subprocess.CompletedProcess:
    """Run a subprocess command and return the completed process."""
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _extract_reason(text: str) -> str:
    """
    Return the most informative line of a subprocess' stderr.

    Git prints ``Cloning into '...'`` on stdout/stderr before the real
    error (``fatal:`` or ``error:``), and java similarly prefixes
    diagnostic lines. We prefer lines starting with ``fatal:``,
    ``error:``, or ``Error:`` if any exist; otherwise fall back to the
    last non-empty line (which is usually the most specific); otherwise
    to the first non-empty line. Result is trimmed to _MAX_REASON_CHARS.
    """
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    if not lines:
        return (text or "").strip()[:_MAX_REASON_CHARS]

    for line in lines:
        low = line.lower()
        if low.startswith(("fatal:", "error:", "exception")):
            return line[:_MAX_REASON_CHARS]

    return lines[-1][:_MAX_REASON_CHARS]


def _clone_repository(owner: str, name: str, target_dir: Path) -> RunResult:
    """
    Shallow-clone *owner/name* into *target_dir*.

    Returns (ok, reason). On success reason is None. On failure reason is
    a short human-readable string suitable for a failures.csv row.
    If *target_dir* already exists and is non-empty, assume a previous
    clone succeeded and return (True, None).
    """
    if target_dir.exists() and any(target_dir.iterdir()):
        return True, None

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    url = f"https://github.com/{owner}/{name}.git"
    try:
        result = _run(
            [Config.GIT_BIN, "clone", "--depth", "1", url, str(target_dir)],
            timeout=_CLONE_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        reason = f"git clone timed out after {_CLONE_TIMEOUT_SECONDS}s"
        print(f"    [ERROR] {reason} for {owner}/{name}")
        return False, reason
    except (FileNotFoundError, OSError) as exc:
        reason = f"git executable not found ({Config.GIT_BIN}): {exc}"
        print(f"    [ERROR] {reason}")
        return False, reason

    if result.returncode != 0:
        reason = f"git clone failed: {_extract_reason(result.stderr)}"
        print(f"    [ERROR] {reason} ({owner}/{name})")
        return False, reason

    return True, None


def _run_ck(project_path: Path, ck_output_dir: Path) -> RunResult:
    """
    Execute the CK JAR against *project_path*, writing CSVs into *ck_output_dir*.

    Returns (ok, reason) with the same semantics as _clone_repository.
    """
    ck_jar = Path(Config.CK_JAR_PATH)
    if not ck_jar.is_file():
        reason = f"CK jar not found at {ck_jar}"
        print(f"    [ERROR] {reason}")
        return False, reason

    ck_output_dir.mkdir(parents=True, exist_ok=True)

    # CK expects an output prefix; trailing separator keeps files inside the dir.
    output_prefix = f"{ck_output_dir}/"

    try:
        result = _run(
            [
                Config.JAVA_BIN,
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
        reason = f"CK timed out after {_CK_TIMEOUT_SECONDS}s"
        print(f"    [ERROR] {reason} for {project_path}")
        return False, reason
    except (FileNotFoundError, OSError) as exc:
        reason = f"java executable not found ({Config.JAVA_BIN}): {exc}"
        print(f"    [ERROR] {reason}")
        return False, reason

    if result.returncode != 0:
        reason = f"CK exited with code {result.returncode}: {_extract_reason(result.stderr)}"
        print(f"    [ERROR] {reason} ({project_path})")
        return False, reason

    class_csv = ck_output_dir / Config.CK_CLASS_FILE
    if not class_csv.is_file():
        reason = f"CK produced no {Config.CK_CLASS_FILE}"
        print(f"    [ERROR] {reason} in {ck_output_dir}")
        return False, reason

    return True, None


def _safe_rmtree(path: Path) -> None:
    """
    Remove *path* recursively, handling Windows read-only files (git packs).

    Git writes ``.git/objects/pack/*.pack`` and ``*.idx`` as read-only on
    Windows, which causes ``shutil.rmtree`` to leave them behind. We clear
    the read-only bit on every entry before calling rmtree.
    """
    if not path.exists():
        return
    for root, dirs, files in os.walk(path):
        for entry in dirs + files:
            full = os.path.join(root, entry)
            try:
                os.chmod(full, stat.S_IWRITE)
            except OSError:
                pass
    shutil.rmtree(path, ignore_errors=True)


def clone_and_run_ck(
    owner: str,
    name: str,
    repos_base: Path,
    ck_base: Path,
    keep_clone: bool = False,
) -> Tuple[Optional[Path], Optional[str]]:
    """
    Clone *owner/name* and run CK on it.

    Creates ``<repos_base>/<owner>__<name>`` for the clone and
    ``<ck_base>/<owner>__<name>`` for the CK CSV outputs.

    Returns a ``(output_dir, error_reason)`` tuple:

    - On success: ``(Path(ck_output_dir), None)``
    - On clone failure: ``(None, "git clone failed: ...")``
    - On CK failure:    ``(None, "CK exited with code N: ...")``

    When *keep_clone* is False (default), the clone directory is removed
    after CK finishes (or after the clone fails) to save disk space.
    """
    safe_key = f"{owner}__{name}"
    clone_dir = repos_base / safe_key
    ck_output_dir = ck_base / safe_key

    clone_ok, clone_reason = _clone_repository(owner, name, clone_dir)
    if not clone_ok:
        _safe_rmtree(clone_dir)
        return None, clone_reason

    ck_ok, ck_reason = _run_ck(clone_dir, ck_output_dir)

    if not keep_clone:
        _safe_rmtree(clone_dir)

    if not ck_ok:
        return None, ck_reason

    return ck_output_dir, None
