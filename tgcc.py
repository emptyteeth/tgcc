#!/usr/bin/env python

from time import sleep
from urllib import request
from pychromecast.discovery import CastInfo
import zeroconf
import pychromecast
from pychromecast.controllers.bubbleupnp import BubbleUPNPController
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext,CommandHandler
import re
from os import environ, getenv

def parseurl(url: str) -> list:
    try:
        r = request.urlopen(url)
        if r.code != 200:
            r.close()
            return [1]
        else:
            h = r.headers
            result = [0,r.url,h.get('Content-Type'),h.get('icy-name')]
            r.close()
            return result
    except:
        return [1]

def devicelist() ->list:
    zconf = zeroconf.Zeroconf()
    devices,browser = pychromecast.discovery.discover_chromecasts(zeroconf_instance=zconf)
    browser.stop_discovery()
    zconf.close()
    return devices

def deviceplay(castinfo:CastInfo,mediainfo:list):
    zconf = zeroconf.Zeroconf()
    cast = pychromecast.get_chromecast_from_cast_info(castinfo,zconf)
    bubbleupnp = BubbleUPNPController()
    cast.wait(3)
    sleep(2)
    cast.register_handler(bubbleupnp)
    bubbleupnp.launch()
    metadata = {'title':mediainfo[3],'metadataType':3}
    bubbleupnp.play_media(mediainfo[1],mediainfo[2],mediainfo[3],stream_type='LIVE',metadata=metadata)
    bubbleupnp.block_until_active()
    sleep(1)
    bubbleupnp.play()
    cast.disconnect()
    zconf.close()

def devicestop(castinfo:CastInfo):
    zconf = zeroconf.Zeroconf()
    cast = pychromecast.get_chromecast_from_cast_info(castinfo,zconf)
    cast.wait(3)
    sleep(2)
    cast.quit_app()
    cast.disconnect()
    zconf.close()

def urlhandler(update: Update, context: CallbackContext) -> None:
    device_list = devicelist()
    if device_list.count == 0:
        update.message.reply_text('no device available')
        return

    url = update.message.text
    if re.match('^https://radio.garden/listen/.+$',url):
        url = 'https://radio.garden/api/ara/content/listen/'+update.message.text[-8:]+'/channel.mp3'

    mediainfo = parseurl(url)
    if mediainfo[0] == 1:
        update.message.reply_text('bad url')
        return
    if not mediainfo[2].startswith('audio'):
        update.message.reply_text('not an audio url')
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
        deviceplay(data[1],data[2])
        query.edit_message_text(text=f"playing {data[2][3]} on {data[1].friendly_name}")
    if data[0] == 'stop':
        devicestop(data[1])
        query.edit_message_text(text=f"playing on {data[1].friendly_name} has been stopped")

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("a) Send audio url\nb) Share radio station from radio garden APP\nc) /status check device status")

def status(update: Update, context: CallbackContext) -> None:

    device_list = devicelist()
    if device_list.count == 0:
         update.message.reply_text('no device available')
         return

    keyboard = []
    for device in device_list:
        data = ["stop", device]
        keyboard.append([InlineKeyboardButton(device.friendly_name, callback_data=data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("stop playing on:", reply_markup=reply_markup)

###########################################3

for env in ["tgtoken","tgchatid"]:
    if env not in environ:
        print(env + ' not found')
        exit()
del env

updater = Updater(getenv('tgtoken'), arbitrary_callback_data=True)
idflt = Filters.chat(int(getenv('tgchatid')))
urlflt = Filters.regex(r'^https?:\/\/.+$')
updater.dispatcher.add_handler(CommandHandler('start', start, idflt))
updater.dispatcher.add_handler(CommandHandler('status', status, idflt))
updater.dispatcher.add_handler(MessageHandler(urlflt & idflt, urlhandler))
updater.dispatcher.add_handler(CallbackQueryHandler(btnhandler))
updater.start_polling()
updater.idle()
