import requests
from config import bot
import Torrent_download
from telethon import events
from FastTelethonhelper import fast_upload
import os , shutil
import bencodepy as bencode
import hashlib,base64


is_busy = False

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
    hashcontents = bencode.bencode(metadata['info'])
    digest = hashlib.sha1(hashcontents).digest()
    b32hash = base64.b32encode(digest)
    return f"magnet:?xt=urn:btih:{str(b32hash)}"



@bot.on(events.NewMessage(pattern='/torrent'))
async def download_torrent(event):
    global is_busy
    if is_busy == True : return
    try:
        is_busy = True
        x = await event.get_reply_message()
        if x == None or x.media == None:
            split  = event.raw_text.split()
            link  = split[-1]
        else:
            link = await bot.download_file(x.media)
            link = generate_magnet(link)

        if "nyaa" in link:
            res = requests.get(link,allow_redirects=True,stream=True)
            link = res.content
            link = generate_magnet(link)

        directory = 'downloads'
        delete_files(directory)
        await bot.send_message(event.chat_id,"downloading torrent....")
        await Torrent_download.download_torrent(link,event)
        file_list = []  
        for root,subdirectories, files in os.walk(directory):
            for file in files:
                file_list.append(os.path.join(root, file))
        await upload_files(event,file_list)
        delete_files(directory)
    except Exception as e:
        await bot.send_message(event.chat_id,e)




bot.start()
bot.run_until_disconnected()

