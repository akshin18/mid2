import asyncio
from datetime import datetime, timedelta
from loguru import logger
import json

from storage import Data
from service import get_prompts, send_prompt, interaction, send_message, save
from config import MIDJOURNERY_ID, PROMPT_GENERATE_TYPE, UPSCALE_TYPE


async def handler(event: dict):
    logger.info("event handle")
    try:
        author = event["d"].get("author")
    except:
        logger.warning(f"Could not find author {event}")
        return
    if author is None:
        logger.info(f"Could not find author {event['t']}")
        return
    if int(author["id"]) == MIDJOURNERY_ID:
        await handle_midjourney(event)
    else:
        await handle_author(event)
    
async def handle_author(event: dict):
    message_type = event["t"]
    if message_type == "MESSAGE_CREATE":
        await check_start(event)

async def handle_midjourney(event: dict):
    logger.info("check midjourney")
    content = event["d"].get("content")
    if content is None:
        logger.warning(f"Could not find content {event}")
        return
    message_type = event["t"]
    if message_type == "MESSAGE_CREATE":
        logger.success("Check MESSAGE_CREATE")
        print(event)
        await handle_message_create(event)
    elif message_type == "MESSAGE_UPDATE":
        logger.info("Check MESSAGE_UPDATE")
        await handle_message_update(event)
    else:
        logger.info("Could not find message type midhourney")
    

async def handle_message_create(event: dict):
    content = event["d"].get("content")
    if check_content_end(content, PROMPT_GENERATE_TYPE):
        if check_content_upscale_type(content, UPSCALE_TYPE):
            logger.info("Found upscale prompt")
            components = [event["d"]["attachments"][0]["url"]]
            choose = event["d"]["referenced_message"]["components"][0]["components"][0]["custom_id"]
            await update_upscale(choose,components)
        else:
            components = [x["custom_id"] for x in event["d"]["components"][0]["components"]][:4]
            await update_prompt(content, components)
    else:
        if content == "":
            embed = event["d"]["embeds"][0]
            if embed["description"] == "You have reached the maximum allowed number of concurrent jobs. Don't worry, this job will start as soon as another one finishes!":
                if Data.process_type == "p":
                    prompt = embed["footer"]["text"].replace("/imagine ","").split("-")[0].strip()
                    real_prompt = [x for x in Data.prompts if prompt in x][0]
                    logger.info(f"Found limit prompt {prompt}")
                    Data.wait_prompts.append(real_prompt)
                elif Data.process_type == "u":
                    prompt = embed["footer"]["text"].replace("/imagine ","").split("-")[0].strip()
                    data = [{x:Data.choose[x]} for x in Data.choose if prompt in Data.choose[x]["prompt"]][0]
                    Data.wait_upsclae.append(data)
            else:
                try:
                    logger.warning("Found bad prompt")
                    prompt = embed["footer"]["text"].replace("/imagine ","").split("-")[0].strip()
                    for i in Data.prompts:
                        if prompt in i:
                            Data.prompts[i]["components"].append(None)
                            break
                except:
                    logger.info("Could not content '' error")
                    return
                    
        elif "- Image #" in content:
            custom_id = event["d"]["components"][0]["components"][0]["custom_id"]
            image = event["d"]["attachments"][0]["url"]
            prompt = event["d"]["content"].replace("**","").split("-")[0].strip()
            message_id = event["d"]["id"]
            Data.choose[custom_id] = {"prompt":prompt, "image":image, "message_id":message_id}
            logger.success(f"Found image {prompt} {custom_id} {message_id}")
        else:
            logger.info("Could not find components")

async def update_prompt(content, components):
    for prompt in Data.prompts:
        if prompt in content:
            Data.prompts[prompt]["components"] = components
            logger.success(f"Updated prompt {Data.prompts[prompt]}")
            if Data.wait_prompts != []:
                wait_prompt = Data.wait_prompts.pop(0)
                await send_prompt(wait_prompt)
                clear_prompt = wait_prompt.split("-")[0].strip()
                Data.prompts[clear_prompt] = {"components":[], "real_name":wait_prompt}
            return

async def update_upscale(content, components):
    for choose in Data.choose:
        if choose in content:
            Data.upsclae[choose]["components"] = components
            logger.success(f"Updated upscale {Data.upsclae[choose]}")
            if Data.wait_upsclae != []:
                wait_upscale = Data.wait_upsclae.pop(0)
                custom_id = list(wait_upscale.keys())[0]
                Data.upsclae[custom_id] = {"components":[], "message_id":wait_upscale[custom_id]["message_id"], "prompt":wait_upscale[custom_id]["prompt"]}
                await send_upscale(wait_upscale[custom_id]["message_id"], custom_id)
            return

async def send_upscale(message_id, custom_id):
    await interaction(message_id, custom_id)

def check_content_end(content, check_type):
    return any([True for x in check_type if content.endswith(x)])

def check_content_upscale_type(content, check_type):
    return any([True for x in check_type if x in content])

async def handle_message_update(event):
    Data.update_time = datetime.utcnow()
    logger.debug(f"Update time {Data.update_time}")

async def check_start(event: dict):
    content = event["d"]["content"]
    if content == "start":
        author_id =event["d"]["author"]["id"]
        guild_id = event["d"]["guild_id"]
        channel_id = event["d"]["channel_id"]
        Data.author_id = author_id
        Data.guild_id = guild_id
        Data.channel_id = channel_id
        await prompt_process()
    elif content == "upscale":
        Data.prompts_done = True
        Data.wait_prompts = []
        await upscale_process()
    elif content == "con":
        author_id =event["d"]["author"]["id"]
        guild_id = event["d"]["guild_id"]
        channel_id = event["d"]["channel_id"]
        Data.author_id = author_id
        Data.guild_id = guild_id
        Data.channel_id = channel_id
    elif content == "save":
        save()
    elif content == "save c":
        save("c")

async def upscale_process():
    Data.process_type = "u"
    for zi, choose in enumerate(Data.choose):
        Data.upsclae[choose] = {"components": [], "message_id":Data.choose[choose]["message_id"], "prompt":Data.choose[choose]["prompt"]}
        if zi < 3:
            await interaction(Data.choose[choose]["message_id"], choose)
            logger.success(f"Upscale {choose}")
        else:
            Data.wait_upsclae.append({choose:Data.choose[choose]})
        await asyncio.sleep(1)
    asyncio.create_task(check_upscale_done())
    asyncio.create_task(check_upscale_time())

async def check_prompt_time():
    Data.update_time = datetime.utcnow()
    while True:
        logger.info(f"Check prompt time {datetime.utcnow()} {Data.update_time}")
        if Data.prompts_done == False:
            if datetime.utcnow() - Data.update_time > timedelta(minutes=2):
                logger.warning("Prompt time out")
                if Data.prompts == []:
                    Data.prompts_done = True
                    return
                for prompt in Data.prompts:
                    if Data.prompts[prompt]["components"] == []:
                        real_prompt = [x for x in Data.prompts if prompt in x][0]
                        await send_prompt(real_prompt)
                        clear_prompt = real_prompt.split("-")[0].strip()
                        Data.prompts[clear_prompt] = {"components":[], "real_name":real_prompt}
                Data.update_time = datetime.utcnow()
            else:
                await asyncio.sleep(20)
        else:
            return

async def check_upscale_time():
    Data.update_time = datetime.utcnow()
    while True:
        logger.info(f"Check prompt time {datetime.utcnow()} {Data.update_time}")
        if Data.upscale_done == False:
            if (datetime.utcnow() - Data.update_time) > timedelta(minutes=2):
                logger.warning("Upscale time out")
                if Data.wait_upsclae != []:
                    wait_upscale = Data.wait_upsclae.pop(0)
                    new_chose = list(wait_upscale.keys())[0]
                    Data.upsclae[wait_upscale] = {"components":[], "message_id":wait_upscale[new_chose]["message_id"], "prompt":wait_upscale[new_chose]["prompt"]}
                    await send_upscale(wait_upscale[new_chose]["message_id"], wait_upscale[new_chose]["custom_id"])
                    Data.update_time = datetime.utcnow()
                else:
                    Data.upscale_done = True
                    return
            else:
                await asyncio.sleep(20)
        else:
            return

async def prompt_process():
    Data.process_type = "p"
    prompts = get_prompts()
    for zi, prompt in enumerate(prompts):
        if zi < 3:
            await send_prompt(prompt)
            clear_prompt = prompt.split("-")[0].strip()
            Data.prompts[clear_prompt] = {"components":[], "real_name":prompt}
            await asyncio.sleep(1)
        else:
            Data.wait_prompts.append(prompt)
    
    asyncio.create_task(check_prompts_done())
    asyncio.create_task(check_prompt_time())

async def check_prompts_done():
    while True:
        result = 0
        for prompt in Data.prompts:
            if Data.prompts[prompt]["components"] == []:
                result += 1
        if (result == 0 or Data.prompts_done == True) and Data.wait_prompts == []:
            logger.success("All prompts done")
            send_message("All prompts done")
            Data.prompts_done = True
            break
        else:
            logger.info(f"Check prompts done {Data.prompts}")
            logger.info(f"wait prompts {Data.wait_prompts}")
            await asyncio.sleep(10)

async def check_upscale_done():
    while True:
        result = 0
        for choose in Data.upsclae:
            if Data.upsclae[choose]["components"] == []:
                result += 1
        if (result == 0 or Data.upscale_done == True) and Data.wait_upsclae == []:
            logger.success("All upscale done")
            send_message("All upscale done")
            Data.upscale_done = True
            break
        else:
            logger.info(f"Check upscale done {Data.upsclae}")
            logger.info(f"wait upscale {Data.wait_upsclae}")
            await asyncio.sleep(10)