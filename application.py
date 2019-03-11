import discord
import asyncio
import gspread
from oauth2client.service_account import ServiceAccountCredentials

class MyClient(discord.Client):

    def __init__(self, sheets_client):
        discord.Client.__init__(self)
        self.sheets = sheets_client
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
            #sheet = self.sheets.open(message.user.display_name).sheet1
            #print("------")
            #print(response)
            #print("------")
            await message.channel.send(response)
        elif message.content.startswith('!sleep'):
            with message.channel.typing():
                await asyncio.sleep(5.0)
                await message.channel.send('Done sleeping.')

    def execute_command(self, message, messagecommand):
        #print("==============")
        index = messagecommand.find(' ')
        #print(index)
        command = messagecommand[:index] if index!=-1 else messagecommand
        args = messagecommand[index+1:] if index!=-1 else ""
        #print("Parsed {} into {} and {}.".format(messagecommand, command, args))
        response = "Unable to parse command {}".format(messagecommand)
        if command in ['cf','csf']:
            if args == "":
                args = message.author.nick
            try:
                workbook = self.load_sheet(args)
                return format_character_description_2(workbook)
            except Exception as e:
                raise e
                return "Error"

        if command in ['c','cs']:
            if args == "":
                args = message.author.nick
            try:
                workbook = self.load_sheet(args)
                return format_character_description(workbook.sheet1.get_all_values())
            except Exception as e:
                raise e
                return "Error"
        else:
            return "invalid command"


    def load_sheet(self, character):
        if character in self.sheetcache:
            return self.sheetcache[character]
        else:
            self.sheetcache[character] = self.sheets.open(character)
            return self.sheetcache[character]

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
    maxload = vals[c1[0]+1][c1[1]][14:]
    inventory = "**Inventory ({}/{})**\n".format(vals[c1[0]][c1[1]], maxload)
    for x in items:
        name = x[0]
        tags = x[1]
        weight = x[2]
        s = ""
        if tags == "":
            inventory += "{} (weight {})\n".format(name, weight)
        else:
            inventory += "{} ({}, weight {})\n".format(name,tags,weight)
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


# use creds to create a client to interact with the Google Drive API
sheetscope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
sheetcreds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', sheetscope)
sheetclient = gspread.authorize(sheetcreds)
print(sheetclient)

with open('discordsecret', 'r') as myfile:
    discordkey=myfile.read().replace('\n', '')

client = MyClient(sheetclient)
client.run(discordkey)

