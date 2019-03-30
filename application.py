import discord
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import random
import re
import dice

affirmatives = ["ye","yes","Ye","Yes","Y","y"]

class MyClient(discord.Client):

    def __init__(self, sheets_creds):
        discord.Client.__init__(self)
        self.sheets_creds = sheets_creds
        self.sheetcache = {}

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return
        if message.content.startswith('!dw'):
            response = self.execute_command(message, message.content[4:])
            await message.channel.send(response)
        elif message.content.startswith('!r'):
            response = self.execute_command(message, "rr " + message.content[3:])
            await message.channel.send(response)

    def execute_command(self, message, messagecommand):
        #print("==============")
        index = messagecommand.find(' ')
        #print(index)
        command = messagecommand[:index] if index!=-1 else messagecommand
        args = messagecommand[index+1:] if index!=-1 else ""
        #print("Parsed {} into {} and {}.".format(messagecommand, command, args))
        response = "Unable to parse command {}".format(messagecommand)
        try:
            if command in ['cf','csf']:
                if args == "":
                    args = message.author.nick
                workbook = self.load_sheet(args)
                return format_character_description_2(workbook)
            if command in ['c','cs']:
                if args == "":
                    args = message.author.nick
                workbook = self.load_sheet(args)
                return format_character_description(workbook.sheet1.get_all_values())
            if command in ['r']:
                return self.roll_move(message, args)
            if command in ['rr']:
                return self.roll(message, args)
            else:
                return "invalid command"
        except Exception as e:
            print(e)
            return "Error"

    def roll(self, message, args):
        sheet = self.load_sheet(message.author.nick).sheet1
        roll = args
        statLocations = {'STR':[6,4],
                 'DEX':[6,5],
                 'CON':[6,6],
                 'INT':[6,7],
                 'WIS':[6,8],
                 'CHA':[6,9],
                 }
        for statname, idx in statLocations.items():
            statbonus = sheet.cell(idx[0], idx[1]).value
            print("{}|{}".format(statname,statbonus))
            args = args.replace(statname,statbonus)
            roll = roll.replace(statname,"{}({})".format(statname,statbonus))
        print('------------\n')
        print(roll)
        print('\n')
        print(args)
        print('------------\n')
        return "rolling for {}: {} = {}".format(message.author.nick, roll, dice.roll(args))

    def roll_move(self, message, args):
        args = args.replace(" ","")
        args = args.replace("+","")
        sheet = self.load_sheet(message.author.nick).sheet1
        x = {'STR':[6,4],
             'DEX':[6,5],
             'CON':[6,6],
             'INT':[6,7],
             'WIS':[6,8],
             'CHA':[6,9],
             }[args[:3]]

        stat = int(sheet.cell(x[0],x[1]).value)
        const = 0
        if(len(args) > 3):
            const=int(args[3:])
        dice = random.randint(1,6)+random.randint(1,6)
        roll = "2d6({})+{}({}){}".format(dice, args[:3], stat, (('' if const<0 else '+') +str(const)) if const != 0 else '')
        return "rolling for {}: {} = {}".format(message.author.nick, roll, dice+stat+const)


    def load_sheet(self, character):
        self.sheets = gspread.authorize(self.sheets_creds)
        return self.sheets.open(character)

def format_character_description(vals):
    return ("**__{} the {}__**\n".format(vals[2][1],vals[0][0])
    +"----------\n"
    +"STR {} ({})\n".format(vals[4][3],vals[5][3])
    +"DEX {} ({})\n".format(vals[4][4],vals[5][4])
    +"CON {} ({})\n".format(vals[4][5],vals[5][5])
    +"INT {} ({})\n".format(vals[4][6],vals[5][6])
    +"WIS {} ({})\n".format(vals[4][7],vals[5][7])
    +"CHA {} ({})\n".format(vals[4][8],vals[5][8])
    +"----------\n"
    +"Hit Points: {}/{}\n".format(vals[10][1],vals[9][1])
    +"Damage: {}\n".format(vals[11][1])
    +"Level: {}\n".format(vals[1][4])
    +"Experience: {}\n".format(vals[3][9][18:]))

def format_character_description_2(workbook):
    charvals = workbook.sheet1.get_all_values()
    stats = format_character_description(charvals)
    bonds = format_bonds(charvals)
    inventory = format_inventory(charvals,10,4,15,[8,5])
    character = (stats
            +"----------\n"
            +bonds
            +"----------\n"
            +inventory
            +"----------\n"
            )
    if charvals[0][0] == 'Ranger':
        character = character + format_companion(workbook.get_worksheet(2).get_all_values()) + "----------\n"
    if charvals[0][0] == 'Wizard':
        character = character + format_spells(workbook.get_worksheet(1).get_all_values()) + "----------\n"
    return character

def format_bonds(vals):
    bondcount = int(vals[12][0][7])
    bonds = "**Bonds**\n"
    for i in range(bondcount):
        bonds += vals[14+2*i][0].replace('_','\\_') + "\n"
    return bonds

def format_inventory(vals,b1,b2,l,c1):
    items = []
    for i in range(l):
        x = (vals[b1+i][b2],vals[b1+i][b2+1],vals[b1+i][b2+2])
        #print(x)
        if x[0]!="" or x[1]!="" or x[2]!="":
            #print(x)
            items.append(x)
    currentload = vals[c1[0]+1][c1[1]][14:]
    inventory = "**Inventory ({}/{})**\n".format(currentload, vals[c1[0]][c1[1]])
    for x in items:
        name = x[0]
        weight = x[1]
        tags = x[2]
        s = ""
        if tags == "":
            inventory += "{} ({} weight)\n".format(name, weight)
        else:
            inventory += "{} ({}, {} weight)\n".format(name,tags,weight)
    return inventory

def format_companion(vals):
    return ("__**{}**__\n".format(vals[0][0])
    +"-----\n"
    +"Localty: {}\n".format(vals[2][2])
    +"Damage: {}\n".format(vals[3][2])
    +"Armor: {}\n".format(vals[4][2])
    +"Hit Points: {}/{}\n".format(vals[5][2],vals[6][2])
    +"Instinct: {}\n".format(vals[20][0])
    +"Cost: {}\n".format(vals[20][3])
    +"-----\n"
    +"**Tags**\n"
    +vals[1][3]+"\n"
    +"**Moves**\n"
    +vals[3][3]+"\n"
    +"-----\n"
    +format_inventory(vals,11,1,8,[9,2]))

def format_spells(vals):
    val = "__**Spells**__\n-----\n"
    for i in range(2,40):
        if i >= len(vals):
            break
        row = vals[i]
        val += "**{}** ({}) *{}*\n".format(row[0],row[1], "prepared" if row[2] in affirmatives else "")
    return val


# use creds to create a client to interact with the Google Drive API
sheetscope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
sheetcreds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', sheetscope)
#sheetclient = gspread.authorize(sheetcreds)
#print(sheetclient)

with open('discordsecret', 'r') as myfile:
    discordkey=myfile.read().replace('\n', '')

client = MyClient(sheetcreds)
client.run(discordkey)

