"""Apply pipeline: write files, validate the flake, commit to git.

Safety model:
  * the diff is available for preview before anything is written,
  * validation failure rolls every file back to its previous content,
  * each applied plan becomes one git commit, so `git revert` undoes it.

When `nix` or `git` aren't available (e.g. developing the tool off-NixOS)
the corresponding stage is skipped and reported, never silently.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .edits import EditPlan

VALIDATE_TIMEOUT = 300


@dataclass
class ApplyResult:
    ok: bool
    message: str
    validated: bool = False
    committed: bool = False
    commit_hash: str | None = None
    rolled_back: bool = False
    output: str = ""
    written: list[Path] = field(default_factory=list)


def _run(cmd: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
    )


class Pipeline:
    def __init__(self, root: Path, validate: bool = True, commit: bool = True):
        self.root = root
        self.validate = validate
        self.commit = commit

    def nix_available(self) -> bool:
        return shutil.which("nix") is not None

    def git_available(self) -> bool:
        if shutil.which("git") is None:
            return False
        try:
            res = _run(["git", "rev-parse", "--is-inside-work-tree"], self.root)
        except (OSError, subprocess.TimeoutExpired):
            return False
        return res.returncode == 0 and res.stdout.strip() == "true"

    def preview(self, plan: EditPlan) -> str:
        return plan.diff()

    def apply(self, plan: EditPlan) -> ApplyResult:
        if not plan.edits:
            return ApplyResult(ok=False, message="Nothing to apply")

        # 1. Write
        written: list[Path] = []
        try:
            for edit in plan.edits:
                edit.path.parent.mkdir(parents=True, exist_ok=True)
                edit.path.write_text(edit.after)
                written.append(edit.path)
        except OSError as exc:
            self._rollback(plan, written)
            return ApplyResult(
                ok=False,
                message=f"Failed writing {exc.filename}: {exc.strerror}",
                rolled_back=True,
            )

        # 2. Validate
        validated = False
        if self.validate:
            if self.nix_available():
                try:
                    res = _run(
                        ["nix", "flake", "check", "--no-build",
                         "--extra-experimental-features", "nix-command flakes"],
                        self.root,
                        timeout=VALIDATE_TIMEOUT,
                    )
                except subprocess.TimeoutExpired:
                    self._rollback(plan, written)
                    return ApplyResult(
                        ok=False,
                        message="Validation timed out; changes rolled back",
                        rolled_back=True,
                    )
                if res.returncode != 0:
                    self._rollback(plan, written)
                    return ApplyResult(
                        ok=False,
                        message="nix flake check failed; changes rolled back",
                        output=res.stderr.strip(),
                        rolled_back=True,
                    )
                validated = True
            # nix missing: proceed, but say so in the final message.

        # 3. Commit
        committed = False
        commit_hash = None
        commit_msg = ""
        if self.commit and self.git_available():
            rels = [str(p) for p in written]
            add = _run(["git", "add", "--", *rels], self.root)
            if add.returncode == 0:
                com = _run(
                    ["git", "commit", "-m", plan.description, "--", *rels], self.root
                )
                if com.returncode == 0:
                    committed = True
                    rev = _run(["git", "rev-parse", "--short", "HEAD"], self.root)
                    commit_hash = rev.stdout.strip() or None
                else:
                    commit_msg = com.stderr.strip() or com.stdout.strip()
            else:
                commit_msg = add.stderr.strip()

        parts = [f"Applied: {plan.description}"]
        if validated:
            parts.append("flake check passed")
        elif self.validate:
            parts.append("validation skipped (nix not available)")
        if committed:
            parts.append(f"committed {commit_hash}")
        elif self.commit:
            parts.append(
                f"git commit skipped ({commit_msg})" if commit_msg
                else "git commit skipped (not a git repo)"
            )
        return ApplyResult(
            ok=True,
            message="; ".join(parts),
            validated=validated,
            committed=committed,
            commit_hash=commit_hash,
            written=written,
        )

    def _rollback(self, plan: EditPlan, written: list[Path]) -> None:
        for edit in plan.edits:
            if edit.path not in written:
                continue
            try:
                if edit.create:
                    edit.path.unlink(missing_ok=True)
                else:
                    edit.path.write_text(edit.before)
            except OSError:
                pass  # best effort; git still has the pristine version
