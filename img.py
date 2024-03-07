import os
from exiftool import ExifToolHelper
from loguru import logger

def set_metadata(data:list):
    for image_path, prompt in data:
        prompt = prompt.split(",")[0].replace("**","").strip()
        logger.debug(f"Saving metadata {image_path} prompt: {prompt}")
        with ExifToolHelper() as et:
            et.set_tags(
                [image_path],
                tags={"XMP:Title": prompt},
                params=["-P", "-overwrite_original"]
            )


def get_metadata():
    for image_path in os.listdir("images"):
        with ExifToolHelper() as et:
            for d in et.get_metadata(f"images/{image_path}"):
                for k, v in d.items():
                    print(f"Dict: {k} = {v}")
        print("\n")
