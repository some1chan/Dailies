# Dailies bot by Grant Scrits 
#        @GeekOverdriveUS

import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.ext.commands import CommandNotFound
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import random
import time
import requests
from datetime import datetime, timedelta
from dateutil import tz
from calendar import monthrange
import operator
import math
import json
import os
import sys

from dotenv import load_dotenv
load_dotenv()
BOT_ID = os.getenv("DISCORD_TOKEN")

# Switched to Ints to comply with new Discord.py conventions for IDs
DAILY_CHANNEL_ID = int(os.getenv("DAILY_CHANNEL_ID"))
DDISC_CHANNEL_ID = int(os.getenv("DDISC_CHANNEL_ID"))
SPAM_CHANNEL_ID  = int(os.getenv("SPAM_CHANNEL_ID"))
STREAKER_NOTIFY_ID = int(os.getenv("STREAKER_NOTIFY_ID"))

API_HOST = os.getenv("API_HOST", "http://localhost:42069")

API = {
    "getURL": API_HOST + "/api/v0/discord/embedtemplate",
    "postURL": API_HOST + "/api/v0/dailies/version"
}

class Streaker:
  def __init__(self, id, name=None, lpt=None, streak=1, weekStreak=0, streakRecord=0, streakAllTime=0, mercies=0, casual = False):
    self.id = id
    self.name = name
    if (lpt): self.lastPostTime = lpt
    else:     self.lastPostTime = datetime.utcnow()
    self.streak = streak
    self.weekStreak = weekStreak
    self.streakRecord = streakRecord
    self.streakAllTime = streakAllTime
    self.mercies = mercies
    self.casual = casual # Parry this you filthy casual

streakers = []
streakMilestones = {}
lastDay = 0
lastLBMessage = None
lastCMDMessage = None

bot = commands.Bot(command_prefix='!')
bot.remove_command("help")

def main():
    global lastDay

    lastDay = datetime.utcnow().day
    load_backup()

    bot.run(BOT_ID)


@bot.event
async def on_ready():

    # This is all a nice simple hack to improvise a version control system out of the streak user system
    # -[
    found_update_user = False

    version = "1.54"
    for s in streakers:
        if (s.name == version):
            found_update_user = True

    # COMMENTED OUT FOR API UPDATE

#     if (not found_update_user):
#         await bot.get_channel(DAILY_CHANNEL_ID).send("""
# :vertical_traffic_light: Hey peeps! Streak Whip-Master Pete here. Here's a tiny update for everybody. Also, happy late Thanksgiving for those of you who celebrate it!

# - :bug: The streak highscores and all-time values resetting should be fixed now!
# - :sparkles: Improved the embeds. They should always post now, regardless of their length. They also no longer have that blank space where the title used to be.
# <@200340393596944384> Hah! Gotcha this time. :clap:
# """)
#         streakers.append(Streaker(1, version, streak=0))
#         backup()

    #-]

    try: requests.post(API["postURL"] + "?version={}".format(version))
    except Exception: print("\n*UNABLE TO SEND VERSION TO API*\n")

    print("\nDailies bot at the ready!")

    # await bot.change_presence(activity=discord.Game(name="Maintaining Streaks"))



@bot.event
async def on_message(message):
    await bot.process_commands(message)

    if (message.author.id == bot.user.id):
        return

    await processDay(message)

async def processDay(message, dayTest = False):
    global streakMilestones
    global lastDay

    streaker = False
    newStreaker = True
    streaksEnded = {}
    newDay = False
    newWeek = False
    newMonth = False
    amazingMilestone = False

    if (datetime.utcnow().day != lastDay or dayTest):
        newDay = True
        lastDay = datetime.utcnow().day
        # If yesterday's week is not the same as today's week...
        if ( (datetime.utcnow() - timedelta(1)).isocalendar()[1] != datetime.utcnow().isocalendar()[1] ): newWeek = True
        # If yesterday's motnh is not the same as today's month...
        if ( (datetime.utcnow() - timedelta(1)).month != datetime.utcnow().month ): newMonth = True
        await bot.get_channel(DAILY_CHANNEL_ID).send(":vertical_traffic_light: `A new streak day has started ( Time in UTC is: {0} )` <@&{1}>".format(datetime.utcnow(), STREAKER_NOTIFY_ID))

    if (message.channel.id == DAILY_CHANNEL_ID):
        streaker = True

    for s in streakers:
        if newDay:
            # if the time since this streaker's last post is more than one day
            if dayDifferenceNow(s.lastPostTime) > 1 and s.streak != 0:
                if (not s.casual):
                    # If this streaker is the rollover-causing author, prevent their streak from being lost
                    if (s.id == message.author.id and message.channel.id == DAILY_CHANNEL_ID): 
                        s.lastPostTime = datetime.utcnow() - timedelta(hours = 1)
                    
                    if (s.mercies == 0):
                        streaksEnded[s] = s.streak
                        s.lastPostTime = None
                    else:
                        streakMilestones[s] = 5
                        s.mercies -= 1

                        if (s.mercies < 2):
                            try:
                                user = await bot.fetch_user(s.id)
                                await user.send("Your streak is going to expire in **{0} {2}**. You have **{1} Mercy Days** left!\nMake sure to post something in #daily-challenge before then.".format(s.mercies + 1, s.mercies, "Days" if (s.mercies + 1 > 1) else "Day"))
                            except Exception as e:
                                print("\n{} COULDN'T BE MESSAGED! THEIR STREAK IS ABOUT TO EXPIRE!!!\n".format(s.name))

                    backup()

        if streaker and message.author.id == s.id:
            newStreaker = False

            if (dayDifferenceNow(s.lastPostTime) < 1):
                await message.add_reaction('💯')
                continue

            if not s.casual:
                s.lastPostTime = datetime.utcnow()
                s.streak += 1
                if (s.streak > s.streakRecord): s.streakRecord = s.streak
                s.streakAllTime += 1
                backup()

                # Assemble the list of streak milestones
                # Each milestone is given a value of 1 through 5
                # This groups the milestones together by length of time/mercy day/casual mode instead of streak total
                if (s.streak == 1):
                    streakMilestones[s] = 1
                if (s.streak % 30 == 0):
                    await message.add_reaction('🔥')
                    streakMilestones[s] = 4
                    s.mercies += 1; backup()
                elif (s.streak % 7 == 0):
                    await message.add_reaction('🔱')
                    streakMilestones[s] = 3
                        #await bot.get_channel(__CHANNEL__).send(bot.get_channel(DDISC_CHANNEL_ID), ":trident: `{0} has achieved a streak of {1} WEEK!`".format(info.display_name, s.streak // 7))
                        #await bot.get_channel(__CHANNEL__).send(bot.get_channel(DDISC_CHANNEL_ID), ":trident: `{0} has achieved a streak of {1} WEEKS!`".format(info.display_name, s.streak // 7))
                elif (s.streak % 3 == 0):
                    await message.add_reaction('⚜️')
                    streakMilestones[s] = 2
                    s.mercies += 1; backup()
                    #await bot.get_channel(__CHANNEL__).send(bot.get_channel(DDISC_CHANNEL_ID), ":fleur_de_lis: `{0} has achieved a streak of {1} DAYS!`".format(info.display_name, s.streak))
                else:
                    await message.add_reaction('❤️')
            else:
                # If we're working with a filthy casual...
                s.lastPostTime = datetime.utcnow()
                s.streak += 1
                s.weekStreak += 1
                if (s.streak > s.streakRecord): s.streakRecord = s.streak
                s.streakAllTime += 1
                backup()

                # Add reactions
                if s.weekStreak < 3:
                    await message.add_reaction('⚜️')
                elif s.weekStreak < 5:
                    await message.add_reaction('🔱')
                else:
                    await message.add_reaction('🔥')

        # Assemble the list of casual milestones
        # Each milestone is given a value of 11 through 13
        if (s.casual):
            if newWeek and not newMonth:
                if s.weekStreak < 3:
                    #print("Added milestone")
                    streakMilestones[s] = 11
                elif s.weekStreak < 5:
                    streakMilestones[s] = 12
                else:
                    streakMilestones[s] = 13
            elif newMonth:
                if s.streak < 10:
                    streakMilestones[s] = 11
                elif s.streak < 20:
                    streakMilestones[s] = 12
                else:
                    streakMilestones[s] = 13


    if newDay:
        embeds = []
        today = datetime.utcnow().date()
        end_of_day = datetime(today.year, today.month, today.day, tzinfo=tz.tzutc()) + timedelta(1)

        filthyCasuals = False

        # Sort milestones by length in descending order
        # Assemble the milestone string with fields of "{name} has a streak of {x}"
        if (len(streakMilestones) != 0):
            milestoneString = [""]
            casualMilestoneString = [""]
            mx = 0; cmx = 0 # set string list indexes
            streakMilesSorted = sorted(streakMilestones.items(), key=lambda x: x[1], reverse=True)
            for s in streakMilesSorted:
                # If the string is not small enough to fit in an embed
                if len(milestoneString[mx]) > 900:
                    mx += 1
                    milestoneString.append("")
                # If this milestone group is a challenger group
                if s[1] < 10:
                    if (s[1] == 5):
                        milestoneString[mx] += "\n:revolving_hearts: `{0}'s streak of` **{1} DAYS** `was saved by a Mercy Day!`".format(s[0].name, s[0].streak)
                    if (s[1] == 1):
                        milestoneString[mx] += "\n:beginner: `{} has started a new streak!`".format(s[0].name)
                    elif (s[1] == 4):
                        amazingMilestone = True
                        if (s[0].streak == 30):
                            milestoneString[mx] += "\n:fire: `{0} has achieved a streak of` **{1} MONTH!!**".format(s[0].name, s[0].streak // 30)
                        else:
                            milestoneString[mx] += "\n:fire: `{0} has achieved a streak of` **{1} MONTHS!!!!**".format(s[0].name, s[0].streak // 30)
                    elif (s[1] == 3):
                        if (s[0].streak == 7):
                            milestoneString[mx] += "\n:trident: `{0} has achieved a streak of` **{1} WEEK!**".format(s[0].name, s[0].streak // 7)
                        else:
                            milestoneString[mx] += "\n:trident: `{0} has achieved a streak of` **{1} WEEKS!**".format(s[0].name, s[0].streak // 7)
                    elif (s[1] == 2):
                        milestoneString[mx] += "\n:fleur_de_lis: `{0} has achieved a streak of` **{1} DAYS!**".format(s[0].name, s[0].streak)
                # If this milestone group is a casual group
                else:
                    filthyCasuals = True
                    # If the string is not small enough to fit in an embed
                    if len(casualMilestoneString[cmx]) > 900:
                        cmx += 1
                        casualMilestoneString.append("")
                    # If we are alerting for the casual 'month' category...
                    if (newMonth):
                        if (s[1] == 12):
                            casualMilestoneString[cmx] += "\n:trident: `{0} achieved a streak of` **{1} DAYS** `this month.`".format(s[0].name, s[0].streak)
                        elif (s[1] == 13):
                            casualMilestoneString[cmx] += "\n:fire: `{0} achieved a streak of` **{1} DAYS** `this month.`".format(s[0].name, s[0].streak)
                        elif (s[0].streak > 1):
                            casualMilestoneString[cmx] += "\n:fleur_de_lis: `{0} achieved a streak of` **{1} DAYS** `this month.`".format(s[0].name, s[0].streak)
                        elif (s[0].streak != 0):
                            casualMilestoneString[cmx] += "\n:fleur_de_lis: `{0} achieved a streak of` **{1} DAY** `this month.`".format(s[0].name, s[0].streak)
                        # Reset casual streaks
                        s[0].streak = 0
                        s[0].weekStreak = 0
                    # If we are alerting for the casual 'week' category...
                    else:
                        if (s[1] == 12):
                            casualMilestoneString[cmx] += "\n:trident: `{0} achieved a streak of` **{1} DAYS** `this week.`".format(s[0].name, s[0].weekStreak)
                        elif (s[1] == 13):
                            casualMilestoneString[cmx] += "\n:fire: `{0} achieved a streak of` **{1} DAYS** `this week.`".format(s[0].name, s[0].weekStreak)
                        elif (s[0].weekStreak > 1):
                            casualMilestoneString[cmx] += "\n:fleur_de_lis: `{0} achieved a streak of` **{1} DAYS** `this week.`".format(s[0].name, s[0].weekStreak)
                        elif (s[0].weekStreak != 0):
                            casualMilestoneString[cmx] += "\n:fleur_de_lis: `{0} achieved a streak of` **{1} DAY** `this week.`".format(s[0].name, s[0].weekStreak)
                        # Reset casual week streaks
                        s[0].weekStreak = 0

            if milestoneString[0] == "": milestoneString[0] = "none"
            if casualMilestoneString[0] == "": casualMilestoneString[0] = "none"
            for xx in range(len(milestoneString)):
                embeds.append(discord.Embed(color=getEmbedData()["color"]))
                embeds[xx].timestamp = end_of_day
                embeds[xx].add_field(name="Milestones", value=milestoneString[xx], inline=False)
            if filthyCasuals:
                for xxx in range(len(casualMilestoneString)):
                    embeds.append(discord.Embed(color=getEmbedData()["color"]))
                    embeds[xxx].timestamp = end_of_day
                    embeds[xxx].add_field(name="Casual Milestones", value=casualMilestoneString[xxx], inline=False)

        if (len(streaksEnded) != 0):
            alertString = ""
            streaksEndedSorted = sorted(streaksEnded.items(), key=lambda x: x[1], reverse=True)
            for s in streaksEndedSorted:
                if (s[0].streak > 1):
                    alertString += "\n:100: `{0} achieved a streak of` **{1} DAYS**".format(s[0].name, s[0].streak)
                else:
                    alertString += "\n:100: `{0} achieved a streak of` **{1} DAY**".format(s[0].name, s[0].streak)
                # Reset challenger streak
                s[0].streak = 0

            embeds[len(embeds)-1].add_field(name="Losses", value=alertString, inline=False)

        streakMilestones = {}
        
        if (not amazingMilestone):
            for e in embeds:
                await bot.get_channel(DAILY_CHANNEL_ID).send(embed=e)
        else:
            first = True
            for e in embeds:
                if first:
                    first = False
                    await bot.get_channel(DAILY_CHANNEL_ID).send(embed=e, file=discord.File('assets/amazingStreak.gif'))
                else:
                    await bot.get_channel(DAILY_CHANNEL_ID).send(embed=e)

    if (streaker and newStreaker):
        #print("streaker added")
        await message.add_reaction('❤️')

        info = await bot.fetch_user(message.author.id)
        if len(info.display_name.split()) > 1:
            name = info.display_name.title()
        else:
            name = info.display_name

        streakers.append(Streaker(message.author.id, name)); backup()
        await bot.get_channel(DDISC_CHANNEL_ID).send(":white_check_mark: `{} has started their first streak!`".format(name))

#
#
# USER COMMANDS
#
#

@bot.command(
    brief="Shorthand for !streaks"
)
async def s(ctx, extra = None):
    await streaks(ctx, extra)

@bot.command(
    brief="Shorthand for !streaks"
)
async def streak(ctx, extra = None):
    await streaks(ctx, extra)

@bot.command(
    brief="Show streak stats of the target user",
    description="""(target) : 'target' is optional. If left out, it defaults to you. This value can be entered as 'me', 'top', 'all', a user ID, or nothing. 'me' shows your streak stats. 'top' shows the top three streak groups and the users in them. 'all' shows all of the streak groups.

This command will show you the streak stats of the target user"""
)
async def streaks(ctx, extra = None):
    global lastLBMessage
    global lastCMDMessage
    has_alerted_wait = False

    today = datetime.utcnow().date()
    end_of_day = datetime(today.year, today.month, today.day, tzinfo=tz.tzutc()) + timedelta(1)

    embed = discord.Embed(title="STREAKS", description="", color=getEmbedData()["color"])
    embed.timestamp = end_of_day

    if (not extra or extra.lower() == "me"):
        streakUser = None
        for s in streakers:
            if (s.id == ctx.message.author.id):
                streakUser = s
                break

        user = await bot.fetch_user(ctx.message.author.id)
        embed.set_author(name = user.display_name, icon_url=user.avatar_url)

        if (streakUser):
            # If the user's name has not been added to the class (Done to make compatible with pre 6/3/2020 data backups)
            # Now used to update names in the list to adapt to user nickname changes
            #--if not s.name:
            if len(user.display_name.split()) > 1:
                s.name = user.display_name.title()
            else:
                s.name = user.display_name

            embed.title="Challenge Mode" if not streakUser.casual else "Casual Mode"
            if (not streakUser.casual):
                # Uhg, this mess
                if (streakUser.streak > 1): day1 = "DAYS"
                elif (streakUser.streak > 0): day1 = "DAY"
                else: day1 = ""
                embed.description="Current Streak: **{0} {4}**\nMercy Days: **{1}**\n\n`Highest Streak:` {2}\n`Streak Day Total:` {3}".format(streakUser.streak, streakUser.mercies, streakUser.streakRecord, streakUser.streakAllTime, day1)
            else:
                # UHGGGG
                if (streakUser.streak > 1): day1 = "DAYS"
                elif (streakUser.streak > 0): day1 = "DAY"
                else: day1 = ""
                if (streakUser.weekStreak > 1): day2 = "DAYS"
                elif (streakUser.weekStreak > 0): day2 = "DAY"
                else: day2 = ""
                embed.description="Current Month Streak: **{0} {4}**\nCurrent Week Streak: **{1} {5}**\n\n`Highest Streak: {2}\nStreak Day Total: {3}`".format(streakUser.streak, streakUser.weekStreak, streakUser.streakRecord, streakUser.streakAllTime, day1, day2)
        else:
            embed.title="Clothist Mode"
            embed.description="You do not have a streak. Start one in {}".format(bot.get_channel(DAILY_CHANNEL_ID).name)

    elif (extra.lower() == "all"):
        if (ctx.message.channel.id != SPAM_CHANNEL_ID):
            await ctx.send(":x: `-!streaks all- can only be used in {}`".format(bot.get_channel(SPAM_CHANNEL_ID).name))
            return
        else:
            embed.title="STREAKS"
            embed.description="---------------------------------------------------------------------"

            streakGroups = getStreakGroups()
            noStreakers = True
            for group in streakGroups:
                names = ""
                for s in streakers:
                    if (s.streak == group):
                        noStreakers = False

                        if not s.name: # If the user's name has not been added to the class (Done to make compatible with pre 6/3/2020 data backups)
                            if not has_alerted_wait:
                                has_alerted_wait = True
                                await ctx.send(":stopwatch: `Please allow me a minute to assemble the list for you`")
                            user = await bot.fetch_user(s.id)
                            if len(user.display_name.split()) > 1:
                                s.name = user.display_name.title()
                            else:
                                s.name = user.display_name

                        if (names == ""):
                            names += s.name + (" (Casual)" if s.casual else "")
                        else:
                            names += "\n" + s.name + (" (Casual)" if s.casual else "")

                if (group > 1):
                    embed.add_field(name="{} DAYS".format(group), value=names, inline=True)
                else:
                    embed.add_field(name="{} DAY".format(group), value=names, inline=True)

            if (noStreakers):
                embed.description = "No streaks available at this time"

    elif (extra.lower() == "top"):
        embed.title="TOP STREAKS"
        embed.description="---------------------------------------------------------------------"

        streakGroups = getStreakGroups()
        x=0
        noStreakers = True
        for group in streakGroups:
            x+=1
            names = ""
            for s in streakers:
                if (s.streak == group):
                    noStreakers = False
                    if not s.name: # If the user's name has not been added to the class (Done to make compatible with pre 6/3/2020 data backups)
                        user = await bot.fetch_user(s.id)
                        if len(user.display_name.split()) > 1:
                            s.name = user.display_name.title()
                        else:
                            s.name = user.display_name

                    if (names == ""):
                        names += s.name
                    else:
                        names += "\n" + s.name

            if (group > 1):
                embed.add_field(name="{} DAYS".format(group), value=names, inline=True)
            else:
                embed.add_field(name="{} DAY".format(group), value=names, inline=True)

            # Cut off after displaying the third streak group
            if (x == 3):
                break

    else:
        noStreakers = False

        extra = extra.replace('<', '')
        extra = extra.replace('!', '')
        extra = extra.replace('@', '')
        extra = extra.replace('>', '')

        try:
            extra = await bot.fetch_user(extra)
            embed.set_author(name = extra.display_name, icon_url=extra.avatar_url)

            streakUser = None
            for s in streakers:
                if (s.id == extra.id):
                    streakUser = s
                    break

            if (streakUser):
                embed.title="Challenge Mode" if not streakUser.casual else "Casual Mode"
                if (not streakUser.casual):
                    # Uhg, this mess
                    if (streakUser.streak > 1): day1 = "DAYS"
                    elif (streakUser.streak > 0): day1 = "DAY"
                    else: day1 = ""
                    embed.description="Current Streak: **{0} {4}**\nMercy Days: **{1}**\n\n`Highest Streak:` {2}\n`Streak Day Total:` {3}".format(streakUser.streak, streakUser.mercies, streakUser.streakRecord, streakUser.streakAllTime, day1)
                else:
                    # UHGGGG
                    if (streakUser.streak > 1): day1 = "DAYS"
                    elif (streakUser.streak > 0): day1 = "DAY"
                    else: day1 = ""
                    if (streakUser.weekStreak > 1): day2 = "DAYS"
                    elif (streakUser.weekStreak > 0): day2 = "DAY"
                    else: day2 = ""
                    embed.description="Current Month Streak: **{0} {4}**\nCurrent Week Streak: **{1} {5}**\n\n`Highest Streak:` {2}\n`Streak Day Total:` {3}".format(streakUser.streak, streakUser.weekStreak, streakUser.streakRecord, streakUser.streakAllTime, day1, day2)
            else:
                embed.title="Clothist Mode"
                embed.description="This user does not have a streak"
        except Exception as e:
            embed.title="ERROR"
            embed.description="I couldn't find {}'s info".format(extra)
            embed.set_author(name = "", icon_url="")

    # Delete previous command responses
    if (lastCMDMessage):
        try:
            await lastCMDMessage.delete()
        except:
            print("\nUnable to delete lastCMDMessage")

    if (lastLBMessage):
        try:
            await lastLBMessage.delete()
        except:
            print("\nUnable to delete lastLBMessage")

    lastCMDMessage = ctx.message
    lastLBMessage = await ctx.send(embed=embed)

@bot.command(brief="Toggle casual mode",
    description="""Casual mode allows you to be a streaker without the threat of losing your streak. Your streak will instead be based on a weekly/monthly total, resetting every month.

PLEASE NOTE: Toggling this mode will reset your streak and mercy days back to 0.""")
async def casual(ctx):
    global lastCMDMessage
    global lastLBMessage
    # Delete previous command responses
    if (lastCMDMessage):
        try:
            await lastCMDMessage.delete()
        except:
            print("\nUnable to delete lastCMDMessage")

    if (lastLBMessage):
        try:
            await lastLBMessage.delete()
        except:
            print("\nUnable to delete lastLBMessage")

    if (getStreaker(ctx.message.author.id)):
        s = getStreaker(ctx.message.author.id)
        if (not hasattr(s, 'casualWarn')): s.casualWarn = False
        if (not s.casualWarn):
            if not s.casual:
                lastLBMessage = await ctx.send(":warning: `Are you sure you want to enable casual mode? THIS WILL RESET YOUR STREAK AND MERCY DAYS`\n*Use* `!casual` *again to confirm.*")
            else:
                lastLBMessage = await ctx.send(":warning: `Are you sure you want to disable casual mode? THIS WILL RESET YOUR CASUAL STREAKS`\n*Use* `!casual` *again to confirm.*")
            s.casualWarn = True
            return
        
        s.casualWarn = False
        s.casual = not s.casual
        s.mercies = 0
        s.streak = 0
        s.weekStreak = 0
        backup()

        if (s.casual):
            msg = await ctx.send(":white_check_mark: `Casual Mode ENABLED. Your streak and Mercy Days have been reset`")
        else:
            msg = await ctx.send(":white_check_mark: `Casual Mode DISABLED. Remember, you start with 0 Mercy Days`")
        await deleteInteraction((msg, ctx.message))
    else:
        msg = await ctx.send(":question: `You can't use this yet. Become a streaker by posting something in {} first`".format(bot.get_channel(DAILY_CHANNEL_ID).name))
        await deleteInteraction((msg, ctx.message))

@bot.command(brief="Toggle streak alerts. This role gets pinged when a new streak day starts")
async def alert(ctx):
    notifyRole = discord.utils.get(ctx.message.guild.roles, id=STREAKER_NOTIFY_ID)
    isAlerter = False
    for role in ctx.message.author.roles:
        if int(role.id) == STREAKER_NOTIFY_ID:
            isAlerter = True
            break

    try:
        if isAlerter:
            await ctx.message.author.remove_roles(notifyRole)
            await ctx.send(":white_check_mark: `New streak day alerts DISABLED`")
        else:
            await ctx.message.author.add_roles(notifyRole)
            await ctx.send(":white_check_mark: `New streak day alerts ENABLED`")
    except:
        await ctx.send(":x: `I do not have the power to modify roles!!!`")

#
#
# ADMIN COMMANDS
#
#

@bot.command(hidden=True)
async def setmercies(ctx, user = None, mercies = None):
    if (not await isAdministrator(ctx)):
        return

    if (not isExpectedArgs( (str, int), (user, mercies) )):
        msg = await ctx.send(":x: `!setmercies requires 2 arguments: <user> <mercies>`")
        await deleteInteraction((msg, ctx.message))
        return

    if (getStreaker(user)):
        getStreaker(user).mercies = int(mercies)
    else:
        msg = await ctx.send(":x: `User '{}' not found`".format(user))
        await deleteInteraction((msg, ctx.message))
        return

    await ctx.send(":white_check_mark: `{0}'s mercies have been set to {1} {2}`".format(getStreaker(user).name, mercies, "DAYS" if int(mercies) > 1 else "DAY"))

@bot.command(hidden=True)
async def setstreak(ctx, user = None, newStreak = None, setToToday = None):
    if (not await isAdministrator(ctx)):
        return

    if (not isExpectedArgs( (str, int, (bool, str)), (user, newStreak, setToToday) )):
        msg = await ctx.send(":x: `!setstreak requires 2 arguments: <user> <streak>`")
        await deleteInteraction((msg, ctx.message))
        return

    if (getStreaker(user)):
        s = getStreaker(user)
        if (not setToToday):
            s.lastPostTime = datetime.utcnow() - timedelta(1)
        elif (setToToday.isdigit()):
            s.lastPostTime = (datetime.utcnow() - timedelta(int(setToToday)))
        else:
            s.lastPostTime = datetime.utcnow()
        s.streak = int(newStreak); backup()
    else:
        msg = await ctx.send(":x: `User '{}' not found`".format(user))
        await deleteInteraction((msg, ctx.message))
        return

    time_text = "DAYS"
    if (int(newStreak) == 1):
        time_text = "DAY"

    user = getStreaker(user)
    if (not setToToday):
        await ctx.send(":white_check_mark: `{0}'s streak has been set to {1} {2}. Their lastPostTime has been set to yesterday`".format(user.name, newStreak, time_text))
    else:
        if (not setToToday.isdigit()):
            await ctx.send(":white_check_mark: `{0}'s streak has been set to {1} {2}`".format(user.name, newStreak, time_text))
        else:
            await ctx.send(":white_check_mark: `{0}'s streak has been set to {1} {2}. Their lastPostTime has been set to {3} days ago`".format(user.name, newStreak, time_text, int(setToToday)))


@bot.command(hidden=True)
async def bumpstreak(ctx, user = None, setToToday = None):
    if (not await isAdministrator(ctx)):
        return

    if (not user):
        msg = await ctx.send(":x: `!bumpstreak requires 1 argument: <user>`")
        await deleteInteraction((msg, ctx.message))
        return

    if (getStreaker(user)):
        s = getStreaker(user)
        if (not setToToday):
            s.lastPostTime = datetime.utcnow() - timedelta(1)
        else:
            s.lastPostTime = datetime.utcnow()
        s.streak = s.streak + 1; backup()
    else:
        msg = await ctx.send(":x: `User '{}' not found`".format(user))
        await deleteInteraction((msg, ctx.message))
        return

    time_text = "DAYS"
    if (s.streak == 1):
        time_text = "DAY"

    user = getStreaker(user)
    if (not setToToday):
        await ctx.send(":white_check_mark: `{0}'s streak has been bumped to {1} {2}. Their lastPostTime has been set to yesterday`".format(user.name, s.streak, time_text))
    else:
        await ctx.send(":white_check_mark: `{0}'s streak has been bumped to {1} {2}`".format(user.name, s.streak, time_text))

@bot.command(hidden=True)
async def checkday(ctx):
    if (not await isAdministrator(ctx)):
        return

    await processDay(ctx.message, True)

#
#
# CHECKER FUNCTIONS
#
#

def isExpectedArgs(types, args, decypherString = True):
    if type(args) == tuple: args = list(args)
    if (decypherString):
        # Go through each arg and try to decypher a value from it
        for x in range(0, len(args)):
            if (not args[x] or type(args[x]) != str): continue
            if args[x].isdigit(): args[x] = int(args[x]); continue
            # Why no .isbool()? >:(
            if args[x].lower == "true": args[x] = True; continue
            if args[x].lower == "false": args[x] = False; continue

    index=-1
    for kind in types:
        index+=1
        # If arg can be multiple types...
        if (type(kind) == tuple):
            # if arg is not any of the accepted types
            if (not type(args[index] in kind)):
                return False
        # If arg can be only one type...
        else:
            # if arg is not its required type...
            if (kind != type(args[index])):
                return False
    return True

async def isAdministrator(ctx):
    mod_role = discord.utils.get(ctx.message.guild.roles, id=462342299171684364)

    if (ctx.message.author.id != 359521958519504926 and mod_role not in ctx.message.author.roles):
        msg = await ctx.send(":x: `You do not have permission to do this`")
        time.sleep(3)

        await msg.delete()
        await ctx.message.delete()
        return False
    return True

#
#
# UTILITY FUNCTIONS
#
#

def getStreaker(user):
    if (not user):
        return False

    if (type(user) != int):
        # If we were not given an ID, assume it is a mention and pull it from the string
        if (not user[0].isdigit()):
            user = user.replace('<', '')
            user = user.replace('!', '')
            user = user.replace('@', '')
            user = user.replace('>', '')
        
        # If we still don't have an ID, assume it is a nickname and return false
        if (not user[0].isdigit()):
            return False

    for s in streakers:
        if s.id == int(user):
            return s
    return False

def getStreakGroups():
    lastHighestStreak = 0
    streakGroups = []

    streakers.sort(reverse=True, key=operator.attrgetter('streak'))

    for s in streakers:
        if s.streak != lastHighestStreak and s.streak != 0:
            lastHighestStreak = s.streak
            streakGroups.append(s.streak)

    return streakGroups          

async def deleteInteraction(msgs):
    time.sleep(3)
    if (type(msgs) == tuple):
        for msg in msgs:
            await msg.delete()
    else:
        await msgs.delete()

def dayDifferenceNow(oldTime, newTime=0):
    # if (newTime != 0): # FOR TESTING PURPOSES
    #     dayNow = newTime.day
    #     dayOld = oldTime.day

    #     dif = dayNow - dayOld

    #     if (dif > -1):
    #         return dif
    #     else:
    #         # if the month has rolled over, get the amount of days between the old time, the end of the month, and now
    #         mLength = monthrange(oldTime.year, oldTime.month)[1]
    #         dif = (mLength - dayOld) + dayNow
    #         return dif

    if (oldTime != None):
        dayNow = datetime.utcnow().day
        dayOld = oldTime.day

        dif = dayNow - dayOld

        if (dif > -1):
            return dif
        else:
            # if the month has rolled over, get the amount of days between the old time, the end of the month, and now
            mLength = monthrange(oldTime.year, oldTime.month)[1]
            dif = (mLength - dayOld) + dayNow
            return dif
    else:
        #print("old time is 0 :(")
        return 1

def getEmbedData():
    try:
        data = requests.get(API["getURL"]).json()
    except Exception:
        print("\n*COULD NOT GET EMBED DATA. USING DEFAULTS...*\n")
        data = {
            "color": 0xD8410A,
        }
    return data



# Backup all of the data
def backup():
    #if (DEBUG): return

    serializable_data = {}

    try: os.rename("data/dailies_data.json", "data/dailies_data_OLD.json")
    except Exception: pass

    with open("data/dailies_data.json", "w") as dailies_data_file:
        for s in streakers:
            id = str(s.id) # compliance with new Discord.py integer IDs
            serializable_data[id] = {}

            # Make compatible with v1.2 to v1.5 streak user class
            if (not s.weekStreak): s.weekStreak = 0
            if (not s.streakRecord): s.streakRecord = s.streak
            if (not s.streakAllTime): s.streakAllTime = s.streak
            if (not s.mercies): s.mercies = 0
            if (not s.casual): s.casual = False

            serializable_data[id]["name"] = s.name
            serializable_data[id]["streak"] = s.streak
            serializable_data[id]["weekStreak"] = s.weekStreak
            serializable_data[id]["streakRecord"] = s.streakRecord
            serializable_data[id]["streakAllTime"] = s.streakAllTime
            serializable_data[id]["mercies"] = s.mercies
            serializable_data[id]["lastPostTime"] = str(s.lastPostTime)
            serializable_data[id]["casual"] = s.casual

        json.dump(serializable_data, dailies_data_file, indent=4, sort_keys=True)

# Load all of the backup data
def load_backup():
    #if (DEBUG): return
    json_data = {}

    try:
        with open("data/dailies_data.json", "r") as dailies_data_file:
            json_data = json.load(dailies_data_file)

            for id in json_data:
                #print("Loading id for {}".format(id))
                if (json_data[id]["lastPostTime"] != "None"):
                    time = datetime.strptime(json_data[id]["lastPostTime"], '%Y-%m-%d %H:%M:%S.%f')
                else:
                    time = None
                # Make compatible with v1.2 to v1.5 streak user class
                if (not "weekStreak" in json_data[id]): json_data[id]["weekStreak"] = 0
                if (not "streakRecord" in json_data[id]): json_data[id]["streakRecord"] = json_data[id]["streak"]
                if (not "streakAllTime" in json_data[id]): json_data[id]["streakAllTime"] = json_data[id]["streak"]
                if (not "mercies" in json_data[id]): json_data[id]["mercies"] = 0
                if (not "casual" in json_data[id]): json_data[id]["casual"] = False
                streakers.append( Streaker( id=int(id),
                                            name=json_data[id].get("name"),
                                            lpt=time,
                                            streak=json_data[id]["streak"],
                                            streakRecord=json_data[id]["streakRecord"],
                                            streakAllTime=json_data[id]["streakAllTime"],
                                            weekStreak=json_data[id]["weekStreak"],
                                            mercies=json_data[id]["mercies"],
                                            casual=json_data[id]["casual"]
                                            ))
    except Exception as e:
        print("\n**BACKUP MODIFIED OR CORRUPTED**\n")
        print(e)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return
    raise error


if __name__ == "__main__":
    # If we don't have any arguments to process
    if (len(sys.argv) == 1):
        main()
    else: # Load up the test IDs
        with open("data/testServer.json", "r") as testServer:
            jsonData = json.load(testServer)

            DAILY_CHANNEL_ID = jsonData["DCID"]
            DDISC_CHANNEL_ID = jsonData["DDCID"]
            SPAM_CHANNEL_ID  = jsonData["SCID"]
            STREAKER_NOTIFY_ID = jsonData["SRID"]
        main()
