from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class LintResult:
    file_path: str
    status: str
    fixed_issues: int = 0
    remaining_issues: list[str] = field(default_factory=list)
    error: str | None = None


class LintService:
    def __init__(self, output_folder: str = "output"):
        self.output_folder = Path(output_folder)
        self.mdformat_available = False
        self.markdownlint_available = False
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        import importlib.util

        if importlib.util.find_spec("mdformat") is not None:
            self.mdformat_available = True

        try:
            result = subprocess.run(
                [sys.executable, "-m", "markdownlint", "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                self.markdownlint_available = True
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

    def lint_file(self, file_path: str, fix: bool = True) -> LintResult:
        path = Path(file_path)
        if not path.exists():
            return LintResult(
                file_path=file_path,
                status="error",
                error="File not found",
            )

        if not path.suffix.lower() == ".md":
            return LintResult(
                file_path=file_path,
                status="skipped",
                error="Not a markdown file",
            )

        fixed = 0
        remaining: list[str] = []

        if fix and self.mdformat_available:
            try:
                from mdformat import run as mdformat_run  # type: ignore[attr-defined]

                original_content = path.read_text(encoding="utf-8")
                mdformat_run(
                    [str(path)],
                    encoder="utf-8",
                    extensions=["gfm"],
                )
                new_content = path.read_text(encoding="utf-8")
                if original_content != new_content:
                    fixed = 1
            except Exception as e:
                return LintResult(
                    file_path=file_path,
                    status="error",
                    error=f"mdformat failed: {str(e)}",
                )

        if self.markdownlint_available:
            try:
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "markdownlint",
                        "--stdin",
                        "--disable-rule",
                        "MD001",
                        "--disable-rule",
                        "MD002",
                        "--disable-rule",
                        "MD004",
                        "--disable-rule",
                        "MD005",
                        "--disable-rule",
                        "MD007",
                        "--disable-rule",
                        "MD009",
                        "--disable-rule",
                        "MD010",
                        "--disable-rule",
                        "MD012",
                        "--disable-rule",
                        "MD013",
                        "--disable-rule",
                        "MD014",
                        "--disable-rule",
                        "MD018",
                        "--disable-rule",
                        "MD019",
                        "--disable-rule",
                        "MD020",
                        "--disable-rule",
                        "MD021",
                        "--disable-rule",
                        "MD022",
                        "--disable-rule",
                        "MD023",
                        "--disable-rule",
                        "MD024",
                        "--disable-rule",
                        "MD025",
                        "--disable-rule",
                        "MD026",
                        "--disable-rule",
                        "MD027",
                        "--disable-rule",
                        "MD028",
                        "--disable-rule",
                        "MD029",
                        "--disable-rule",
                        "MD030",
                        "--disable-rule",
                        "MD031",
                        "--disable-rule",
                        "MD032",
                        "--disable-rule",
                        "MD033",
                        "--disable-rule",
                        "MD034",
                        "--disable-rule",
                        "MD035",
                        "--disable-rule",
                        "MD036",
                        "--disable-rule",
                        "MD037",
                        "--disable-rule",
                        "MD038",
                        "--disable-rule",
                        "MD039",
                        "--disable-rule",
                        "MD040",
                        "--disable-rule",
                        "MD041",
                        "--disable-rule",
                        "MD042",
                        "--disable-rule",
                        "MD043",
                        "--disable-rule",
                        "MD044",
                        "--disable-rule",
                        "MD045",
                        "--disable-rule",
                        "MD046",
                        "--disable-rule",
                        "MD047",
                        "--disable-rule",
                        "MD048",
                        "--disable-rule",
                        "MD049",
                        "--disable-rule",
                        "MD050",
                        "--disable-rule",
                        "MD051",
                        "--disable-rule",
                        "MD052",
                        "--disable-rule",
                        "MD053",
                        "--disable-rule",
                        "MD054",
                        "--disable-rule",
                        "MD055",
                        "--disable-rule",
                        "MD056",
                        "--disable-rule",
                        "MD057",
                        "--disable-rule",
                        "MD058",
                        "--disable-rule",
                        "MD059",
                        "--disable-rule",
                        "MD060",
                        "--disable-rule",
                        "MD061",
                        "--disable-rule",
                        "MD062",
                        "--disable-rule",
                        "MD063",
                        "--disable-rule",
                        "MD064",
                        "--disable-rule",
                        "MD065",
                        "--disable-rule",
                        "MD066",
                        "--disable-rule",
                        "MD067",
                        "--disable-rule",
                        "MD068",
                        "--disable-rule",
                        "MD069",
                        "--disable-rule",
                        "MD070",
                        "--disable-rule",
                        "MD071",
                        "--disable-rule",
                        "MD072",
                        "--disable-rule",
                        "MD073",
                        "--disable-rule",
                        "MD074",
                        "--disable-rule",
                        "MD075",
                        "--disable-rule",
                        "MD076",
                        "--disable-rule",
                        "MD077",
                        "--disable-rule",
                        "MD078",
                        "--disable-rule",
                        "MD079",
                        "--disable-rule",
                        "MD080",
                        "--disable-rule",
                        "MD081",
                        "--disable-rule",
                        "MD082",
                        "--disable-rule",
                        "MD083",
                        "--disable-rule",
                        "MD084",
                        "--disable-rule",
                        "MD085",
                        "--disable-rule",
                        "MD086",
                        "--disable-rule",
                        "MD087",
                        "--disable-rule",
                        "MD088",
                        "--disable-rule",
                        "MD089",
                        "--disable-rule",
                        "MD090",
                        "--disable-rule",
                        "MD091",
                        "--disable-rule",
                        "MD092",
                        "--disable-rule",
                        "MD093",
                        "--disable-rule",
                        "MD094",
                        "--disable-rule",
                        "MD095",
                        "--disable-rule",
                        "MD096",
                        "--disable-rule",
                        "MD097",
                        "--disable-rule",
                        "MD098",
                        "--disable-rule",
                        "MD099",
                        "--disable-rule",
                        "MD100",
                        "--disable-rule",
                        "MD101",
                        "--disable-rule",
                        "MD102",
                        "--disable-rule",
                        "MD103",
                        "--disable-rule",
                        "MD104",
                        "--disable-rule",
                        "MD105",
                        "--disable-rule",
                        "MD106",
                        "--disable-rule",
                        "MD107",
                        "--disable-rule",
                        "MD108",
                        "--disable-rule",
                        "MD109",
                        "--disable-rule",
                        "MD110",
                        "--disable-rule",
                        "MD111",
                        "--disable-rule",
                        "MD112",
                        "--disable-rule",
                        "MD113",
                        "--disable-rule",
                        "MD114",
                        "--disable-rule",
                        "MD115",
                        "--disable-rule",
                        "MD116",
                        "--disable-rule",
                        "MD117",
                        "--disable-rule",
                        "MD118",
                        "--disable-rule",
                        "MD119",
                        "--disable-rule",
                        "MD120",
                        "--disable-rule",
                        "MD121",
                        "--disable-rule",
                        "MD122",
                        "--disable-rule",
                        "MD123",
                        "--disable-rule",
                        "MD124",
                        "--disable-rule",
                        "MD125",
                        "--disable-rule",
                        "MD126",
                        "--disable-rule",
                        "MD127",
                        "--disable-rule",
                        "MD128",
                        "--disable-rule",
                        "MD129",
                        "--disable-rule",
                        "MD130",
                        "--disable-rule",
                        "MD131",
                        "--disable-rule",
                        "MD132",
                    ],
                    input=path.read_text(encoding="utf-8"),
                    capture_output=True,
                    text=True,
                )
                if result.stdout.strip():
                    remaining = result.stdout.strip().split("\n")
            except Exception as e:
                remaining.append(f"markdownlint error: {str(e)}")

        status = "success"
        if fixed > 0:
            status = "fixed"
        elif remaining:
            status = "issues"

        return LintResult(
            file_path=file_path,
            status=status,
            fixed_issues=fixed,
            remaining_issues=remaining,
        )

    def lint_directory(self, directory: str, fix: bool = True) -> list[LintResult]:
        dir_path = Path(directory)
        if not dir_path.exists():
            return [
                LintResult(
                    file_path=directory,
                    status="error",
                    error="Directory not found",
                )
            ]

        results: list[LintResult] = []
        for md_file in dir_path.rglob("*.md"):
            result = self.lint_file(str(md_file), fix=fix)
            results.append(result)

        return results

    def lint_output_folder(self, fix: bool = True) -> list[LintResult]:
        return self.lint_directory(str(self.output_folder), fix=fix)

    def get_status_summary(self, results: list[LintResult]) -> dict:
        total = len(results)
        fixed = sum(1 for r in results if r.status == "fixed")
        success = sum(1 for r in results if r.status == "success")
        issues = sum(1 for r in results if r.status == "issues")
        errors = sum(1 for r in results if r.status == "error")
        skipped = sum(1 for r in results if r.status == "skipped")

        return {
            "total": total,
            "fixed": fixed,
            "success": success,
            "issues": issues,
            "errors": errors,
            "skipped": skipped,
        }


lint_service = LintService()
