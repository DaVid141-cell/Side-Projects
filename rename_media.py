"""
Overview:
What this script does is, it renames the file that you wanted automatically. 
the ranming will be based on what you want to rename the file.

So it is great when you have a large amount of file's that you wanted to rename based on what you wanted.

HOW TO USE:
1. Edit the settings in the "SETTINGS" section of the code below.
2. Run with " DRY_RUN = True " first to preview the renames (nothing will be change here yet)
3. Once the preview looks right, set " DRY_RUN = False " and run again to actually rename.

"""

import os
from pathlib import Path

# =====================================================================
# SETTINGS - Change these to match what you want to rename a file
# =====================================================================

FOLDER_PATH = r"C:\Users\Gabriel\Downloads\fb-Jul-Gem-gempisao.juliana.barbadilloTG@burikatemall\vidoes"                   # paste the url of the folder containing your files
BASE_NAME = "gempisao.juliana.barbadilloTG@burikatemall"                                                            # input the name that you want to rename the old file name
START_NUMBER = 154                                                              # number to start the counting from
PADDING_NUMBER = 4                                                            # this will be how many digits your number can hold, e.g., 4 -> 0001, 0002
DRY_RUN = False                                                               # True = just a preview nothing has change yet, False = it will actually rename the old file name.


# this part will be the indicator of which file types count as "photos/vidoes". Add more if needed (only if the file type is not in the code below this)
MEDIA_EXTENSIONS = {
    # Photos file types
    ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff",

    # Vidoes file types
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".3gp"
}

# How to order the files before numbering them:
# "name" -> aplhabetical by current filename
# "modified" -> by last-modifed date (oldest first) - good for matching the order you took them

SORT_BY = "modified"

# ================================
# SCRIPT - LOGIC 
# ================================

def get_media_files(folder: Path):

    # it returns a list of media files in the folder, and sorted as configured.
    files = [f for f in folder.iterdir() 
                if f.is_file() and f.suffix.lower() 
                    in MEDIA_EXTENSIONS]
    
    if SORT_BY == "modified":
        files.sort(key=lambda f: f.stat().st_mtime)
    else:
        files.sort(key=lambda f: f.name.lower())

    return files


def build_new_name(index: int, extension: str) -> str:
    
    #this builds the new filename for the old file name you have
    number_str = str(index).zfill(PADDING_NUMBER)
    return f"{BASE_NAME}_{number_str}{extension.lower()}"

def rename_files():
    folder = Path(FOLDER_PATH)

    if not folder.exists():
        print(f"Folder not found: {folder}")
        return
    
    files = get_media_files(folder)

    if not files:
        print("No matching photo/video files found in that folder.")

        return
    
    print(f"Found {len(files)} file(s) to rename.\n")

    # step 1: rename it to temporary names first
    # this avoids collisions if a target name already exists
    # (e.g. renaming file 2 to the same name file 5 currently has)

    temp_names = []
    for i, file in enumerate(files):
        temp_path = file.with_name(f"__temp_rename_{i}__{file.suffix}")

        temp_names.append((temp_path, file.suffix))
        if not DRY_RUN:
            file.rename(temp_path)
    
    # step 2: rename from temp name to the final names.
    number = START_NUMBER
    for i, (temp_path, ext) in enumerate(temp_names):
        new_name = build_new_name(number, ext)
        final_path = folder / new_name

        original_name = files[i].name 
        print(f"{original_name} -> {new_name}")

        if not DRY_RUN:
            temp_path.rename(final_path)

        number += 1

    if DRY_RUN:
        print("\nThis was a DRY RUN - no files wre actually renamed.")
        print("Set DRY_RUN = False at the top of the script section and run again to apply.")
    else:
        print("\nDone! Files have been rename.")

if __name__ == "__main__":
    rename_files()