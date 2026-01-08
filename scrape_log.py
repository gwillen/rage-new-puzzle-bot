#!/usr/bin/env -S uv run

import argparse
import datetime
import json
import os
import os.path
import time
import traceback

try:
  import winsound
except ImportError:
  winsound = None

import dotenv

from discord import post_discord, tag_npe
from fetch_puzzles import fetch_puzzles
from puzzle_types import Puzzle


dotenv.load_dotenv()


DISCORD_CHANNEL = os.getenv("DISCORD_CHANNEL", "new-puzzle-entry-private")
DISCORD_FORMAT = """\
**[{type} {action}]**
**Round:** {round}
**Name:** {name}{meta}{locked}
**URL:** `{url}`
**Desc:** {desc}\
"""


def load_puzzles() -> list[Puzzle]:
  if os.path.exists("puzzles.json"):
    with open("puzzles.json") as fp:
      return json.load(fp)
  else:
    return []


def save_puzzles(puzzles: list[Puzzle]):
  with open("puzzles.json", "w") as fp:
    json.dump(puzzles, fp, indent=2)


def poll(puzzles: list[Puzzle], beep=True, save=True, discord=False):
  prev_puzzles = {puzzle["url"]: puzzle for puzzle in puzzles}
  try:
    puzzles = fetch_puzzles()
  except Exception:
    traceback.print_exc()
    print("----------")
    if beep and winsound:
      winsound.Beep(220, 1000)
  else:
    any_found = False
    for puzzle in puzzles:
      state = puzzle.get("state")
      is_round = puzzle.get("isRound", False)
      is_meta = puzzle.get("isMeta", False)
      puzzle_type = "Round" if is_round else "Puzzle"
      meta = " (meta)" if is_meta else ""
      locked = state == "unlockable"
      if puzzle["url"] not in prev_puzzles:
        action = "Found"
      elif (
        state == "unlocked"
        and prev_puzzles[puzzle["url"]].get("state") == "unlockable"
      ):
        action = "Unlocked"
      else:
        action = None
      if action:
        any_found = True
        print(
          "{type} {action}\t{round}\t{name}{meta}{locked}\t{url}".format(
            type=puzzle_type,
            action=action,
            locked=" (locked)" if locked else "",
            meta=meta,
            **puzzle,
          )
        )
        if discord:
          msg = DISCORD_FORMAT.format(
            type=puzzle_type,
            action=action,
            locked=" :lock:" if locked else "",
            meta=meta,
            **puzzle,
          )
          post_discord(DISCORD_CHANNEL, tag_npe(msg, separator="\n"))
    if any_found:
      print("----------")
      if beep and winsound:
        winsound.Beep(440, 2000)
    else:
      print(f"[{datetime.datetime.now():%H:%M}] No Change")
    if save:
      save_puzzles(puzzles)
  return puzzles


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "-l",
    "--load",
    action="store_true",
    help="Load previously seen puzzles.json",
  )
  parser.add_argument(
    "-s",
    "--save",
    action="store_true",
    help="Save previously seen puzzles.json",
  )
  parser.add_argument(
    "-b",
    "--beep",
    action="store_true",
    help="Beep on new puzzles (only works on Windows)",
  )
  parser.add_argument(
    "-d", "--discord", action="store_true", help="Post to Discord"
  )
  parser.add_argument(
    "-p", "--poll", type=float, metavar="SECONDS", help="Poll in a loop"
  )
  args = parser.parse_args()

  if args.load:
    puzzles = load_puzzles()
  else:
    puzzles = []

  if args.poll:
    while True:
      puzzles = poll(
        puzzles, beep=args.beep, save=args.save, discord=args.discord
      )
      time.sleep(args.poll)
  else:
    poll(puzzles, beep=args.beep, save=args.save, discord=args.discord)
