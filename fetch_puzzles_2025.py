import json
import os
import re
import urllib.parse

import dotenv
import requests

from puzzle_types import Puzzle


dotenv.load_dotenv()


TIMEOUT = 5
HUNT_URL = os.getenv("HUNT_URL")
SESSION_COOKIE_KEY = os.getenv("MH_SESSION_COOKIE_KEY", "sessionid")
SESSION_COOKIE_VALUE = os.getenv("MH_SESSION_COOKIE")

assert HUNT_URL is not None, "Must set hunt URL with HUNT_URL .env var"
assert SESSION_COOKIE_VALUE is not None, (
  "Must set session cookie with MH_SESSION_COOKIE .env var"
)


def fetch_puzzles() -> list[Puzzle]:
  assert HUNT_URL is not None
  assert SESSION_COOKIE_VALUE is not None
  cookies = {SESSION_COOKIE_KEY: SESSION_COOKIE_VALUE}
  res = requests.get(
    HUNT_URL + "/all_puzzles", cookies=cookies, timeout=TIMEOUT
  )
  res.raise_for_status()
  match = re.search(
    r"<script>window\.initialAllPuzzlesState = (.*?)</script>", res.text
  )
  assert match
  data = json.loads(match[1])
  rounds = data["rounds"]
  rounds.append(
    {
      "title": "Stray Leads",
      "slug": "stray_leads",
      "puzzles": data["stray"],
    }
  )
  puzzles: list[Puzzle] = []
  for round in rounds:
    url = urllib.parse.urljoin(HUNT_URL, f"rounds/{round['slug']}")
    puzzles.append(
      {
        "url": url,
        "round": round["title"],
        "name": f"{round['title']} (Round)",
        "isRound": True,
        "desc": "",
      }
    )
    for puzzle in round["puzzles"]:
      url = urllib.parse.urljoin(HUNT_URL, f"/puzzles/{puzzle['slug']}")
      puzzles.append(
        {
          "url": url,
          "round": round["title"],
          "name": puzzle["title"],
          "desc": puzzle.get("desc", ""),
          "state": puzzle["state"],
          "isRound": False,
          "isMeta": puzzle.get("is_meta", False),
        }
      )
  return puzzles
