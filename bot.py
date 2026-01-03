import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import time

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =======================
# DUYURU SİSTEMİ
# =======================
duyuru_mesajlari = {}

# =======================
# INVITE SİSTEMİ
# =======================
invite_cache = {}
invite_counts = {}
join_times = {}

FAKE_INVITE_TIME = 600

INVITE_ROLE_REWARDS = {
    1: 1457051963005866060,
    2: 1457051963005866059,
}

# =======================
@bot.event
async def on_ready():
    await bot.tree.sync()

    for guild in bot.guilds:
        invites = await guild.invites()
        invite_cache[guild.id] = {i.code: i.uses for i in invites}

    print(f"{bot.user} aktif!")

# =======================
# SLASH /duyuru
# =======================
@bot.tree.command(name="duyuru", description="Reactionlı DM duyurusu")
async def duyuru(interaction: discord.Interaction, dm_mesaji: str):

    perms = interaction.channel.permissions_for(interaction.guild.me)
    if not perms.send_messages or not perms.add_reactions:
        await interaction.response.send_message(
            "❌ Bu kanalda mesaj göndərmək və ya reaksiya əlavə etmək üçün icazəm yoxdur.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title="Click 🍼",
        description="Press ✅ in order to get DM",
        color=discord.Color.blue()
    )

    await interaction.response.send_message("✅ Duyuru gönderildi.", ephemeral=True)

    msg = await interaction.channel.send(embed=embed)

    try:
        await msg.add_reaction("✅")
    except discord.Forbidden:
        await interaction.followup.send(
            "⚠️ Mesaj gönderildi ama reaksiya ekleyemedim (yetkim yok).",
            ephemeral=True
        )
        return

    duyuru_mesajlari[msg.id] = dm_mesaji

# =======================
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot:
        return

    if reaction.message.id not in duyuru_mesajlari:
        return

    if str(reaction.emoji) != "✅":
        return

    try:
        await user.send(duyuru_mesajlari[reaction.message.id])
    except discord.Forbidden:
        pass

# =======================
# ÜYE KATILDI
# =======================
@bot.event
async def on_member_join(member):
    guild = member.guild
    before = invite_cache.get(guild.id, {})
    after = await guild.invites()

    used_invite = None
    for inv in after:
        if inv.code in before and inv.uses > before[inv.code]:
            used_invite = inv
            break

    invite_cache[guild.id] = {i.code: i.uses for i in after}

    if not used_invite:
        return

    inviter = used_invite.inviter
    invite_counts[inviter.id] = invite_counts.get(inviter.id, 0) + 1
    join_times[member.id] = (inviter.id, time.time())

    count = invite_counts[inviter.id]

    for req, role_id in INVITE_ROLE_REWARDS.items():
        if count == req:
            role = guild.get_role(role_id)
            if role:
                await inviter.add_roles(role)

# =======================
# FAKE INVITE KORUMA
# =======================
@bot.event
async def on_member_remove(member):
    if member.id not in join_times:
        return

    inviter_id, join_time = join_times.pop(member.id)

    if time.time() - join_time <= FAKE_INVITE_TIME:
        invite_counts[inviter_id] = max(0, invite_counts.get(inviter_id, 1) - 1)

# =======================
# /inv
# =======================
@bot.tree.command(name="inv", description="Invite sayını gösterir")
async def inv(interaction: discord.Interaction):
    count = invite_counts.get(interaction.user.id, 0)
    await interaction.response.send_message(f"📨 **Invite Sayın:** `{count}`", ephemeral=True)

# =======================
# /invite
# =======================
@bot.tree.command(name="invite", description="Invite rol şartlarını gösterir")
async def invite(interaction: discord.Interaction):
    text = ""
    for req, role_id in INVITE_ROLE_REWARDS.items():
        role = interaction.guild.get_role(role_id)
        if role:
            text += f"🔹 `{req}` invite → **{role.name}**\n"

    await interaction.response.send_message(
        embed=discord.Embed(
            title="🎯 Invite Rol Şartları",
            description=text or "Rol ayarlanmamış.",
            color=discord.Color.green()
        ),
        ephemeral=True
    )

bot.run(os.getenv("DISCORD_TOKEN"))
