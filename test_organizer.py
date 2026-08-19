"""
Sets up realistic messy test folders and runs organizer.py against them
under several scenarios, capturing real console output for the report:
  1. Dry run on a mixed folder
  2. Live run on the same folder
  3. Duplicate-filename collision handling
  4. Custom rules config file
  5. Error handling on a non-existent source directory
"""
import shutil
import subprocess
import sys
from pathlib import Path

TEST_ROOT = Path("test_sandbox")
TRANSCRIPT = Path("scenario_transcript.txt")


def reset(path: Path):
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def make_messy_folder(path: Path):
    path.mkdir(parents=True, exist_ok=True)
    files = [
        "vacation_photo.jpg", "screenshot.png", "resume.pdf", "notes.txt",
        "budget.xlsx", "sales_data.csv", "presentation.pptx", "archive.zip",
        "song.mp3", "movie_clip.mp4", "script.py", "setup.exe",
        "random_file.xyz",  # unknown extension -> "Other"
    ]
    for name in files:
        (path / name).write_text(f"dummy content for {name}")


def run(cmd, log):
    log.write(f"$ {' '.join(cmd)}\n")
    result = subprocess.run(cmd, capture_output=True, text=True)
    log.write(result.stdout)
    if result.stderr:
        log.write(result.stderr)
    log.write(f"(exit code: {result.returncode})\n\n")
    print(result.stdout)
    return result


def main():
    reset(TEST_ROOT)
    organizer = str(Path("organizer.py").resolve())

    with open(TRANSCRIPT, "w") as log:

        # --- Scenario 1: dry run ---
        log.write("SCENARIO 1: Dry run on a mixed folder (13 files, 12 known types + 1 unknown)\n")
        log.write("-" * 70 + "\n")
        scenario1 = TEST_ROOT / "scenario1_dry_run"
        make_messy_folder(scenario1)
        run([sys.executable, organizer, "--source", str(scenario1), "--dry-run",
             "--log-file", str(TEST_ROOT / "scenario1.log")], log)
        after = sorted(p.name for p in scenario1.iterdir())
        log.write(f"Folder contents after dry run (unchanged): {after}\n\n")
        assert len(after) == 13, "Dry run must not move any files"

        # --- Scenario 2: live run ---
        log.write("SCENARIO 2: Live run on the same set of files\n")
        log.write("-" * 70 + "\n")
        scenario2 = TEST_ROOT / "scenario2_live_run"
        make_messy_folder(scenario2)
        run([sys.executable, organizer, "--source", str(scenario2),
             "--log-file", str(TEST_ROOT / "scenario2.log")], log)
        after = sorted(p.name for p in scenario2.iterdir() if p.is_dir())
        log.write(f"Sub-folders created: {after}\n\n")
        assert "Images" in after and "Documents" in after and "Other" in after

        # --- Scenario 3: duplicate filename collision ---
        log.write("SCENARIO 3: Re-running organizer after adding a duplicate filename\n")
        log.write("-" * 70 + "\n")
        (scenario2 / "notes.txt").write_text("a second notes.txt created after first run")
        run([sys.executable, organizer, "--source", str(scenario2),
             "--log-file", str(TEST_ROOT / "scenario2.log")], log)
        docs = sorted(p.name for p in (scenario2 / "Documents").iterdir())
        log.write(f"Documents/ contents after collision handling: {docs}\n\n")
        assert "notes_1.txt" in docs, "Collision should be renamed, not overwritten"

        # --- Scenario 4: custom rules config ---
        log.write("SCENARIO 4: Using a custom rules config file (sample_rules.json)\n")
        log.write("-" * 70 + "\n")
        scenario4 = TEST_ROOT / "scenario4_custom_rules"
        make_messy_folder(scenario4)
        run([sys.executable, organizer, "--source", str(scenario4),
             "--config", "sample_rules.json",
             "--log-file", str(TEST_ROOT / "scenario4.log")], log)
        after = sorted(p.name for p in scenario4.iterdir() if p.is_dir())
        log.write(f"Sub-folders created with custom rules: {after}\n\n")
        assert "Scripts" in after  # only exists in the custom config, not defaults

        # --- Scenario 5: error handling on bad source path ---
        log.write("SCENARIO 5: Error handling -- source directory does not exist\n")
        log.write("-" * 70 + "\n")
        result = run([sys.executable, organizer, "--source", "test_sandbox/does_not_exist",
             "--log-file", str(TEST_ROOT / "error_case.log")], log)
        log.write(f"Correctly exited with non-zero status: {result.returncode != 0}\n\n")
        assert result.returncode != 0

    print(f"\nAll scenarios passed. Transcript saved to {TRANSCRIPT}")


if __name__ == "__main__":
    main()
