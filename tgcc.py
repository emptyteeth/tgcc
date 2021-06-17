#!/usr/bin/env python

import zeroconf
import pychromecast
from urllib import request
from time import sleep
from os import environ, getenv
from uuid import UUID
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext,CommandHandler

class MyCastListener(pychromecast.discovery.AbstractCastListener):
    def add_cast(self, uuid, _service):
        pass
    def remove_cast(self, uuid, _service, cast_info):
        browser.services.clear()
    def update_cast(self, uuid, _service):
        pass

def help(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Send the audio url to play\nSend status command to get device status and a button to stop the playing")

def btnhandler(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    data = query.data.split(",")
    if data[0] == 'play':
        query.edit_message_text(text=f"play {urlinfo[3]} on {data[2]}")
        play(data[1])
    if data[0] == 'stop':
        query.edit_message_text(text=f"stop playing on {data[2]}")
        stop(data[1])

def geturl(update: Update, context: CallbackContext) -> None:
    if browser.count == 0:
        update.message.reply_text('no device available')
        return
    url = update.message.text
    global urlinfo
    urlinfo = parseurl(url)
    if urlinfo[0] == 0:
        update.message.reply_text('bad url')
        return
    if not urlinfo[2].startswith('audio'):
        update.message.reply_text('not an audio url')
        return
    keyboard = []
    for uuid, service in browser.services.items():
        data = ",".join(['play',str(uuid),str(service.friendly_name)])
        keyboard.append([InlineKeyboardButton(format(service.friendly_name), callback_data=data)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Play "+urlinfo[3]+" on:", reply_markup=reply_markup)

def status(update: Update, context: CallbackContext) -> None:
    if browser.count == 0:
        update.message.reply_text('no device available')
        return
    keyboard = []
    states = []
    for uuid, service in browser.services.items():
        data = ",".join(['stop',str(uuid),str(service.friendly_name)])
        keyboard.append([InlineKeyboardButton(format(service.friendly_name), callback_data=data)])
        states.append(getstatus(str(uuid)))
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(str(states)+"\n\n"+'Stop playing on:', reply_markup=reply_markup)

def play(uuid:str):
    device = browser.services[UUID(uuid)]
    cast = pychromecast.get_chromecast_from_cast_info(device, zconf)
    cast.wait()
    sleep(2)
    cast.media_controller.play_media(urlinfo[1],urlinfo[2],urlinfo[3])
    cast.media_controller.block_until_active()
    cast.media_controller.play()
    cast.disconnect()

def stop(uuid:str):
    device = browser.services[UUID(uuid)]
    cast = pychromecast.get_chromecast_from_cast_info(device, zconf)
    cast.wait()
    sleep(2)
    cast.quit_app()
    cast.disconnect()

def getstatus(uuid:str) -> list:
    device = browser.services[UUID(uuid)]
    cast = pychromecast.get_chromecast_from_cast_info(device, zconf)
    cast.wait()
    sleep(2)
    mc = cast.media_controller.status
    state = [cast.name,cast.is_idle,mc.title,mc.content_id,mc.content_type]
    cast.disconnect()
    return state

def parseurl(url: str) -> list:
    try:
        r = request.urlopen(url)
        if r.code != 200:
            r.close()
            return [0]
        else:
            h = r.headers
            result = [1,r.url,h.get('Content-Type'),h.get('icy-name')]
            r.close()
            return result
    except:
        return [0]

##########################################

for env in ["tgtoken","tgchatid"]:
    if env not in environ:
        print(env + ' not found')
        exit()
del env

zconf = zeroconf.Zeroconf()
browser = pychromecast.discovery.CastBrowser(MyCastListener(), zeroconf_instance=zconf)
browser.start_discovery()

updater = Updater(getenv('tgtoken'))
idflt = Filters.chat(int(getenv('tgchatid')))
urlflt = Filters.regex(r'^https?:\/\/.+$')
updater.dispatcher.add_handler(CommandHandler('help', help, idflt))
updater.dispatcher.add_handler(CommandHandler('status', status, idflt))
updater.dispatcher.add_handler(MessageHandler(urlflt & idflt, geturl))
updater.dispatcher.add_handler(CallbackQueryHandler(btnhandler))
updater.start_polling()
updater.idle()
