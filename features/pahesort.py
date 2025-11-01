import os
import shutil
import re
import argparse
from pathlib import Path

def gather_anime(path: str, dry_run: bool = False):
    if path:
        os.chdir(path)

    animepahe_files = [filename for filename in os.listdir(path) if filename.startswith("AnimePahe")]
    animepahe_folder = os.path.join(path, "AnimePahe")

    if not os.path.exists(animepahe_folder):
        if dry_run:
            print(f"[DRY RUN] Would create folder: {animepahe_folder}")
        else:
            os.mkdir(animepahe_folder)

    for file in animepahe_files:
        filepath = os.path.join(path, file)
        if dry_run:
            print(f"[DRY RUN] Would move {filepath} -> {animepahe_folder}")
        else:
            shutil.move(filepath, animepahe_folder)

    return animepahe_folder

def rename_anime(path: str, animepahe: bool = False, dry_run: bool = False):
    if animepahe:
        folder_path = gather_anime(path, dry_run=dry_run)
        os.chdir(folder_path)
    else:
        folder_path = path
        os.chdir(path)

    animeinpath = [pahe for pahe in os.listdir() if os.path.isfile(pahe)]

    if animeinpath:
        noise_tokens = {"dub", "sub", "dual", "audio", "eng", "chi"}

        for file in animeinpath:
            anime, ext = os.path.splitext(file)
            if ext in ['.mp4', '.mkv', '.avi'] and anime.startswith('AnimePahe'):
                tokens = list(filter(None, anime.replace('AnimePahe_', '').replace('-', '').split('_')))

                # Find episode number index
                integer_index = None
                for i, x in enumerate(tokens):
                    if x[0].isdigit() or re.match(r"^\d{1,3}v?\d?$", x):
                        integer_index = i
                        break

                if integer_index is None:
                    print(f"This file -> {file} , should be manually renamed")
                    continue

                try:
                    episode_num = str(int(re.sub(r"[^0-9]", "", tokens[integer_index]))).zfill(2)
                    animename_list = [t for t in tokens[:integer_index] if t.lower() not in noise_tokens]
                    animename_short = animename_list[:4]
                    quality = tokens[integer_index + 1] if integer_index + 1 < len(tokens) else "Unknown"

                    new_filename = f"{episode_num}-{'_'.join(animename_short)}-{quality}{ext}"
                except:
                    print(f"This file -> {file} , should be manually renamed")
                    continue

                if dry_run:
                    print(f"[DRY RUN] Would rename: {file} -> {new_filename}")
                else:
                    os.rename(file, new_filename)
                    print(f"Renamed file ({file}) --> ({new_filename})\n")
    else:
        print(f"\nAll Animepahe files have been renamed\n\nDirectory Cleaned -> {path}\nFiles Current path -> {folder_path}")

def organize_anime(path: str, animepahe: bool = False, dry_run: bool = False):
    if animepahe:
        folder_path = gather_anime(path, dry_run=dry_run)
    else:
        folder_path = path

    os.chdir(folder_path)
    anime_files = [file for file in os.listdir() if os.path.isfile(file)]

    for file in anime_files:
        match = re.match(r"^\d+-(.*?)-\d+p", file)
        if not match:
            match = re.match(r"^\d+-(.*?)-[a-zA-Z]+", file)

        if match:
            anime_name = match.group(1).strip()
        else:
            print(f"\nSkipping file: {file} (doesn't match expected format)")
            continue

        anime_folder = os.path.join(folder_path, anime_name)

        if not os.path.exists(anime_folder):
            if dry_run:
                print(f"[DRY RUN] Would create folder: {anime_folder}")
            else:
                os.mkdir(anime_folder)
                print("\n============================================================================")
                print(f"\nCreated new folder {anime_name} at {folder_path}")

        if dry_run:
            print(f"[DRY RUN] Would move file: {file} -> {anime_folder}")
        else:
            shutil.move(file, os.path.join(anime_folder, file))
            print(f"\nMoved file ({file}) to {anime_folder}")

def main():
    parser = argparse.ArgumentParser(description="Process and organize anime files.")
    parser.add_argument("path", help="Specify the path where the anime files exist", type=str, nargs='?')
    parser.add_argument("-a","--all", help="Perform all operations: transfer, rename, and organize", action='store_true')
    parser.add_argument("-r","--rename", help="Only rename the anime files", action='store_true')
    parser.add_argument("-o","--organize", help="Only organize the anime files into folders", action='store_true')
    parser.add_argument("-dr","--dry-run", help="Simulate the operations without making any changes", action='store_true')

    args = parser.parse_args()
    rearg = args.rename
    orgarg = args.organize
    patharg = args.path or Path.home() / "Downloads"

    if args.all:
        rename_anime(patharg, animepahe=True, dry_run=args.dry_run)
        organize_anime(patharg, animepahe=True, dry_run=args.dry_run)
    elif rearg:
        rename_anime(patharg, dry_run=args.dry_run)
    elif orgarg:
        organize_anime(patharg, dry_run=args.dry_run)
    else:
        print("\nNo operation specified. Use --all, --rename, or --organize.")

if __name__ == "__main__":
    main()
