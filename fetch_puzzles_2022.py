import html
import os
import re

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

ROUND_BASE_URLS = {
  "The Investigation": "https://www.starrats.org",
}


def fetch_puzzles() -> list[Puzzle]:
  assert HUNT_URL is not None
  assert SESSION_COOKIE_VALUE is not None
  cookies = {SESSION_COOKIE_KEY: SESSION_COOKIE_VALUE}
  res = requests.get(HUNT_URL + "/puzzles/", cookies=cookies, timeout=TIMEOUT)
  puzzles: dict[str, Puzzle] = {}
  for round in re.findall(
    r'<h2>\s*<a href="(/round/[^"]*)">(.*?)</a>\s*</h2>\s*'
    r"<table>(.*?)</table>",
    res.text,
    re.S,
  ):
    round_name = html.unescape(round[1])
    round_base = ROUND_BASE_URLS.get(round_name, HUNT_URL)
    round_url = round_base + round[0]
    for line in re.findall(
      r'<td><a href="(/puzzle/[^"]*)">(.*?)</a></td>', round[2]
    ):
      url = round_base + line[0]
      puzzles[url] = {
        "url": url,
        "round": round_name,
        "name": html.unescape(line[1]),
      }
    # determine meta
    res = requests.get(round_url, cookies=cookies, timeout=TIMEOUT)
    match = re.search(
      r'<div class="round-table-container">\s*<table>\s*'
      r"<tr><th>Puzzle</th><th>Answer</th></tr>(.*?)</table>",
      res.text,
      re.S,
    )
    assert match
    for line in re.findall(
      r'<tr>\s*<td>\s*<a href="(/puzzle/[^"]*)"( class="meta")?[^>]*>\s*'
      r"(.*?)\s*</a>\s*</td>",
      match[1],
      re.S,
    ):
      url = round_base + line[0]
      is_meta = bool(line[1])
      if url in puzzles:
        puzzles[url]["isMeta"] = is_meta
      else:
        print(f'{round_name} "{line[2]}" ({url}) not on all puzzles')
  return list(puzzles.values())
