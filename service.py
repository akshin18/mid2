import random
import json
import asyncio
import os

import requests
from loguru import logger

from config import HEADERS, MIDJOURNERY_ID, SESSION_ID
from storage import Data
from img import set_metadata


async def interaction(message_id:str, custom_id:str):
    nonce = generate_nonce()
    data = {
        "type":3,
        "nonce":nonce, 
        "guild_id":str(Data.guild_id), 
        "channel_id":str(Data.channel_id), 
        "message_flags":0,
        "message_id":str(message_id), 
        "application_id":str(MIDJOURNERY_ID), 
        "session_id":SESSION_ID,
        "data":{
            "component_type":2,
            "custom_id":str(custom_id) 
        }
        }
    try:
        r = requests.post("https://discord.com/api/v9/interactions", headers=HEADERS, json=data)
        return nonce
    except:
        logger.error("Could not send interaction")
        await asyncio.sleep(5)
        return await interaction(message_id, custom_id)

def send_message(content:str):
    nonce = generate_nonce()
    data = {
        "mobile_network_type":"unknown",
        "content":content,
        "nonce":nonce,
        "tts":False,
        "flags":0
    }
    requests.post(f"https://discord.com/api/v9/channels/{Data.channel_id}/messages", headers=HEADERS, json=data)
    return nonce

async def send_prompt(prompt):
    url = "https://discord.com/api/v9/interactions"
    nonce = generate_nonce()
    pre_data = {"type":2,"application_id":f"{MIDJOURNERY_ID}","guild_id":f"{Data.guild_id}","channel_id":f"{Data.channel_id}","session_id":f"{SESSION_ID}","data":{"version":"1166847114203123795","id":"938956540159881230","name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":f"{prompt}"}],"application_command":{"id":"938956540159881230","type":1,"application_id":"936929561302675456","version":"1166847114203123795","name":"imagine","description":"Create images with Midjourney","options":[{"type":3,"name":"prompt","description":"The prompt to imagine","required":True,"description_localized":"The prompt to imagine","name_localized":"prompt"}],"integration_types":[0],"global_popularity_rank":1,"description_localized":"Create images with Midjourney","name_localized":"imagine"},"attachments":[]},"nonce":f"{nonce}","analytics_location":"slash_ui"}
    payload = {
        'payload_json': json.dumps(pre_data)
        }
    try:
        r = requests.post(url, headers=HEADERS, data=payload)
        return nonce
    except:
        logger.error("Could not send prompt")
        await asyncio.sleep(5)
        return await send_prompt(prompt)

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