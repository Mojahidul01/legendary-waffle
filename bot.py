import requests
import urllib.parse
from urllib.parse import unquote, urlencode
from config import bot
import Torrent_download
from telethon import events
from FastTelethonhelper import fast_upload
import os , shutil
import bencodepy as bencode
import hashlib,base64


is_busy = False
link_queue = []



def delete_files(folder):
    folder = folder
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


async def upload_files(event,file_list):
    file_list = sorted(file_list)
    for files in file_list:
        name = files.split('/')
        msg = await bot.send_message(event.chat_id, "Uploading...")
        file = await fast_upload(bot,files,reply=msg)
        await bot.send_message(event.chat_id, name[-1], file = file, force_document=True)
        await bot.delete_messages(event.chat_id, msg)


def generate_magnet(file_bytes):
    metadata = bencode.bdecode(file_bytes)
    hashcontents = bencode.bencode(metadata[b'info'])
    digest = hashlib.sha1(hashcontents).digest()
    b32hash = base64.b32encode(digest).decode("utf-8")

    try:

        b32 = urlencode({'xt': 'urn:btih:%s' % b32hash})
        b32 = unquote(b32)

        params = {'dn':  metadata[b'info'][b'name'],
                  'tr':  metadata[b'announce']}


        paramstr = b32 + '&' + urllib.parse.urlencode(params)
        magnet = 'magnet:?%s' % paramstr

        return magnet
    except:
        return "magnet:?xt=urn:btih:%s" % b32hash



@bot.on(events.NewMessage(pattern='/torrent'))
async def download_torrent(event):
    global is_busy
    if is_busy == True : 
        await bot.send_message(event.chat_id,"busy with another task, try again later")
        return
    try:
        is_busy = True
        x = await event.get_reply_message()
        if x == None or x.media == None:
            split  = event.raw_text.split()
            link  = split[-1]
        else:
            link = await bot.download_file(x)
            link = generate_magnet(link)
            print(link)

        # for nyaa.si links
        if "nyaa.si" in link:
            res = requests.get(link,allow_redirects=True,stream=True)
            link = generate_magnet(res.content)
            print(link)

        directory = 'downloads'
        delete_files(directory)
        await bot.send_message(event.chat_id,"downloading torrent.... use /cancel to cancel")
        await Torrent_download.download_torrent(link,event)
        file_list = []  
        for root,subdirectories, files in os.walk(directory):
            for file in files:
                file_list.append(os.path.join(root, file))
        await upload_files(event,file_list)
        await bot.send_message(event.chat_id,"Done!")


        delete_files(directory)
    except Exception as e:
        if str(e) == "TimeoutError":
            await bot.send_message(event.chat_id,f"{str(e)}, Process exceeded {Torrent_download.timeout_time}s time limit")
        else:
            await bot.send_message(event.chat_id,str(e))
    finally:
        is_busy = False

@bot.on(events.NewMessage(pattern='/cancel'))
async def download_torrent(event):
    Torrent_download.cancel = True


@bot.on(events.NewMessage(pattern='/aq'))
async def add_queue(event):
    global link_queue
    try:
        split  = event.raw_text.split()
        split.pop(0)
        link_queue = split
        print(link_queue)
        await bot.send_message(event.chat_id,f"Added links to queue")
    except Exception as e:
        await bot.send_message(event.chat_id,str(e))

@bot.on(events.NewMessage(pattern='/sq'))
async def start_queue(event):
    global link_queue 
    while link_queue != []:
        try:
            link = link_queue.pop(0)
            if "nyaa.si" in link:
                res = requests.get(link,allow_redirects=True,stream=True)
                link = generate_magnet(res.content)
                print(link)

            directory = 'downloads'
            delete_files(directory)
            await bot.send_message(event.chat_id,"downloading torrent.... ")
            await Torrent_download.download_torrent(link,event)
            file_list = []  
            for root,subdirectories, files in os.walk(directory):
                for file in files:
                    file_list.append(os.path.join(root, file))
            await upload_files(event,file_list)
            await bot.send_message(event.chat_id,"Done!")
        except Exception as e:
            await bot.send_message(event.chat_id,str(e))

@bot.on(events.NewMessage(pattern='/clearq'))
async def clearq(event):
    global link_queue
    link_queue = []
    await bot.send_message(event.chat_id,"Queue cleared!")

@bot.on(events.NewMessage(pattern='/listq'))
async def listq(event):
    global link_queue 
    if link_queue != []:
        msg = "\n".join(link_queue)
        await bot.send_message(event.chat_id,f"These links are in queue\n\n{msg}")
    else:
        await bot.send_message(event.chat_id,"Nothing in Queue")


@bot.on(events.NewMessage(pattern='/getmagnet'))
async def get_magnet(event):
    try:
        x = await event.get_reply_message()
        if x == None or x.media == None:
            split  = event.raw_text.split()
            link  = split[-1]
        else:
            link = await bot.download_file(x)
            link = generate_magnet(link)
            print(link)

        # for nyaa.si links
        if "nyaa.si" in link:
            res = requests.get(link,allow_redirects=True,stream=True)
            link = generate_magnet(res.content)
            print(link)
        
        await bot.send_message(event.chat_id,f"`{str(link)}`")
    except Exception as e:
            await bot.send_message(event.chat_id,str(e))
            # await bot.send_message(event.chat_id,str(e))


bot.start()
bot.run_until_disconnected()

