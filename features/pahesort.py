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
    """
    Rename AnimePahe files to a cleaner format.
    Files are renamed in-place (in their current directory).
    
    Args:
        path: Directory containing anime files
        animepahe: If True, first gather AnimePahe files into a subfolder
        dry_run: If True, only show what would be done
    """
    if animepahe:
        folder_path = gather_anime(path, dry_run=dry_run)
    else:
        folder_path = path

    # Use Path for cross-platform compatibility
    folder_path = Path(folder_path).resolve()
    
    # Get list of files
    try:
        animeinpath = [f for f in folder_path.iterdir() if f.is_file()]
    except Exception as e:
        print(f"Error reading directory {folder_path}: {e}")
        return

    if not animeinpath:
        print(f"\nAll Animepahe files have been renamed\n\nDirectory Cleaned -> {path}\nFiles Current path -> {folder_path}")
        return

    noise_tokens = {"dub", "sub", "dual", "audio", "eng", "chi"}
    files_renamed = 0

    for file_path in animeinpath:
        file = file_path.name
        anime, ext = os.path.splitext(file)
        
        if ext.lower() in ['.mp4', '.mkv', '.avi'] and anime.startswith('AnimePahe'):
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
            except Exception:
                print(f"This file -> {file} , should be manually renamed")
                continue

            new_file_path = folder_path / new_filename
            
            if dry_run:
                print(f"[DRY RUN] Would rename: {file} -> {new_filename}")
            else:
                try:
                    file_path.rename(new_file_path)
                    print(f"Renamed file ({file}) --> ({new_filename})\n")
                    files_renamed += 1
                except Exception as e:
                    print(f"Error renaming {file}: {e}")
    
    if files_renamed == 0 and not dry_run:
        print(f"\nAll Animepahe files have been renamed\n\nDirectory Cleaned -> {path}\nFiles Current path -> {folder_path}")
    elif files_renamed > 0 and not dry_run:
        print(f"\n✅ Renamed {files_renamed} files in {folder_path}")

def organize_anime(path: str, animepahe: bool = False, dry_run: bool = False):
    """
    Organize anime files into subfolders based on anime name.
    Files are organized in-place (in their current directory).
    
    Args:
        path: Directory containing anime files
        animepahe: If True, first gather AnimePahe files into a subfolder
        dry_run: If True, only show what would be done
    """
    if animepahe:
        folder_path = gather_anime(path, dry_run=dry_run)
    else:
        folder_path = path

    # Use Path for cross-platform compatibility
    folder_path = Path(folder_path).resolve()
    
    # Get list of files before changing directory
    try:
        anime_files = [f for f in folder_path.iterdir() if f.is_file()]
    except Exception as e:
        print(f"Error reading directory {folder_path}: {e}")
        return

    if not anime_files:
        print(f"\nNo files found in {folder_path}")
        return

    files_organized = 0
    for file_path in anime_files:
        file = file_path.name
        
        # Match renamed files: "01-Anime_Name-720p.mp4"
        match = re.match(r"^\d+-(.*?)-\d+p", file)
        if not match:
            match = re.match(r"^\d+-(.*?)-[a-zA-Z]+", file)

        if match:
            anime_name = match.group(1).strip()
        else:
            print(f"\nSkipping file: {file} (doesn't match expected format)")
            continue

        # Create anime folder in the same directory as the file (in-place)
        anime_folder = folder_path / anime_name

        if not anime_folder.exists():
            if dry_run:
                print(f"[DRY RUN] Would create folder: {anime_folder}")
            else:
                anime_folder.mkdir(parents=True, exist_ok=True)
                print("\n============================================================================")
                print(f"\nCreated new folder '{anime_name}' at {folder_path}")

        target_path = anime_folder / file
        
        if dry_run:
            print(f"[DRY RUN] Would move file: {file} -> {anime_folder}")
        else:
            try:
                shutil.move(str(file_path), str(target_path))
                print(f"\nMoved file ({file}) to {anime_folder}")
                files_organized += 1
            except Exception as e:
                print(f"\nError moving {file}: {e}")
    
    if not dry_run and files_organized > 0:
        print(f"\n✅ Organized {files_organized} files in {folder_path}")

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
