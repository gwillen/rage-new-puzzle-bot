import html
import os
import re

# from bs4 import BeautifulSoup
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
  res = requests.get(HUNT_URL + "/log", cookies=cookies, timeout=TIMEOUT)
  return [
    {
      "url": HUNT_URL + line[0],
      "round": html.unescape(line[3]),
      "name": html.unescape(line[2]),
      "isMeta": bool(line[1]),
    }
    for line in re.findall(
      r'<a href="(/puzzle/[^/]+/)">Found (meta)?puzzle &quot;(.*?)&quot;'
      r" \((.*?)\)</a>",
      res.text,
    )
    if line[2] != "Infinite Corridor"
  ]
