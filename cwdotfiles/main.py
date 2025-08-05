import argparse
from pathlib import Path

from cwdotfiles.impl import Config, run


def main():
    parser = argparse.ArgumentParser(description='Dotfiles manager with profile support')
    parser.add_argument('--home-dir', default='~',
                        help='Home directory (default: ~)')
    parser.add_argument('--backup-dir', default='~/.local/share/cwdotfiles/backup',
                        help='Base backup directory (default: ~/.local/share/cwdotfiles/backup)')
    parser.add_argument('--dry-run', default=False, action="store_true",
                        help='Test run')
    parser.add_argument('profiles', nargs='*', default=[],
                        help='List of profiles to activate (first has priority)')
    args = parser.parse_args()

    home_dir = Path(args.home_dir).expanduser()
    base_backup_dir = Path(args.backup_dir).expanduser()
    dotfiles_dir = Path.home() / "Sync" / "dotfiles"
    profiles = (args.profiles + ["common"]) if not "common" in args.profiles else args.profiles
    dry_run = args.dry_run

    if not dotfiles_dir.is_dir():
        print(f"Error: {dotfiles_dir} does not exist!")
        exit(1)

    print(f"Profiles: {', '.join(profiles)}")

    print(f"Creating links from {dotfiles_dir} to {home_dir}{' TEST ' if dry_run else ''}" )
    cfg = Config(home_dir, dotfiles_dir, base_backup_dir, profiles, dry_run)
    run(cfg)
    print("Done!")
