#!/usr/bin/env python3
"""
Smart File Organizer
=====================
Task 2 deliverable: an automation script that solves a real repetitive
problem -- sorting a messy downloads/desktop folder into organized
sub-folders by file type, on a schedule, with logging and notifications.

Usage:
    python organizer.py --source ~/Downloads
    python organizer.py --source ~/Downloads --dry-run
    python organizer.py --source ~/Downloads --config my_rules.json
    python organizer.py --source ~/Downloads --watch --interval 3600

Author: Redynox Python Developer Intern
"""
import argparse
import json
import logging
import shutil
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Default categorization rules (used when no --config file is supplied)
# ---------------------------------------------------------------------------
DEFAULT_RULES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".odt", ".rtf"],
    "Spreadsheets": [".xls", ".xlsx", ".csv"],
    "Presentations": [".ppt", ".pptx"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Audio": [".mp3", ".wav", ".flac", ".aac"],
    "Video": [".mp4", ".mov", ".avi", ".mkv"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".json", ".sh"],
    "Installers": [".exe", ".msi", ".dmg", ".pkg", ".deb"],
}


def setup_logger(log_file: Path) -> logging.Logger:
    logger = logging.getLogger("file_organizer")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    return logger


def load_rules(config_path: str | None, logger: logging.Logger) -> dict:
    if config_path is None:
        return DEFAULT_RULES
    path = Path(config_path)
    if not path.exists():
        logger.warning(f"Config file '{config_path}' not found, falling back to default rules.")
        return DEFAULT_RULES
    try:
        with open(path) as f:
            rules = json.load(f)
        logger.info(f"Loaded custom categorization rules from {config_path}")
        return rules
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to read config file '{config_path}': {e}. Using default rules.")
        return DEFAULT_RULES


def category_for(extension: str, rules: dict) -> str:
    extension = extension.lower()
    for category, extensions in rules.items():
        if extension in extensions:
            return category
    return "Other"


def organize(source: Path, rules: dict, dry_run: bool, logger: logging.Logger) -> Counter:
    """Moves every file in `source` (non-recursive) into a category
    sub-folder. Returns a Counter of {category: file_count} for the
    summary/notification step."""
    if not source.exists():
        raise FileNotFoundError(f"Source directory does not exist: {source}")
    if not source.is_dir():
        raise NotADirectoryError(f"Source path is not a directory: {source}")

    stats = Counter()
    errors = 0

    files = [f for f in source.iterdir() if f.is_file()]
    logger.info(f"Scanning '{source}' -- {len(files)} file(s) found.")

    for file_path in files:
        category = category_for(file_path.suffix, rules)
        dest_dir = source / category
        dest_path = dest_dir / file_path.name

        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would move '{file_path.name}' -> {category}/")
            else:
                dest_dir.mkdir(exist_ok=True)
                # avoid overwriting an existing file with the same name
                if dest_path.exists():
                    stem, suffix = file_path.stem, file_path.suffix
                    counter = 1
                    while dest_path.exists():
                        dest_path = dest_dir / f"{stem}_{counter}{suffix}"
                        counter += 1
                shutil.move(str(file_path), str(dest_path))
                logger.info(f"Moved '{file_path.name}' -> {category}/{dest_path.name}")
            stats[category] += 1
        except (OSError, PermissionError) as e:
            logger.error(f"Failed to move '{file_path.name}': {e}")
            errors += 1

    stats["_errors"] = errors
    return stats


def notify(stats: Counter, dry_run: bool, logger: logging.Logger) -> None:
    """Console notification summary. In production this could be swapped
    for an smtplib email call or a Slack webhook without touching the
    rest of the script -- that's the point of keeping it a separate
    function."""
    errors = stats.pop("_errors", 0)
    total = sum(stats.values())

    mode = "DRY RUN — no files were moved" if dry_run else "COMPLETE"
    lines = [
        "",
        "=" * 50,
        f"  File Organizer Summary — {mode}",
        "=" * 50,
        f"  Total files processed : {total}",
    ]
    for category, count in sorted(stats.items(), key=lambda x: -x[1]):
        lines.append(f"    {category:<15s}: {count}")
    if errors:
        lines.append(f"  Errors                : {errors}")
    lines.append("=" * 50)

    summary = "\n".join(lines)
    print(summary)
    logger.info(f"Run summary: {dict(stats)} | errors={errors}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Automatically organize files in a directory by type."
    )
    parser.add_argument("--source", required=True, help="Directory to organize")
    parser.add_argument("--config", default=None, help="Path to a JSON rules file (optional)")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without moving files")
    parser.add_argument("--watch", action="store_true", help="Run continuously on a schedule")
    parser.add_argument("--interval", type=int, default=3600, help="Seconds between runs when --watch is set (default: 3600)")
    parser.add_argument("--log-file", default="organizer.log", help="Path to the log file")
    return parser.parse_args()


def run_once(source: Path, rules: dict, dry_run: bool, logger: logging.Logger) -> Counter:
    logger.info(f"--- Run started ({'dry-run' if dry_run else 'live'}) ---")
    stats = organize(source, rules, dry_run, logger)
    notify(stats, dry_run, logger)
    logger.info("--- Run finished ---")
    return stats


def main():
    args = parse_args()
    logger = setup_logger(Path(args.log_file))
    rules = load_rules(args.config, logger)
    source = Path(args.source).expanduser()

    try:
        if args.watch:
            logger.info(f"Watch mode enabled. Running every {args.interval}s. Press Ctrl+C to stop.")
            while True:
                run_once(source, rules, args.dry_run, logger)
                logger.info(f"Sleeping for {args.interval}s...")
                time.sleep(args.interval)
        else:
            run_once(source, rules, args.dry_run, logger)
    except (FileNotFoundError, NotADirectoryError) as e:
        logger.error(str(e))
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Stopped by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
