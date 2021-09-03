#!/usr/bin/env python

import re
from time import sleep
from urllib import request
from os import environ, getenv
import zeroconf
import pychromecast
from pychromecast.discovery import CastInfo
from pychromecast.controllers.bubbleupnp import BubbleUPNPController
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext,CommandHandler

##########device###########
def devicelist() ->list:
    zconf = zeroconf.Zeroconf()
    devices,browser = pychromecast.discovery.discover_chromecasts(zeroconf_instance=zconf)
    browser.stop_discovery()
    zconf.close()
    return devices

def deviceplay(info:CastInfo,mediainfo:list) -> bool:
    try:
        cast = pychromecast.get_chromecast_from_host(
            [info.host, info.port, info.uuid, info.model_name, info.friendly_name])
        bubbleupnp = BubbleUPNPController()
        cast.wait(3)
        cast.register_handler(bubbleupnp)
        bubbleupnp.launch()
        metadata = {'title':mediainfo[3],'metadataType':3}
        bubbleupnp.play_media(mediainfo[1],mediainfo[2],mediainfo[3],stream_type='LIVE',metadata=metadata)
        bubbleupnp.block_until_active()
        bubbleupnp.play()
        cast.disconnect()
        return True
    except:
        return False

def devicestop(info:CastInfo) -> bool:
    try:
        cast = pychromecast.get_chromecast_from_host(
            [info.host, info.port, info.uuid, info.model_name, info.friendly_name])
        cast.wait(3)
        cast.quit_app()
        cast.disconnect()
        return True
    except:
        return False

def devicestatus(info:CastInfo) -> bool:
    try:
        cast = pychromecast.get_chromecast_from_host(
            [info.host, info.port, info.uuid, info.model_name, info.friendly_name])
        cast.wait(3)
        result = cast.is_idle
        cast.disconnect()
        return result
    except:
        return False

##########tg###########
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("a) Send audio url\nb) Share radio station from radio garden APP\nc) /status check device status")

def status(update: Update, context: CallbackContext) -> None:
    device_list = devicelist()
    if device_list.count == 0:
         update.message.reply_text('no device available')
         return
    keyboard = []
    device_avl = ""
    for device in device_list:
        device_avl = device_avl + "\n- " + device.friendly_name
        if not devicestatus(device):
            data = ["stop", device]
            keyboard.append([InlineKeyboardButton(device.friendly_name, callback_data=data)])
    if keyboard == []:
        update.message.reply_text(f"Available device:{device_avl}")
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        update.message.reply_text(f"Available device:{device_avl}\nStop the current playback on:", reply_markup=reply_markup)

def urlhandler(update: Update, context: CallbackContext) -> None:
    urlmatch = re.match('^.*(https?://[\S]+).*$',update.message.text,re.I)
    if not urlmatch:
        update.message.reply_text("Show me the URL")
        return
    url = urlmatch.group(1)
    if re.match('^https?://radio.garden/listen/.+/.{8}$',url,re.I):
        url = 'https://radio.garden/api/ara/content/listen/'+url[-8:]+'/channel.mp3'
    mediainfo = parseurl(url)
    if mediainfo[0] == 1:
        update.message.reply_text('bad url')
        return
    if not mediainfo[2].startswith('audio'):
        update.message.reply_text('not an audio url')
        return
    device_list = devicelist()
    if device_list.count == 0:
        update.message.reply_text('no device available')
        return
    keyboard = []
    for device in device_list:
        data = ["play", device, mediainfo]
        keyboard.append([InlineKeyboardButton(device.friendly_name, callback_data=data)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Play "+mediainfo[3]+" on:", reply_markup=reply_markup)

def btnhandler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data
    if data[0] == 'play':
        if deviceplay(data[1],data[2]):
            query.edit_message_text(text=f"playing {data[2][3]} on {data[1].friendly_name}")
        else:
            query.edit_message_text(text=f"operation failed")
    if data[0] == 'stop':
        if devicestop(data[1]):
            query.edit_message_text(text=f"playing on {data[1].friendly_name} has been stopped")
        else:
            query.edit_message_text(text=f"operation failed")

##########etc###########
def parseurl(url: str) -> list:
    try:
        r = request.urlopen(url)
        if r.code != 200:
            return [1]
        else:
            h = r.headers
            result = [0,r.url,h.get('Content-Type'),h.get('icy-name')]
            return result
    except:
        return [1]

def main():
    for env in ["tgtoken","tgchatid"]:
        if env not in environ:
            print(env + ' not found')
            exit(1)
    del env
    updater = Updater(getenv('tgtoken'), arbitrary_callback_data=True)
    idflt = Filters.chat(int(getenv('tgchatid')))
    updater.dispatcher.add_handler(CommandHandler('start', start, idflt))
    updater.dispatcher.add_handler(CommandHandler('status', status, idflt))
    updater.dispatcher.add_handler(MessageHandler(idflt, urlhandler))
    updater.dispatcher.add_handler(CallbackQueryHandler(btnhandler))
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
