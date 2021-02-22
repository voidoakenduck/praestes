import discord, asyncio
from discord.ext import commands
import asyncio as aio


class Moderation(commands.Cog):
    def __init__(self, client):
        self.client = client

    async def cog_check(self, ctx):
        return not ctx.guild is None

    @commands.command(aliases=["cr"])
    @commands.has_permissions(manage_roles=True)
    async def createrole(self, ctx, name:str="new role", clr:discord.Colour=0, pos:int=1, perms:int=0):
        """ create a role, with optional colour, position, and permissions code """
        _perms = discord.Permissions()
        _perms.value = perms

        clr = clr or discord.Colour(0)
        role = await ctx.guild.create_role(name=name, colour=clr, permissions=_perms)
        pos = pos if pos > 1 else 1
        await role.edit(position=pos)

        embed = discord.Embed(title="Created role", colour=clr)
        embed.description = f"```yaml\n---\nname: {name}\nid: {role.id}\ncolour: {str(clr)}\nposition: {pos}\npermissions: {_perms.value}\n---\n```"
        await ctx.send(embed=embed)

    @commands.command(aliases=["del"])
    @commands.has_permissions(manage_messages=True)
    @commands.cooldown(1, 5, type=commands.BucketType.user)
    async def delete(self, ctx, count:int=1):
        """ delete up to 100 messages in context channel """
        if 0 >= count or count > 100:
            raise Exception("you cannot delete more than 100 messages, or less than 1.")

        chnl = ctx.channel
        await chnl.delete_messages([ctx.message])
        messages = await chnl.history(limit=count).flatten()
        await chnl.delete_messages(messages)

        msg = await ctx.send(f"Message{'s' * int(bool(int(count) - 1))} deleted.")
        await asyncio.sleep(1.2)
        await chnl.delete_messages([msg])

    @commands.command()
    @commands.has_permissions(manage_nicknames=True)
    async def setnick(self, ctx, member:discord.Member, *, new_nick:str):
        """ change given user's nickname """
        old_nick = member.display_name
        await member.edit(nick=new_nick)
        embed = discord.Embed(description=f"Updated **{member.name}**'s nickname.")
        await ctx.reply(embed=embed)

    @commands.command(aliases=["ar"])
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, member:discord.Member, *, role:discord.Role):
        """ add role to a given member, by mention or ID """
        await member.add_roles(role)
        await ctx.reply(f"Added role `{role}` to **{member}**.")

    @commands.command(aliases=["rr"])
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member:discord.Member, *, role:discord.Role):
           """ remove role from a given member, by mention or ID """
           await member.remove_roles(role)
           await ctx.reply(f"Removed role `{role}` from **{member}**")

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member:discord.Member, *, reason:str="no given reason"):
        """ kick a given user, by ID or mention """
        if self.member_remove_fail(ctx, user): return

        await member.kick()
        embed = discord.Embed(title=f"Reason for kick:", description=reason)
        embed.set_author(name=f"{member} kicked", icon_url=member.avatar_url)
        embed.set_footer(text=f"Kicked by {ctx.author}\nUID: {member.id}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user:discord.User, *, reason:str="no given reason"):
        """ ban a given user, whether in guild or not, by ID or mention """
        if member:=discord.utils.get(ctx.guild.members, id=user.id):
            if self.member_remove_fail(ctx, member): return

        await ctx.guild.ban(discord.Object(id=user.id))
        embed = discord.Embed(title=f"Reason for ban:", description=reason)
        embed.set_author(name=f"{user} banned", icon_url=user.avatar_url)
        embed.set_footer(text=f"Banned by {ctx.author}\nUID: {user.id}")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def massban(self, ctx, *, users):
        """ remove all members passed in, space delimited. may take a few """ \
        """moments to complete due to rate limiting. """
        converter = commands.UserConverter()
        message = "```diff\n"
        confirmation = await ctx.reply("Attempting mass ban...")
        embed = discord.Embed(title="Mass ban")

        for user in users.split():
            try:
                user = await converter.convert(ctx, user)
            except commands.UserNotFound:
                message += f"- User {user} not found.\n"
                continue

            if user:=discord.utils.get(ctx.guild.members, id=user.id):
                if user.id == ctx.bot.user.id or user.id == ctx.guild.owner.id \
                        or self.member_remove_fail(ctx, user):
                    print(ctx.author.id, user.id)
                    message += f"- Could not ban {user}.\n"
                    continue

            message += f"+ Banned {user}.\n"
            embed.description = message + "\n```"
            await confirmation.edit(content="", embed=embed)
            await ctx.guild.ban(discord.Object(id=user.id))
            await aio.sleep(0.5)

        embed.description = message + "\n+ Completed.\n```"
        await confirmation.edit(content="", embed=embed)

    def member_remove_fail(self, ctx, member:discord.Member):
        first = ctx.author.top_role <= member.top_role
        second = ctx.author.id == member.id
        print(first, second)
        return ctx.author.top_role <= member.top_role or ctx.author.id == member.id


def setup(client):
    client.add_cog(Moderation(client))

