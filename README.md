# Smart File Organizer

An automation script that solves a genuinely common problem: a Downloads
or Desktop folder that turns into a junk drawer of unsorted files. It
scans a target directory and sorts every file into a category sub-folder
(`Images/`, `Documents/`, `Spreadsheets/`, `Code/`, etc.) based on file
extension.

## Features

- **Config-driven rules** — categorization rules load from a JSON file
  (`--config rules.json`); falls back to sensible defaults if omitted.
- **Dry-run mode** — `--dry-run` previews every move without touching
  any files.
- **Safe collision handling** — if a destination filename already
  exists, the script appends `_1`, `_2`, etc. instead of overwriting.
- **Logging** — every run writes to both the console and a log file
  (`--log-file`), with timestamps and severity levels.
- **Error handling** — missing source directories, permission errors,
  and individual file-move failures are all caught and logged without
  crashing the whole run.
- **CLI arguments** — `argparse`-based interface (see below).
- **Scheduling** — either run continuously in-process with `--watch
  --interval <seconds>`, or trigger it externally with cron / Task
  Scheduler (examples below).
- **Notifications** — a console summary prints after every run
  (files-per-category counts + error count); the `notify()` function
  is a single, isolated place to swap in email/Slack alerts later.

## Usage

```bash
# Basic run
python organizer.py --source ~/Downloads

# Preview only, no files moved
python organizer.py --source ~/Downloads --dry-run

# Use custom categorization rules
python organizer.py --source ~/Downloads --config sample_rules.json

# Run continuously, once per hour
python organizer.py --source ~/Downloads --watch --interval 3600

# Custom log file location
python organizer.py --source ~/Downloads --log-file /var/log/organizer.log
```

## Scheduling with cron (Linux/macOS)

Run every day at 9 AM:

```cron
0 9 * * * /usr/bin/python3 /path/to/organizer.py --source /home/user/Downloads --log-file /home/user/organizer.log
```

## Scheduling with Task Scheduler (Windows)

1. Open Task Scheduler -> Create Basic Task
2. Set the trigger (e.g. daily at 9:00 AM)
3. Action: "Start a program"
   - Program: `python.exe`
   - Arguments: `organizer.py --source C:\Users\You\Downloads`

## Testing

`test_organizer.py` builds a disposable sandbox with a realistic mix of
13 file types and runs the organizer through 5 scenarios: dry run, live
run, duplicate-filename collision, custom rules config, and a
non-existent source directory (error handling). Run it with:

```bash
python test_organizer.py
```

Sample results from the test run are in `scenario_transcript.txt` and
`screenshots/`.

## Project structure

```
task2_file_organizer/
├── organizer.py              # main script
├── sample_rules.json         # example custom rules config
├── test_organizer.py         # test scenarios
├── scenario_transcript.txt   # captured output from a real test run
├── screenshots/              # terminal screenshots of each scenario
└── README.md
```
