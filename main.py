# This is a discord bot for a Dnd server
#The idea is that the bot helps user organize their sesions as well as to add flavour to their server.
import discord
from discord.ext import commands
import os
from replit import db
import quest as qdt
import asyncio
import keep_alive

TOKEN = os.environ['BOT_TOKEN']
SCHEDULE_URL = os.environ['SCHEDULE_URL']

helpmsg = {
    'help':
    ' Displays a list of available commands. ',
    'request':
    ' Generates a new request to add to the questlog given a title for the request. Ex. %request A Cool Name',
    'completed':
    ' Given a quest name, it closes the quest, removing it from the questlog, and gives the corresponding reward to the adventurer team. Ex. %completed A Cool Name',
    'cancel':
    ' Given a quest name it closes the quest, removing it from the questlog, and it does not give any rewards. Ex. %cancel A Lame Quest',
    'reward':
    ' Given a quest name, it adds or modifies the reward of the quest. Ex. %reward A quest ',
    'require':
    ' Given a quest name, it adds or modifies the requirements of the quest. Ex. %require A quest ',
    'description':
    ' Given a quest name, it modifies the description of the quest. Ex. %description A quest ',
    'changename':
    ' Given a quest name, it changes the name of the given quest with a new one. Ex. %changename old name',
    'list':
    ' It lists all of the available quests. Ex. %list',
    'check':
    ' Given a quest name, displays the requested quest. Ex. %check a quest',
    'join':
    ' Given a quest name, it adds the user as an adventurer on the quest team. Ex. %join a quest',
    'abandon':
    ' Given a quest name, it removes the user as an adventurer on the quest team. Ex. %abandon a quest',
    'img':
    ' Given a quest name, it adds a thumbnail to the quest post. Ex. %img quest'
}
# Change only the no_category default string
help_command = commands.DefaultHelpCommand(
    no_category = 'Commands'
)
#client = discord.Client()
bot = commands.Bot(command_prefix="%",description = "Hello! How can I help you! Here I am gonna list the commands you can use:" ,help_command = help_command)


#################################
# Database interaction functions
#################################


#Function that turns an quest into a json obj
def quest_to_dict(quest):
    obj = {
        "title": quest.title,
        "desc": quest.desc,
        "adventurers": quest.adventurers,
        "reward": quest.reward,
        "requirements": quest.requirements,
        "img": quest.img
    }
    return obj

#Function that turns a dict into a quest object
def dict_to_quest(obj):
    quest = qdt.questdt(obj['title'])
    quest.desc = obj['desc']
    quest.adventurers = obj["adventurers"]
    quest.reward = obj["reward"]
    quest.requirements = obj['requirements']
    quest.img = obj['img']
    return quest


#This function will update the db questlog
def update_questlog(newQuest, server):
    if server in db.keys():
        questlog = db[server]
        notFound = True
        for quest in questlog:
            if quest['title'].lower() == newQuest.title.lower():
                quest.update(quest_to_dict(newQuest))
                notFound = False

        if notFound:
            questlog.append(quest_to_dict(newQuest))

        db[server] = questlog
    else:
        db[server] = [quest_to_dict(newQuest)]
    


#A function that retrives the quest data from the db given a quest name. In case that it does not finds it it returns an None
def retrive_quest(questName, server):
    questlog = db[server]
    if len(questlog) > 0:
        for quest in questlog:
            if (quest["title"].lower() == questName.lower()):
                return dict_to_quest(quest)

        return None
    else:
        return None


#Removes the quest form the questlog
def remove_quest(oldQuest, server):
    questlog = db[server]
    db[server] = [
        quest for quest in questlog
        if not quest["title"].lower() == oldQuest.lower()
    ]


#Functions that creates a new quest
def new_quest(questTitle, questDesc, server):
    qt = qdt.questdt(questTitle)
    qt.desc = questDesc
    update_questlog(qt,server)
    return generate_quest_embed(qt)


##################################
# Helper fucntion to create embeds
#################################

#Create the quest Embed
def generate_quest_embed(quest):
    qEmb = discord.Embed(title=quest.title,url=SCHEDULE_URL,description=quest.desc,color=0x15616D)
    if (quest.adventurers != []):
        advent = ", ".join(quest.adventurers)
    else:
        advent = "None"
    qEmb.add_field(name="Adventurers", value=advent, inline=False)
    if quest.reward != '':
        qEmb.add_field(name="Reward", value=quest.reward, inline=False)
    if quest.requirements != '':
        qEmb.add_field(name="Requirements", value=quest.requirements, inline=False)
    
    if quest.img != '':
        qEmb.set_thumbnail(url=quest.img)

    print("Inside of the embed gen:")
    print(qEmb)
    return qEmb

@bot.event
async def on_ready():
    print("Logged in as [{0.user}]".format(bot))





########################################################
# Bot Commands Logic
#########################################################



#----------------------------------------------------
#Quest modifier commands
#----------------------------------------------------
#@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
#	help="Looks like you need some help.",
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
#	brief="Prints the list of values back to the channel."
#)
#async def cmd(msg, arg):

@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help= helpmsg["request"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Makes a new quest"
)
async def request(msg, *, arg):
    print('Request cmd was issued')

    title = arg
    ser = str(msg.guild)
    qt = retrive_quest(title,ser)
    print(qt)
    if qt != None:
      await msg.channel.send('> **A quest with the same name alredy exists**')
    else:
      if title == '':
          await msg.channel.send('> **Sorry i did not catch**')
          return
      #Get request title
      print('new request is: ' + title)
      #Getting the request description.
      await msg.channel.send("> *Type the description of the request:*")

      def is_auth(m):
          return m.author == msg.author

      try:
          print('waiting for response')
          mdesc = await bot.wait_for('message',
                                        check=is_auth,
                                        timeout=60)
      except asyncio.TimeoutError:
          return await msg.channel.send(
              "> *The time to write the description is done, the request will not be added.*"
          )
      desc = mdesc.content
      print('Description: ' + desc)
      emd = new_quest(title, desc, ser)


      await msg.channel.send(embed=emd)

#Error handling request
@request.error
async def request_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%request**: ' + helpmsg["request"])
    
    
#Completed cmd; it closes a quest giving the reward to the adventurers
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help= helpmsg["completed"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Marks the given quest as completed"
)
async def completed(msg,*, arg):
    
    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title,ser)
    if quest != None:
        if (quest.adventurers != []):
            advent = ", ".join(quest.adventurers)
        else:
            advent = "me"
        rew = quest.reward
        remove_quest(title,ser)
        if (rew != ''):
            congratText = "Great job finishing your quest " + advent + ". The rewards for your team are:\n" + rew
        else:
            congratText = "Great job finishing your quest " + advent

        emd = discord.Embed(title="Congratulations!!!",
                            description=congratText,
                            color=0x40F99B)
        await msg.channel.send(embed=emd)
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling completed
@completed.error
async def completed_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%completed**: ' + helpmsg["completed"])
            

    #Cancel cmd; It removes a quest form the questlog without giving rewards
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help= helpmsg["cancel"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Cancels a quest"
)
async def cancel(msg,*, arg):
    print('Cancel cmd was issued')
    
    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title,ser)
    if quest != None:
        remove_quest(title, ser)
        emd = discord.Embed(
            title="Quest Canceled",
            description=
            "*Shame to see the request be canceled, I'll update the questlog.*",
            url=SCHEDULE_URL,
            color=0xFF312E)
        await msg.channel.send(embed=emd)
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

            
 #Error handling canceled
@cancel.error
async def cancel_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%cancel**: ' + helpmsg["cancel"])           
            
            
#reward cmd; Adds a reward to a quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=helpmsg["reward"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Adds a reward to the quest"
)
async def reward(msg, *, arg):
    print('Reward cmd was issued')

    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title, ser)
    if quest != None:

        await msg.channel.send(
            '> *What is the reward you want to add to this quest?*')

        def is_auth(m):
            return m.author == msg.author

        try:
            print('waiting for response')
            mrew = await bot.wait_for('message',
                                         check=is_auth,
                                         timeout=60)
        except asyncio.TimeoutError:
            return await msg.channel.send(
                "> *The time to write the reward is done, the request will not be modified.*"
            )
        quest.reward = mrew.content
        update_questlog(quest,ser)
        await msg.channel.send('> *There it is!\n> Now lets see...*')
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling reward
@reward.error
async def reward_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%reward**: ' + helpmsg["reward"])
        

        
        
#require cmd; Add a requirement to a quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=helpmsg["require"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Adds a requirement to a quest"
)
async def require(msg,*, arg):
    print('Require cmd was issued')
   
    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title, ser)
    if quest != None:

        await msg.channel.send(
            '> *What is the requirement you want to add to this quest?*'
        )

        def is_auth(m):
            return m.author == msg.author

        try:
            print('waiting for response')
            mreq = await bot.wait_for('message',
                                         check=is_auth,
                                         timeout=60)
        except asyncio.TimeoutError:
            return await msg.channel.send(
                "> *The time to write the requirement is done, the request will not be modified.*"
            )
        quest.requirements = mreq.content
        update_questlog(quest, ser)
        await msg.channel.send('> *There it is!\n> Now lets see...*')
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling require
@require.error
async def require_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%require**: ' + helpmsg["require"])
        
        
        
#description cmd; change description of a quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=helpmsg["description"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Changes the description of a quest"
)
async def description(msg,*, arg):
    print('Description cmd was issued')

    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title, ser)
    if quest != None:

        await msg.channel.send(
            '> *What is the new description you want to give to this quest?*'
        )

        def is_auth(m):
            return m.author == msg.author

        try:
            print('waiting for response')
            mdesc = await bot.wait_for('message',
                                          check=is_auth,
                                          timeout=60)
        except asyncio.TimeoutError:
            return await msg.channel.send(
                "> *The time to write the description is done, the request will not be modified.*"
            )
        quest.desc = mdesc.content
        update_questlog(quest,ser)
        await msg.channel.send('> *There it is!\n> Now lets see...*')
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling description
@description.error
async def description_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%description**: ' + helpmsg["description"])
        
        
        
#changename cmd; changes the title of a quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=helpmsg["changename"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Changes the name of a quest"
)
async def changename(msg,*, arg):
    print('Changename cmd was issued')

    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return

    quest = retrive_quest(title, ser)
    if quest != None:

        await msg.channel.send(
            '> *What is the new title you want to give to this quest?*'
        )

        def is_auth(m):
            return m.author == msg.author

        try:
            print('waiting for response')
            mtitle = await bot.wait_for('message',
                                           check=is_auth,
                                           timeout=60)
        except asyncio.TimeoutError:
            return await msg.channel.send(
                "> *The time to write the title is done, the request will not be modified.*"
            )
        remove_quest(title, ser)
        quest.title = mtitle.content

        update_questlog(quest,ser)
        await msg.channel.send('> *There it is!\n> Now lets see...*')
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling changename
@changename.error
async def changename_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%changename**: ' + helpmsg["changename"])
        
    
#img cmd; Adds a thumbnail to the quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=helpmsg["img"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Adds/Changes an image of a quest"
)
async def img(msg,*, arg):
    print('Img cmd was issued')

    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    print(title)
    quest = retrive_quest(title, ser)
    if quest != None:

        await msg.channel.send(
            '> *What is the new image you want to give to this quest? (the image given must be an url to the image ex:https://i.imgur.com/ljNRYry.jpeg )*'
        )

        def is_auth(m):
            return m.author == msg.author

        try:
            print('waiting for response')
            mimg = await bot.wait_for('message',
                                         check=is_auth,
                                         timeout=60)
        except asyncio.TimeoutError:
            return await msg.channel.send(
                "> *The time to give an image is done, the request will not be modified.*"
            )
        remove_quest(title, ser)
        quest.img = mimg.content

        update_questlog(quest, ser)
        await msg.channel.send('> *There it is!\n> Now lets see...*')
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling img
@img.error
async def img_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%img**: ' + helpmsg["img"])
        

#---------------------------------------------------------
#Checking and joining quest cmds
#----------------------------------------------------------


#list cmd; Lists available quests
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help= helpmsg['list'],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief= 'Lists the quests on the questlog'
)
async def list(msg):
    print('List cmd was issued')
    await msg.channel.send('> *Let me fetch the questlog...*')
    lst = ''
    ser = str(msg.guild)
    for quest in db[ser]:
        lst = lst + '\n' + quest['title']
    emd = discord.Embed(title="Available quests:",
                        description=lst,
                        color=0xF5FBEF)
    await msg.channel.send(embed=emd)

#check cmd; Check a single quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help= helpmsg["check"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief= "Displays a quest"
)
async def check(msg,*, arg):
    print('Check cmd was issued')
    
    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title, ser)
    if quest != None:
        await msg.channel.send('> *There it is!\n> Now lets see...*')
        print(quest.desc)
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling
@check.error
async def check_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%check**: ' + helpmsg["check"])        
        

        
#join cmd;Join a quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help= helpmsg["join"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief= "Adds a player to a quest"
)
async def join(msg,*, arg):
    print('Join cmd was issued')

    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title, ser)
    if quest != None:
        pc = str(msg.author.mention)
        if  pc not in quest.adventurers:
          quest.adventurers.append(pc)
        
        await msg.channel.send('> *Understood! Let me make the change*'
                               )
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

        
        
#Error handling join
@join.error
async def join_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%join**: ' + helpmsg["join"])
        
        

#abandon cmd; abandond a quest
@bot.command(
	# ADDS THIS VALUE TO THE $HELP PRINT MESSAGE.
	help=helpmsg["abandon"],
	# ADDS THIS VALUE TO THE $HELP MESSAGE.
	brief="Removes a player from a quest"
)
async def abandon(msg,*, arg):
    
    title = arg
    ser = str(msg.guild)
    if title == '':
        await msg.channel.send('> **Sorry i did not catch**')
        return
    quest = retrive_quest(title, ser)
    if quest != None:
        #Removing duplicates
        pc = str(msg.author.mention)
        quest.adventurers  = [
            adv for adv in quest.adventurers
            if not adv == pc
        ]
        #Removing the player
        quest.adventurers
        print(quest.adventurers)
        update_questlog(quest, ser)
        await msg.channel.send('> *Very well then!*')
        await msg.channel.send(embed=generate_quest_embed(quest))
    else:
        await msg.channel.send(
            "> *The quest was not found in our questlog, please try to write the correct quest name.*"
        )

#Error handling abandon
@abandon.error
async def abandon_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.channel.send('> **%abandon**: ' + helpmsg["abandon"])
        
        
        
@bot.event
async def on_message(message):
	await bot.process_commands(message)       
        
keep_alive.keep_alive()
bot.run(TOKEN)
