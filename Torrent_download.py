#sudo apt-get install python3-libtorrent
import libtorrent as lt
import time
import datetime
from config import bot, timeout

cancel = False
timeout_time = timeout

async def download_torrent(link, event):
    global cancel
    cancel = False
    ses = lt.session()
    ses.listen_on(6881, 6891)
    params = {
        'save_path': 'downloads',
        'storage_mode': lt.storage_mode_t(2),
        # 'paused': False,
        # 'auto_managed': True,
        # 'duplicate_is_error': True
        }

    # print(link)

    handle = lt.add_magnet_uri(ses, link, params)
    ses.start_dht()

    begin = time.time()
    print(datetime.datetime.now())

    message = await bot.send_message(event.chat_id,"Downloading Metadata...")
    while (not handle.has_metadata() and cancel == False):
        end = time.time()
        if (int(end-begin) > timeout_time):
            raise Exception("TimeoutError")
        time.sleep(0.5)
    if cancel == True: raise Exception("process cancelled")

    await bot.edit_message(event.chat_id,message,"Got Metadata, Starting Torrent Download...")

    print("Starting", handle.name())
    await bot.edit_message(event.chat_id,message,f"Starting, {handle.name()}")
    while (handle.status().state != lt.torrent_status.seeding and cancel == False):
        s = handle.status()
        state_str = ['queued', 'checking', 'downloading metadata', \
                'downloading', 'finished', 'seeding', 'allocating']
        size_bytes = s.total_wanted
        size_mb = size_bytes/(1024*1024)
        size_gb = size_bytes/(1024*1024*1024)
        size = size_mb
        byte = "MB"
        if size_gb > 1:
            size = size_gb
            byte = "GB"

        await bot.edit_message(event.chat_id,message,"%s \n\nSize: %.2f %s\n\n %.2f%% complete (down: %.1f kb/s up: %.1f kB/s peers: %d) %s " % \
        (handle.name(), size,byte, s.progress * 100, s.download_rate / 1000, s.upload_rate / 1000, \
        s.num_peers, state_str[s.state]))
        time.sleep(3)





    end = time.time()

    await bot.edit_message(event.chat_id,message,f"{handle.name()} COMPLETE")

    await bot.send_message(event.chat_id, f"Elapsed Time: {int((end-begin)//60)} min :{int((end-begin)%60)} sec")
    if cancel == True: raise Exception("Process Cancelled")