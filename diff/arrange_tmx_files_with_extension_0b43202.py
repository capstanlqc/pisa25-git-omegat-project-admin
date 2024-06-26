import os
from pathlib import Path
import sys
import lxml
from bs4 import BeautifulSoup as bs
import re
from glob import glob
from itertools import chain

# unique argument: path to the repo root folder
repo = sys.argv[1:][0]


def get_batch_domains(batches):
    # return [get_domain(batch) for batch in batches]
    return list(map(get_domain, batches))


def get_domain(file):
    file_name = file.split("/")[-1] if "/" in file else file
    pattern = "\.tmx(\.zip)?(\.idle)?$"

    if file_name.startswith("PISA_") and re.search(pattern, file_name):
        # for tmx files
        tentative_domain = file_name.split("_")[2]
        if tentative_domain in allowed_domains["QQS"] or tentative_domain in allowed_domains["QQA"]:
            # then it's not the domain, but the actual questionnaire
            return next((key for key, value in allowed_domains.items() if tentative_domain in value), None)
        return tentative_domain
    else:
        # for batch folders or batch TMs
        if "_QQS_" in file_name or "_QQA_" in file_name:
            return file_name.split("_")[1]
        else:
            return file_name.split("_")[2].split("-")[0]


def delete_file(file):
    # file = Path(file) if isinstance(file, str) else file # only needed with unlink()
    try:
        # file.unlink()
        os.remove(file)
        print(f"The file {file} has been successfully deleted.")
    except FileNotFoundError:
        print(f"The file {file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def create_dir(dir_path):
    try:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"An error occurred: {e}")


def move_file(orig_path, dest_path):
    print(f">>> Move {orig_path.replace(repo, '')} to {dest_path.replace(repo, '')} !!!")
    dir_path, file = os.path.split(dest_path)
    create_dir(dir_path)
    try:
        os.replace(orig_path, dest_path)
        print(f"The file {file} has been successfully moved.")
    except FileNotFoundError:
        print(f"The file {file} does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")


def sort_trend_tmx_file_by_domain(file_path, current_domains, idle_extension = ".idle"):
    tmx_domain = get_domain(file_path)

    if os.path.exists(file_path):
        if tmx_domain in current_domains and file_path.endswith(idle_extension):
            # remove penalty
            new_file_path = file_path.rstrip(idle_extension)
            move_file(file_path, new_file_path)
        elif tmx_domain not in current_domains and not file_path.endswith(idle_extension):
            # add penalty
            new_file_path = file_path + idle_extension
            move_file(file_path, new_file_path)
        elif tmx_domain in disallowed_domains:
            # remove file for good
            delete_file(file_path)


def sort_step_tmx_file_by_batch(file_path, batches, idle_extension = ".idle"):
    file_name = file_path.split("/")[-1] if "/" in file_path else file_path
    basename = file_name.split(".")[0]
    if basename in batches and file_path.endswith(idle_extension):
        # remove penalty
        new_file_path = file_path.rstrip(idle_extension)
        move_file(file_path, new_file_path)
    elif basename not in batches and not file_path.endswith(idle_extension):
        # add penalty
        new_file_path = file_path + idle_extension
        move_file(file_path, new_file_path)


def get_tmx_files(tm_dir, origin_dirs):
    files = [glob(f"{tm_dir}/**/{origin_dir}/*.tmx*", recursive=True) for origin_dir in origin_dirs]
    return list(chain.from_iterable(files))


def get_mapped_batches(root_dir_path):
    settings_file = os.path.join(root_dir_path, "omegat.project")
    with open(settings_file, "r") as f:
        content = f.read()
    bs_content = bs(content, "xml")

    mappings = bs_content.find_all("mapping", attrs={'local': re.compile(r"source")})
    return [mapping.attrs['local'].split("/")[1] for mapping in mappings]


if __name__ == "__main__":

    disallowed_domains = ["CRT", "XYZ", "FLQ", "FNL", "WBQ"]
    allowed_domains = {
        "QQS": ("STQ", "STQ-UH", "STQ-UO", "ICQ"),
        "QQA": ("SCQ", "TCQ"),
        "COS": ("MAT", "REA", "SCI")
    }

    root_dir_path = repo # path to root level in the repo
    tm_dir_path = os.path.join(root_dir_path, "tm")

    batches = get_mapped_batches(root_dir_path)
    current_domains = get_batch_domains(batches)
    idle_extension = ".idle"

    for tmx_file in get_tmx_files(tm_dir_path, ["trend"]):
        sort_trend_tmx_file_by_domain(tmx_file, current_domains)

    for tmx_file in get_tmx_files(tm_dir_path, ["prev", "next"]):
        sort_step_tmx_file_by_batch(tmx_file, batches)