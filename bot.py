import discord, requests, json, datetime
from discord.ext import commands, tasks
from discord.app_commands import Choice

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())
client.remove_command("help")
tree = client.tree

dbdir = "db.json"
cachedir = "cache.json"

statusChannelID = 1131960460636327976

activityTypeToTitle = {"0": "Offline", "1": "Online", "2": "In Game", "3": "In Studio"}
activityTypeToColour = {"0": 0x969696, "1": 0x00A2FF, "2": 0x02B757, "3": 0xF68802}

@tasks.loop(seconds=10)
async def dothing():
    with open(dbdir, "r+") as f:
        deta = json.load(f)
        users = deta["stalks"]
        mentions = deta["mentions"]
    if not users:
        return
    req = requests.post("https://presence.roblox.com/v1/presence/users", json={"userIds": users}).json()
    with open(cachedir, "r+") as f:
        data = json.load(f)
        data2 = data.copy()
        for user in req["userPresences"]:
            data2[str(user["userId"])] = {"type": user["userPresenceType"]}
            if user["placeId"]:
                data2[str(user["userId"])]["placeId"] = user["placeId"]
        f.seek(0)
        f.truncate()
        json.dump(data2, f, indent=4)
    statusChannel = client.get_channel(statusChannelID)
    for user in data:
        if data[user]["type"] != data2[user]["type"]:
            username = requests.get(f"https://users.roblox.com/v1/users/{user}").json()["name"]
            thumbnail = requests.get(f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={user}&size=720x720&format=Png&isCircular=false").json()["data"][0]["imageUrl"]
            await statusChannel.send(" ".join(mentions), embed=discord.Embed(title=activityTypeToTitle[str(data2[user]["type"])], colour=activityTypeToColour[str(data2[user]["type"])], description=f"[{username}](https://www.roblox.com/users/{user}/profile) is now **{activityTypeToTitle[str(data2[user]['type'])]}**" if "placeId" not in data[user] else f"[{username}](https://www.roblox.com/users/{user}/profile) is now [**{activityTypeToTitle[str(data2[user]['type'])]}**](https://www.roblox.com/games/{data[user]['placeId']})", timestamp=datetime.datetime.now()).set_thumbnail(url=thumbnail))

@client.event
async def on_ready():
    print(f"Profile Automation now online with {round(client.latency * 1000)}ms ping.")
    with open(cachedir, "r+") as f:
        data = json.load(f)
        data = {}
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)
    dothing.start()

mention = discord.app_commands.Group(name="mention", description="Modify who is mentioned upon a status change")
tree.add_command(mention)

@mention.command(name="add", description="Add a mentionable")
async def mentionadd(interaction : discord.Interaction, mentionable : discord.Member or discord.Role):
    with open(dbdir, "r+") as f:
        data = json.load(f)
        data["mentions"].append(mentionable.mention)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)
    await interaction.response.send_message(embed=discord.Embed(title="Success", colour=0x00FF00, description="Mentionable successfully added to the mention database"))

@mention.command(name="remove", description="Remove a mentionable")
async def mentionremove(interaction : discord.Interaction, mentionable : discord.Member or discord.Role):
    with open(dbdir, "r+") as f:
        data = json.load(f)
        data["mentions"].remove(mentionable.mention)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)
    await interaction.response.send_message(embed=discord.Embed(title="Success", colour=0x00FF00, description="Mentionable successfully removed from the mention database"))

stalk = discord.app_commands.Group(name="stalk", description="Modify who is stalked")
tree.add_command(stalk)

def checkUser(usertype, user):
    if usertype == "1":
        #name
        req = requests.post(f"https://users.roblox.com/v1/usernames/users", data={"usernames": [user]}).json()
        print(req)
        if not req["data"]:
            return None
        return req[0]["id"]
    else:
        #id
        req = requests.get(f"https://users.roblox.com/v1/users/{user}").json()
        if "errors" in req:
            return None
        return req["id"]

@stalk.command(name="add", description="Add a stalked user")
@discord.app_commands.choices(usertype=[
    Choice(name="name", value="1"),
    Choice(name="id", value="2")
])
async def stalkadd(interaction : discord.Interaction, usertype : Choice[str], user : str):
    user = checkUser(usertype.value, user)
    if not user:
        await interaction.response.send_message(embed=discord.Embed(title="Error", colour=0xFF0000, description="Uh-oh, it doesn't look like a user with that name/id exists"))
        return
    with open(dbdir, "r+") as f:
        data = json.load(f)
        data["stalks"].append(user)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)
    await interaction.response.send_message(embed=discord.Embed(title="Success", colour=0x00FF00, description="User has successfully been added to the tracking database"))

@stalk.command(name="remove", description="Remove a stalked user")
@discord.app_commands.choices(usertype=[
    Choice(name="name", value="1"),
    Choice(name="id", value="2")
])
async def stalkremove(interaction : discord.Interaction, usertype : Choice[str], user : str):
    user = checkUser(usertype.value, user)
    if not user:
        await interaction.response.send_message(embed=discord.Embed(title="Error", colour=0xFF0000, description="Uh-oh, it doesn't look like a user with that name/id exists"))
        return
    with open(dbdir, "r+") as f:
        data = json.load(f)
        data["stalks"].remove(user)
        f.seek(0)
        f.truncate()
        json.dump(data, f, indent=4)
    await interaction.response.send_message(embed=discord.Embed(title="Success", colour=0x00FF00, description="User has successfully been removed from the tracking database"))

@client.command()
@commands.check(lambda ctx : ctx.author.id == 301014178703998987)
async def connect(ctx):
    await tree.sync()

client.run("MTIxODI5Mjc2ODMwMTEyNTczMg.G8K51a.0E-ErS_qYMV-tzmw5SqTkEZMv59ZMrpEd-Y5mY")