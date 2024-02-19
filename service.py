import random
import json
import asyncio
import os
import re

import requests
from loguru import logger

from config import HEADERS, MIDJOURNERY_ID, SESSION_ID
from storage import Data
from img import set_metadata


async def interaction(message_id: str, custom_id: str):
    nonce = generate_nonce()
    data = {
        "type": 3,
        "nonce": nonce,
        "guild_id": str(Data.guild_id),
        "channel_id": str(Data.channel_id),
        "message_flags": 0,
        "message_id": str(message_id),
        "application_id": str(MIDJOURNERY_ID),
        "session_id": SESSION_ID,
        "data": {"component_type": 2, "custom_id": str(custom_id)},
    }
    try:
        r = requests.post(
            "https://discord.com/api/v9/interactions", headers=HEADERS, json=data
        )
        return nonce
    except:
        logger.error("Could not send interaction")
        await asyncio.sleep(5)
        return await interaction(message_id, custom_id)


def send_message(content: str):
    nonce = generate_nonce()
    data = {
        "mobile_network_type": "unknown",
        "content": content,
        "nonce": nonce,
        "tts": False,
        "flags": 0,
    }
    requests.post(
        f"https://discord.com/api/v9/channels/{Data.channel_id}/messages",
        headers=HEADERS,
        json=data,
    )
    return nonce


async def send_prompt(prompt):
    url = "https://discord.com/api/v9/interactions"
    nonce = generate_nonce()
    pre_data = {
        "type": 2,
        "application_id": f"{MIDJOURNERY_ID}",
        "guild_id": f"{Data.guild_id}",
        "channel_id": f"{Data.channel_id}",
        "session_id": f"{SESSION_ID}",
        "data": {
            "version": "1166847114203123795",
            "id": "938956540159881230",
            "name": "imagine",
            "type": 1,
            "options": [{"type": 3, "name": "prompt", "value": f"{prompt}"}],
            "application_command": {
                "id": "938956540159881230",
                "type": 1,
                "application_id": "936929561302675456",
                "version": "1166847114203123795",
                "name": "imagine",
                "description": "Create images with Midjourney",
                "options": [
                    {
                        "type": 3,
                        "name": "prompt",
                        "description": "The prompt to imagine",
                        "required": True,
                        "description_localized": "The prompt to imagine",
                        "name_localized": "prompt",
                    }
                ],
                "integration_types": [0],
                "global_popularity_rank": 1,
                "description_localized": "Create images with Midjourney",
                "name_localized": "imagine",
            },
            "attachments": [],
        },
        "nonce": f"{nonce}",
        "analytics_location": "slash_ui",
    }
    payload = {"payload_json": json.dumps(pre_data)}
    try:
        r = requests.post(url, headers=HEADERS, data=payload)
        return nonce
    except:
        logger.error("Could not send prompt")
        await asyncio.sleep(5)
        return await send_prompt(prompt)


async def describe_interaction(link):
    nonce = generate_nonce()
    url = "https://discord.com/api/v9/interactions"

    pre_data = {
        "type": 2,
        "application_id": f"{MIDJOURNERY_ID}",
        "guild_id": f"{Data.guild_id}",
        "channel_id": f"{Data.channel_id}",
        "session_id": f"{SESSION_ID}",
        "data": {
            "version": "1204231436023111690",
            "id": "1092492867185950852",
            "name": "describe",
            "type": 1,
            "options": [
                {
                    "type": 3,
                    "name": "link",
                    "value": link,
                }
            ],
            "application_command": {
                "id": "1092492867185950852",
                "type": 1,
                "application_id": "936929561302675456",
                "version": "1204231436023111690",
                "name": "describe",
                "description": "Writes a prompt based on your image.",
                "options": [
                    {
                        "type": 11,
                        "name": "image",
                        "description": "The image to describe",
                        "required": False,
                        "description_localized": "The image to describe",
                        "name_localized": "image",
                    },
                    {
                        "type": 3,
                        "name": "link",
                        "description": "",
                        "required": False,
                        "description_localized": "",
                        "name_localized": "link",
                    },
                ],
                "integration_types": [0],
                "global_popularity_rank": 2,
                "description_localized": "Writes a prompt based on your image.",
                "name_localized": "describe",
            },
            "attachments": [],
        },
        "nonce": nonce,
        "analytics_location": "slash_ui",
    }
    payload = {"payload_json": json.dumps(pre_data)}
    response = requests.post(url, headers=HEADERS, data=payload)


def generate_nonce(k=19):
    return "".join(random.choices("1234567890", k=k))


def get_prompts():
    with open("prompts.txt", "r") as f:
        return [x.strip() for x in f.read().strip().split("\n")]


def get_random_name():
    return "".join(random.choices("1234567890abcdefghijklmnopqrstuvwxyz_", k=25))


def save(t="u"):
    logger.info("Saving images")
    try:
        os.mkdir("images")
    except:
        pass
    finally:
        images_data = []
        if t == "u":
            for custom_id in Data.upsclae:
                components = Data.upsclae[custom_id]["components"]
                if components != []:
                    img_url = components[0]
                    img_prompt = Data.upsclae[custom_id]["prompt"]
                    r = requests.get(img_url)
                    name = get_random_name()
                    image_path = f"images/{name}.png"
                    with open(image_path, "wb") as f:
                        f.write(r.content)
                    images_data.append([image_path, img_prompt])
        else:
            for custom_id in Data.choose:
                img_url = Data.choose[custom_id]["image"]
                img_prompt = Data.choose[custom_id]["prompt"]
                r = requests.get(img_url)
                name = get_random_name()
                image_path = f"images/{name}.png"
                with open(image_path, "wb") as f:
                    f.write(r.content)
                images_data.append([image_path, img_prompt])
        set_metadata(images_data)
    logger.success("Saved images")
    send_message("images saved")


def upload_images():
    files = os.listdir("describe")
    for i in files:
        image_path = "describe/" + i
        Data.to_describe.append(image_path)


def get_link(image_path):
    url = "https://telegra.ph/upload"

    payload = {}
    files = [("file", ("file", open(image_path, "rb"), "application/octet-stream"))]
    headers = {
        "authority": "telegra.ph",
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-language": "en-US,en;q=0.9",
        "dnt": "1",
        "origin": "https://telegra.ph",
        "referer": "https://telegra.ph/",
        "sec-ch-ua": '"Chromium";v="121", "Not A(Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "x-requested-with": "XMLHttpRequest",
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)
    return "https://telegra.ph" + response.json()[0]["src"]



def find_message(message_id):
    r = requests.get(f"https://discord.com/api/v10/channels/{str(Data.channel_id)}/messages", headers=HEADERS)
    messages = r.json()
    for message in messages:
        if message["id"] == message_id:
            logger.success("oha")
            logger.success(message["embeds"])
            logger.success(message["embeds"][0]["description"])
            return find_describe(message["embeds"][0]["description"])
            

def find_describe(content):
    for i in content.split("\n\n"):
        text = i[4:].split("--")[0]
        if text.startswith("a "):
            text = text[2:]
        elif text.startswith("an "):
            text = text[3:]
        elif text.startswith("the "):
            text = text[4:]
        with open("desc.txt", "a") as f:
            f.write(re.sub("\([^)]*\)|\[[^]]*\]","", text).replace(" , , ","").strip() + " --ar 3:2 --v 6.0 --style raw --s 50" + "\n")