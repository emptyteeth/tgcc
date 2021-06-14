#!/usr/bin/env python

import zeroconf
import pychromecast
from time import sleep
from os import environ, getenv
from uuid import UUID
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler, CallbackContext

class MyCastListener(pychromecast.discovery.AbstractCastListener):
    def add_cast(self, uuid, _service):
        pass
    def remove_cast(self, uuid, _service, cast_info):
        browser.services.clear()
    def update_cast(self, uuid, _service):
        pass

def geturl(update: Update, context: CallbackContext) -> None:
    global url
    url = update.message.text
    keyboard = []
    for uuid, service in browser.services.items():
        keyboard.append([InlineKeyboardButton(format(service.friendly_name), callback_data=format(uuid))])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose:', reply_markup=reply_markup)

def play(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    device = browser.services[UUID(query.data)]
    query.edit_message_text(text=f"play {url} on {device[3]}")
    cast = pychromecast.get_chromecast_from_cast_info(device, zconf)
    cast.wait()
    cast.media_controller.play_media(url,'audio')
    sleep(2)
    cast.media_controller.block_until_active()
    cast.media_controller.play()
    cast.disconnect()

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
updater.dispatcher.add_handler(MessageHandler(Filters.text & Filters.chat(int(getenv('tgchatid'))), geturl))
updater.dispatcher.add_handler(CallbackQueryHandler(play))
updater.start_polling()
updater.idle()
