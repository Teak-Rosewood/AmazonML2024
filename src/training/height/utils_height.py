import re
import constants
import os
import requests
import pandas as pd
import multiprocessing
import time
from time import time as timer
from tqdm import tqdm
import numpy as np
from pathlib import Path
from functools import partial
import requests
import urllib
from PIL import Image

def common_mistake(unit):
    if unit in constants.allowed_units:
        return unit
    if unit.replace('ter', 'tre') in constants.allowed_units:
        return unit.replace('ter', 'tre')
    if unit.replace('feet', 'foot') in constants.allowed_units:
        return unit.replace('feet', 'foot')
    return unit

def parse_string(s):
    s_stripped = "" if s==None or str(s)=='nan' else s.strip()
    if s_stripped == "":
        return None, None
    pattern = re.compile(r'^-?\d+(\.\d+)?\s+[a-zA-Z\s]+$')
    if not pattern.match(s_stripped):
        raise ValueError("Invalid format in {}".format(s))
    parts = s_stripped.split(maxsplit=1)
    number = float(parts[0])
    unit = common_mistake(parts[1])
    if unit not in constants.allowed_units:
        raise ValueError("Invalid unit [{}] found in {}. Allowed units: {}".format(
            unit, s, constants.allowed_units))
    return number, unit


def create_placeholder_image(image_save_path):
    placeholder_image = Image.new('RGB', (100, 100), color='black')
    placeholder_image.save(image_save_path)

def download_image(image_link, save_folder, index, retries=3, delay=3):
    if not isinstance(image_link, str):
        return

    original_filename = Path(image_link).name
    original_image_save_path = os.path.join(save_folder, original_filename)
    new_filename = f"{index}.jpg"
    new_image_save_path = os.path.join(save_folder, new_filename)

    # Check if the file exists with the original name
    try:
        if os.path.exists(original_image_save_path):
            os.rename(original_image_save_path, new_image_save_path)
            return
    except:
        pass

    # Check if the file already exists with the new name
    try:
        if os.path.exists(new_image_save_path):
            return
    except:
        pass

    for _ in range(retries):
        try:
            urllib.request.urlretrieve(image_link, original_image_save_path)
            if os.path.exists(original_image_save_path):  # Ensure the file was downloaded
                os.rename(original_image_save_path, new_image_save_path)
                return
        except:
            time.sleep(delay)
    
    create_placeholder_image(new_image_save_path) # Create a black placeholder image for invalid links/images

def download_image_wrapper(args):
    image_link, index, save_folder, retries, delay = args
    download_image(image_link, save_folder, index, retries, delay)

def download_images(image_links, indices, download_folder, allow_multiprocessing=True):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)

    if allow_multiprocessing:
        args = [(image_link, index, download_folder, 3, 3) for image_link, index in zip(image_links, indices)]
        with multiprocessing.Pool(64) as pool:
            list(tqdm(pool.imap(download_image_wrapper, args), total=len(image_links)))
            pool.close()
            pool.join()
    else:
        for image_link, index in tqdm(zip(image_links, indices), total=len(image_links)):
            download_image(image_link, download_folder, index, retries=3, delay=3)
        