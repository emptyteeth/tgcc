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

def start(update: Update, context: CallbackContext) -> None:
    """
    handle "/start" command from human, so that to humiliate them decently
    """
    update.message.reply_text("a) Send audio url\nb) Share radio station from radio garden APP\nc) /status check device status")

def geturl(update: Update, context: CallbackContext) -> None:
    """
    handle url message from human
    """
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
    playbtn(update)

def rgurl(update: Update, context: CallbackContext) -> None:
    """
    handle the url message from radio garden app sharing
    """
    if browser.count == 0:
        update.message.reply_text('no device available')
        return
    url = 'https://radio.garden/api/ara/content/listen/'+update.message.text[-8:]+'/channel.mp3'
    global urlinfo
    urlinfo = parseurl(url)
    if urlinfo[0] == 0:
        update.message.reply_text('bad url')
        return
    if not urlinfo[2].startswith('audio'):
        update.message.reply_text('not an audio url')
        return
    playbtn(update)

def status(update: Update, context: CallbackContext) -> None:
    """
    handle "/status" command. reply device status, populate stop buttons
    """
    if browser.count == 0:
        update.message.reply_text('no device available')
        return
    keyboard = []
    states = []
    for uuid, service in browser.services.items():
        state = wtf(uuid).getstatus()
        states.append(state)
        if state[1] == True:
            continue
        data = ",".join(['stop',str(uuid),str(service.friendly_name)])
        keyboard.append([InlineKeyboardButton(format(service.friendly_name), callback_data=data)])
    if len(keyboard) == 0:
        update.message.reply_text(str(states))
    else:
        reply_markup = InlineKeyboardMarkup(keyboard)
        # this is ugly, I think I'll just bear with it until I've learned how to do the string things. other codes are ugly too btw :)
        update.message.reply_text(str(states)+"\n\n"+'Stop playing on:', reply_markup=reply_markup)

def playbtn(update: Update) -> None:
    keyboard = []
    for uuid, service in browser.services.items():
        data = ",".join(['play',str(uuid),str(service.friendly_name)])
        keyboard.append([InlineKeyboardButton(format(service.friendly_name), callback_data=data)])
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("Play "+urlinfo[3]+" on:", reply_markup=reply_markup)

def btnhandler(update: Update, context: CallbackContext) -> None:
    """
    handle all human's butts
    """
    query = update.callback_query
    query.answer()
    data = query.data.split(",")
    if data[0] == 'play':
        if wtf(UUID(data[1])).play() == 0:
            query.edit_message_text(text=f"play {urlinfo[3]} on {data[2]}")
        else:
            query.edit_message_text(text=f"operation failed on {data[2]}")

    elif data[0] == 'stop':
        if wtf(UUID(data[1])).stop() == 0:
            query.edit_message_text(text=f"stop playing on {data[2]}")
        else:
            query.edit_message_text(text=f"operation failed on {data[2]}")

class wtf():
    """
    just learned the class thing, and run out of names.
    """
    def __init__(self,uuid:UUID) -> None:
        device = browser.services[uuid]
        self.cast = pychromecast.get_chromecast_from_cast_info(device, zconf)
        self.cast.wait(3)
        sleep(2)
    def play(self) -> int:
        """
        start playing. return int 0->success 1->fail
        """
        try:
            self.cast.media_controller.play_media(urlinfo[1],urlinfo[2],urlinfo[3])
            self.cast.media_controller.block_until_active()
            self.cast.media_controller.play()
            self.cast.disconnect()
            return 0
        except:
            self.cast.disconnect()
            return 1
    def stop(self) -> int:
        """
        stop playing. return int 0->success 1->fail
        """
        try:
            self.cast.quit_app()
            self.cast.disconnect()
            return 0
        except:
            self.cast.disconnect()
            return 1
    def getstatus(self) -> list:
        """
        return device status.
        [device_name, idle_bool, content_title, content_id, content_type]
        """
        sleep(1)
        mc = self.cast.media_controller.status
        state = [self.cast.name,self.cast.is_idle,mc.title,mc.content_id,mc.content_type]
        self.cast.disconnect()
        return state

def parseurl(url: str) -> list:
    """
    shouldn't use r.close()?
    DON'T WANT TO KNOW
    """
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
rgflt = Filters.regex(r'^.*https:\/\/radio.garden\/listen\/.+$')
urlflt = Filters.regex(r'^https?:\/\/.+$')
updater.dispatcher.add_handler(CommandHandler('start', start, idflt))
updater.dispatcher.add_handler(CommandHandler('status', status, idflt))
updater.dispatcher.add_handler(MessageHandler(rgflt & idflt, rgurl))
updater.dispatcher.add_handler(MessageHandler(urlflt & idflt, geturl))
updater.dispatcher.add_handler(CallbackQueryHandler(btnhandler))
updater.start_polling()
updater.idle()
