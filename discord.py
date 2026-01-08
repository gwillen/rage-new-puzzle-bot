#!/usr/bin/env -S uv run

import argparse
import os

import dotenv
import requests


dotenv.load_dotenv()


HERRING_URL = os.getenv("HERRING_URL", "https://www.rage.solutions")
NEW_PUZZLE_ENTRY_ACTIVE = os.getenv("NEW_PUZZLE_ENTRY_ACTIVE")


def post_discord(channel: str, text: str):
  res = requests.post(
    HERRING_URL + "/post_discord/", data={"channel": channel, "text": text}
  )
  res.raise_for_status()
  return res


def tag_npe(msg: str, separator=" "):
  if NEW_PUZZLE_ENTRY_ACTIVE:
    msg = f"<@&{NEW_PUZZLE_ENTRY_ACTIVE}>{separator}{msg}"
  return msg


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "-t", "--tag-npe", action="store_true", help="Tag New Puzzle Entry (Active)"
  )
  parser.add_argument(
    "-s", "--separator", default=" ", help="Separator between tag and message"
  )
  parser.add_argument(
    "-n",
    "--newline",
    action="store_const",
    dest="separator",
    const="\n",
    help="Use newline as a separator",
  )
  default_channel = os.getenv("DISCORD_CHANNEL", "new-puzzle-entry-private")
  parser.add_argument("-c", "--channel", default=default_channel)
  parser.add_argument("message")
  args = parser.parse_args()

  msg = args.message
  if args.tag_npe:
    msg = tag_npe(msg, separator=args.separator)

  post_discord(args.channel, msg)
