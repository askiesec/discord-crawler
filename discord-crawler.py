import discord
import os
import json
import time
import re
import asyncio
import nltk
import argparse
from nltk.sentiment import SentimentIntensityAnalyzer
from discord.ext import commands
from colorama import Fore, Back, Style, init
from dhooks import Webhook, Embed

def ensure_config_exists(config_path="config.json"):
    if not os.path.isfile(config_path):
        default_config = {
            "token": "",
            "channelids": [],
            "hook": "",
            "keywords": []
        }
        with open(config_path, "w") as config_file:
            json.dump(default_config, config_file, indent=4)
        MessagePrinter.print_info(f"Default config created at {config_path}")

init(autoreset=True)
nltk.download("punkt_tab", quiet=True)

DISCORD_SERVER_REGEX = r"(https?://)?(www\.)?(discord\.(gg|com/invite)/[a-zA-Z0-9]+)"

class MessagePrinter:

    @staticmethod
    def print_success(message):
        print(f"{Fore.GREEN}{Style.BRIGHT}✅ {message}")

    @staticmethod
    def print_info(message):
        print(f"{Fore.MAGENTA}{Style.BRIGHT}💡 {message}")

    @staticmethod
    def print_warning(message):
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ {message}")

    @staticmethod
    def print_error(message):
        print(f"{Fore.RED}{Style.BRIGHT}✘ {message}")

ensure_config_exists()

parser = argparse.ArgumentParser(description="Discord Selfbot Crawler")
parser.add_argument("--config", type=str, default="config.json", help="Path to configuration file")
parser.add_argument("--channelid", required=True, type=str, default="config.json", help="Single channel ID to monitor")
args = parser.parse_args()


def banner():
    print(
        f"""

    {Fore.BLUE}{Style.BRIGHT}
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⡤⠤⠴⠂⠀⠀⠀⠀⠉⠉⠉⠉⠉⠉⠉⠙⠓⠒⠤⢤⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠒⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠙⠶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠖⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠳⡄⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⠴⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢦⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡼⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢳⡀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⢀⡀⣠⠴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡄⠀⠀⠀
    ⠀⠀⠀⢰⣾⣭⠉⠙⠲⣄⡀⢠⣾⣷⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⣇⠀⠀
    ⠀⠀⠀⠸⣿⣿⣼⡇⡶⡆⢹⡿⠿⠀⠉⠟⠧⣔⢦⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢧⠀
    ⠀⠀⠀⠀⢸⠻⣿⡭⣷⡷⠟⠁⠀⠀⠀⠀⠀⠩⣆⠀⠀⠀⠀⠀⠀⠀⠿⣦⠀⠀⠀⠀⠀⠀⠀⡏⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣯
    ⠀⠀⠀⣤⠇⠈⢸⠏⠉⠀⠀⠀⠀⠀⠐⠀⠀⠀⠈⠙⠳⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡨
    ⠀⠀⠀⡟⠀⠀⠀⠀⠀⠀⠀⠀⣒⠆⠀⠀⠀⠀⠀⣦⡀⠙⡆⠀⠀⠀⠀⢠⣴⠀⡀⠀⠀⢠⣭⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢪
    ⡀⠀⠀⣷⡀⠀⠀⠀⠀⠀⠀⢠⣿⡇⡀⠀⠀⠀⠀⠘⣇⠀⢸⠀⠀⢀⣐⡿⢫⠞⣷⡀⠀⣾⠓⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼
    ⢿⢻⣍⠻⣿⡀⠀⠀⠀⠀⠀⠀⠙⢏⠀⠀⠀⠀⠀⠀⠈⢧⡘⢳⣶⠟⠉⠀⠀⣰⣟⣧⣴⣿⣆⢻⡀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣹⠿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣶⣾⣿
    ⠀⠓⠿⣶⣾⣄⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠢⠀⠈⢷⣾⡇⠀⠀⠀⣰⡯⣷⣫⣿⠃⠉⢹⣇⠀⠀⠀⠀⢀⣶⡶⠞⠉⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⣰⣤⣶⣶⣾⠃⠀⠀⣿
    ⠀⠀⠀⠈⠙⠻⣧⠈⠳⣤⣄⡀⠀⢠⡀⠀⠀⠀⠀⢳⡀⠀⢸⣿⡧⠀⢀⣰⡯⠿⠟⠛⠁⢀⣠⠞⠉⣃⠴⣿⡷⠟⠛⢿⣲⣤⠉⢿⣦⡀⠀⠀⠀⠀⠀⠾⠿⠋⠀⣹⡿⠀⠀⠀⣿
    ⠀⠀⠀⠀⠀⠀⠈⠙⠺⢿⣷⠟⠁⠀⣿⣦⡀⠀⠀⣶⠘⢀⣾⡏⡄⢠⡨⡟⢀⣠⣤⠖⠚⠉⣠⣶⣯⣽⣿⡁⠀⢀⣤⡤⠞⠙⠓⠛⠛⢿⣦⡦⣤⣼⠏⠁⠀⠀⢀⣿⡧⠀⠀⠲⣿
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠈⠈⠑⠲⣌⡉⠻⢦⣤⣹⣤⡞⠙⣇⣿⣾⣿⢯⡿⠟⢁⡤⢀⣼⣯⠿⡿⢅⣼⠧⠒⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠓⠢⠤⠤⠶⠟⣿⢃⠀⠉⣶⢿
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠓⠾⠿⠿⠛⠀⠀⠘⠙⠻⢿⣏⣠⣾⣏⡴⠋⠹⠷⠖⠓⠚⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⡃⠰⢀⣸⡼⠈
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡠⠞⠁⣂⣠⣄⡿⠃⠠
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⢤⡞⠋⢦⡤⠔⣿⣸⠟⠁⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⠴⠶⠛⢫⢻⢨⡇⢹⣷⣾⣯⠷⠟⠁⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⡴⠒⠋⢅⣈⣧⣴⡶⠼⠿⠟⠛⠛⠛⠉⠁⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠚⠉⣹⡤⠶⠊⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡔⠉⣠⠴⠊⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠟⡦⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣮⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀

        {Style.RESET_ALL}

    """
    )

class DiscordCrawler(commands.Cog,):
    def __init__(self, bot, config, channelid=None):
        self.bot = bot
        self.token = config["token"]
        self.channelids = config.get("channelids", [])
        if channelid:
            self.channelids.append(channelid)
        self.hook = Webhook(config["hook"])
        self.keywords = config["keywords"]

    @commands.Cog.listener()
    async def on_ready(self):
        banner()
        MessagePrinter.print_success("Discord Crawler initialize successfully")
        MessagePrinter.print_success(f"Keywords loaded: {self.keywords}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id in self.channelids:
            date_format = "%a, %d %b %Y %I:%M %p"
            profurl = f"https://discordapp.com/users/{message.author.id}"
            guild_name = message.guild.name
            embed = Embed(color=0x546E7A, timestamp="now")
            embed.set_author(
                name=f"{message.author}", icon_url=f"{message.author.avatar.url}"
            )
            embed.set_thumbnail(url=f"{message.author.avatar.url}")
            embed.add_field(name="Server Name", value=guild_name, inline=False)
            embed.add_field(name="User ID", value=message.author.id)
            embed.add_field(name="", value=f"[Profile Link]({profurl})")
            embed.add_field(
                name="Created At",
                value=f"{message.author.created_at.date()}",
                inline=True,
            )
            embed.add_field(
                name="*Joined*", value=message.author.joined_at.strftime(date_format)
            )
            embed.add_field(
                name="*Message*", value=f"`{message.content}`", inline=False
            )
            embed.add_field(
                name="*Channel*", value=f"#{message.channel.name}", inline=False
            )

            self.hook.send(embed=embed)

            with open("log.csv", "a", encoding="utf-8") as f:
                f.write(
                    f"[-] {time.strftime(date_format)} {message.author}: {message.content}\n"
                )

        server_links = re.findall(DISCORD_SERVER_REGEX, message.content)
        if server_links:
            formatted_links = [f"{link[2]}" for link in server_links]
            MessagePrinter.print_warning(
                f"Discord server link detected {formatted_links}"
            )
            
        try:
            tokens = nltk.word_tokenize(message.content)
            for word in tokens:
                if word.lower() in self.keywords:
                        MessagePrinter.print_warning(f"Keyword detected in channel {self.channelid}: from {message.author}: {word}")
                break
        except Exception as e:
            MessagePrinter.print_error(f"Error in tokenization or keyword checking: {e}")


class WebhookCrawler:
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        try:
            if args.config:
             with open("config.json") as f:
                 config = json.load(f)
                 self.token = config["token"]
                 self.channel_ids = config["channelids"]
                 if args.channelid:
                     self.channelids.append(args.channelid)
                 self.webhook_url = config["hook"]
                 self.keywords = config["keywords"]

            if not self.token:
                 raise ValueError("Token is missing in the config.json")
            if not self.webhook_url:
                 raise ValueError("Webhook URL is missing in the config.json")
            MessagePrinter.print_success("Config loaded successfully")
        except FileNotFoundError:
            MessagePrinter.print_error("config.json file not found")
            raise
        except json.JSONDecodeError:
            MessagePrinter.print_error("Error decoding config.json")
            raise
        except KeyError as e:
            MessagePrinter.print_error(f"Missing key in config.json: {e}")
        except Exception as e:
            MessagePrinter.print_error(f"Unexpected error loading config.json: {e}")
            raise

    def run(self):
        asyncio.ensure_future(self._run_bot())

    async def _run_bot(self):
        try:
            await self.bot.start(self.token)
        except Exception as e:
            MessagePrinter.print_error(f"Error starting Discord Crawler: {e}")


async def main():
    try:
        with open("config.json") as f:
            config = json.load(f)
    except Exception as e:
        MessagePrinter.print_error(f"Failed to load config.json: {e}")
        return

    bot = commands.Bot(command_prefix="", self_bot=True)
    await bot.add_cog(DiscordCrawler(bot, config))
    await bot.start(config["token"])


if __name__ == "__main__":
    try:
        asyncio.run(main())

    except RuntimeError as e:
        MessagePrinter.print_error(f"Event loop error: {e}")
    except ValueError as ve:
        MessagePrinter.print_error(f"Configuration error: {ve}")
