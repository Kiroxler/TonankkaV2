import discord
import random

from datetime import datetime
from dateutil.parser import parse
from discord.ext import tasks
from timedEvents import haalarimerkit_rewrite, tapahtumat_rewrite

import settings
import botToken
import commandHandler, databaseHandler as db

activityTypes = { 'WATCHING': discord.ActivityType.watching, 'LISTENING': discord.ActivityType.listening }

def get_last_check_date():
    raw_date = db.readTable('database')['lastEventLoopDateCheck']
    # remove milliseconds
    raw_date = raw_date.split('.')[0]
    return datetime.strptime(raw_date, '%Y-%m-%d %H:%M:%S')

client = discord.Client()
commands = commandHandler.loadCommands()
if not db.isTable('database'):
    db.createTable('database')
    db.writeTable('database', {'lastEventLoopDateCheck': datetime.now()})

async def changePresence():
    dbData = db.readTable('activities') # get data from activities.json
    activityToBeSet = random.choice(dbData) # select a random activity from the list
    if type(activityToBeSet) is str: # all string items in the list are automatically games
        game = discord.Game(activityToBeSet)
        await client.change_presence(activity=game) # create discord.Game activity type and set active activity
    else:
        # get watching and listening activity types from activityTypes list using 'type' value
        await client.change_presence(activity=discord.Activity(type=activityTypes[activityToBeSet['type']], name=activityToBeSet["name"]))

@tasks.loop(hours=1.0)
async def timedEventLoop():
    print(f"[{datetime.strftime(datetime.now(), '%H:%M')}] Timed Events")
    await changePresence()

    try:
        check_date = get_last_check_date()
        await tapahtumat_rewrite.postNewEvents(client, check_date)
        # await haalarimerkit_rewrite.postNewPatches(client, check_date)

        db.writeTable('database', {'lastEventLoopDateCheck': datetime.now()})

    except Exception as e:
        print(e)

async def runStartUpTasks():
    print("Running Start Up tasks...")
    timedEventLoop.start() # start the loop

@client.event
async def on_ready():
    await runStartUpTasks()
    print("All done!")
    print(f"We have logged in as {client.user}") # lähetä viesti konsoliin, kun botti käynnistyy

@client.event
async def on_message(message):
    if message.author == client.user: return # estä bottia vastaamsta itselleen, jos viestin lähettäjä on sama kuin botti
    if not message.content.startswith(settings.commandPrefix): return # jos viesti EI ala settings.py-tiedostossa määritetyllä prefixillä, peruuta

    message.content = message.content[1:] # poista viestistä prefix
    args = message.content.split() # splitataan viestin/komennon sanat välilyönnin kohdalla -> luodaan lista

    if( args[0] in commands.keys() ): # jos viestin ensimmäinen sana on jokin komennoista commands-dictionaryssä
        await commands[args[0]]['execute'](message, args, client,commands) # suorita execute-funktio kutsutun komennon tiedostossa

client.run(botToken.token)
