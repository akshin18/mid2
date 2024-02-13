import random
import json

import requests

from config import HEADERS, MIDJOURNERY_ID, SESSION_ID
from storage import Data


def interaction(message_id:str, custom_id:str):
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
    print(data)
    r = requests.post("https://discord.com/api/v9/interactions", headers=HEADERS, json=data)
    print(r.status_code)
    print(r.text)
    return nonce

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

def send_prompt(prompt):
    url = "https://discord.com/api/v9/interactions"
    nonce = generate_nonce()
    pre_data = {"type":2,"application_id":f"{MIDJOURNERY_ID}","guild_id":f"{Data.guild_id}","channel_id":f"{Data.channel_id}","session_id":f"{SESSION_ID}","data":{"version":"1166847114203123795","id":"938956540159881230","name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":f"{prompt}"}],"application_command":{"id":"938956540159881230","type":1,"application_id":"936929561302675456","version":"1166847114203123795","name":"imagine","description":"Create images with Midjourney","options":[{"type":3,"name":"prompt","description":"The prompt to imagine","required":True,"description_localized":"The prompt to imagine","name_localized":"prompt"}],"integration_types":[0],"global_popularity_rank":1,"description_localized":"Create images with Midjourney","name_localized":"imagine"},"attachments":[]},"nonce":f"{nonce}","analytics_location":"slash_ui"}
    payload = {
        'payload_json': json.dumps(pre_data)
        }
    r = requests.post(url, headers=HEADERS, data=payload)
    return nonce

def generate_nonce(k=19):
    return "".join(random.choices("1234567890", k=k))

def get_prompts():
    with open("prompts.txt", "r") as f:
        return [x.strip() for x in f.read().strip().split("\n")]