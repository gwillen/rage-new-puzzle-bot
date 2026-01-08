# Rage New Puzzle Bot

This is a script that scrapes the Mystery Hunt site, tracks when new puzzles
unlock, and posts the details of them to `#new-puzzle-entry-private` so they
can be entered in Herring. We keep the actual entry manual instead of automating
it because sometimes the scraped details can different from the way we choose
to group them in Herring, or it may not have all the info. But this bot has
two major advantages which are that you don't have to wait for someone to
notice that there are new puzzles (especially when they unlock at times other
than from solves) and that even once you do know there are new puzzles, it
makes it much easier to enter them in Herring when the name and URL can be
copied directly from Discord instead of searching for it on the hunt site.

## Setting up the script on your machine

1. Clone this repo
2. Make sure you have Python installed
3. Create a virtualenv and install dependencies. The preferred way to do this is
   install [uv](https://docs.astral.sh/uv/getting-started/installation/) and
   then run `uv init`. But if you prefer to do it manually you can run
   ```
   python venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
4. Copy `.env.example` to `.env`
5. Find the role ID of the New Puzzle Entry (Active) role and set it as the
   value of `NEW_PUZZLE_ENTRY_ACTIVE` in `.env`. To do this, go to
   `#new-puzzle-entry-private` and send a message that says
   `\@New Puzzle Entry (Active)`. When you post it, it will be replaced with
   something like`<@&1455048957498626083>`. Copy whatever that string of numbers
   is (without the punctuation around it) and put that in the `.env` file. To
   test that it worked you can run `./discord.py -t "This is a test"`. If
   Herring is running and pointed at the right Discord server with HerringBot
   in it, and the `HERRING_URL`, `DISCORD_CHANNEL`, and
   `NEW_PUZZLE_ENTRY_ACTIVE` env vars are set correctly, then a message
   `@New Puzzle Entry (Active) This is a test` will show up in the Discord
   channel.
6. Once the hunt starts you will need to set `HUNT_URL` to the base URL of the
   hunt site. Also, in some years you have needed to change this mid-hunt
   (usually after a fake-out intro round with a different URL than the rest of
   the hunt)
7. Log in to the hunt site with our team login. Then look in your browser's
   dev tools to find the session cookie that the site uses. Set
   `MH_SESSION_COOKIE_KEY` to the name of the cookie (usually `sessionid`) and
   `MH_SESSION_COOKIE` to its value.

## Updating the script for the current hunt site

`scrape_log.py` is the main entry point, `puzzle_types.py` contains some shared
type definitions, and `discord.py` contains some helper functions for posting
to Discord and an entry point for testing posting to Discord. You should rarely
need to edit any of these.

The file you will need to edit per-year is `fetch_puzzles.py`. Either edit this
file, or make a copy of it named `fetch_puzzles_<year>.py` and update the import
in `scrape_log.py` to `from fetch_puzzles_<year> import fetch_puzzles`.

Either way, this file is expected to export a single function with the
signature `fetch_puzzles() -> list[Puzzle]`. Use whatever method you like to
accomplish this. In 2023 and 2024 this was easy because there was an API
endpoint that just returned the list of puzzles in a machine-readable form
(JSON). The keys in the `Puzzle` type were adjusted specifically to match the
keys in the JSON that this API returned. In 2021 I used regular expressions to
scrape the activity log page. In 2022 I used regular expressions to scrape the
All Puzzles page. In 2025, I used a regular expression to extract a JSON blob
from a script tag on the All Puzzles page and then parsed and transformed their
JSON into the format I actually wanted. At some point I added
[Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/), an HTML
parsing library, as a dependency and experimented with using it to scrape the
HTML, but never actually used it. In 2025 there was a WebSocket that you could
connect to and subscribe to events and wait for events that would give you
JSON updates when new puzzles were found or unlocked, etc. I experimented with
a version that would connect to this WebSocket, but never ended up using it.
The advantage of that was that it would avoid the need to poll, but since all
of `scrape_log.py` as already designed around polling, it would have required
a pretty big redesign to support.

I can't tell you what to do this year, but I can give some guidance. If there is
an API that returns JSON, it should be preferred. Check if `/api/puzzle_list`
returns anything. Next level of preference is to scrape the All Puzzles page,
either with something like Beautiful Soup or some regexes. View source on the
All Puzzles page and see if there's a comment there telling you to use an API
(that's how we found it the first time, but in 2024 it wasn't documented yet
still worked at the same path). If not, feel free to see if there's some JSON
you can scrape like 2025 or otherwise just the structure of the page. If the
All Puzzles page doesn't have everything you need, maybe the Activity Log will
work.

The `Puzzle` object that you have to return a list of (order is unimportant)
is a dictionary with the following keys:

- `url`: The fully-qualified URL to the puzzle page. Usually you get this by
  screen-scraping the `href` of the `<a>` tags on the All Puzzles page. Usually
  these are relative paths so you have to prepend `HUNT_URL`.
- `round`: The name of the round. This can really be any string you want. It
  just tells the new puzzle entry person what round page to add the puzzle in
  but this script doesn't really track rounds, just puzzles.
- `name`: The canonnical name/title of the puzzle.
- `desc`: (Optional) A description of the puzzle. This was added in 2025. Each
  puzzle came with a brief description so you could make an informed choice
  about which of the available puzzles to unlock. In a normal year without a
  team unlocking structure this will probably just be omitted. (Feel free to
  remove it from `DISCORD_FORMAT` in `scrape_log.py` if you don't have
  descriptions, but not doing this won't hurt).
- `state`: (Optional) If present, either `"unlockable"` or `"unlocked"`. This
  was added in 2025 to track whether puzzles were just found but still locked
  and unable to be worked on, or unlocked by our team and solvable. In most
  years without a team unlocking structure you can omit this field and all
  puzzles will be assumed to be unlocked as soon as they are discovered.
- `isRound`: (Optional) Most years the All Puzzles page didn't have links to
  to the rounds so we couldn't track rounds. When a puzzle was discovered with a
  `round` that hadn't been seen before, in order to create a new round in
  Herring, the new puzzle entry person would have to manually find the URL of
  the round itself. In 2025, the structure of the data we were scraping was
  such that we could parse out round metadata and round unlocks as well. If
  you do have the ability to detect round URLs, you can add round entries with
  this field set to `True`. Both `name` and `round` are still required but
  should probably be set to the same thing. For regular puzzles or in years
  where we can't detect round URLs, this field can just be omitted and will
  default to `False`.
- `isMeta`: If you can detect that a puzzle is a meta, do not put `(meta)` in
  the name or anything, instead set this field to `True`. Then `(meta)` will
  automatically be append to the name when displayed on Discord. If omitted this
  defaults to `False`. If you can't detect when a puzzle is a meta, it is
  important to let the new puzzle entry people that they may need to manually
  check whether a puzzle is a meta before they enter it.

## Running `scrape_log.py`

`scrape_log.py` is the main entrypoint for this repo. What it does is calls
`fetch_puzzles` to scrape the hunt site and return the list of all available
puzzles. It stores this list of puzzles and metadata. It will then sleep a
configurable amount of time before polling the `fetch_puzzles` again. It
diffs the new list of puzzles from the old list of puzzles and prints any new
puzzles to the console and posts them to Discord. A puzzle is considered new
only if its `url` was not present in the previous list of puzzles or in 2025 if
the `state` changed from `unlockable` to `unlocked`. Changes in order or other
changes in metadata (like name) are not expected and not detected.

To avoid forgetting puzzles that it previously saw if you end up stopping it and
starting again, it caches the list of puzzles it has seen to a file called
`puzzles.json`. It loads this file when the script first starts. After that it
maintains the list of previous puzzles in memory. However it saves the list to
this file after each poll.

Some of the above details are configurable with command-line parameters though.
For instance, you can choose to run it where it only fetches once and then
exits instead of sleeping and polling. You can also disabling the loading or
saving of the cache.

The default command I would use to run this script is:

```
./scrape_log.py -lsdp 30
```

This will load the cache, save the cache after each poll, post new puzzles to
Discord, and poll every 30 seconds.

If you're on Windows, adding `-b` will make your computer beep every time new
puzzles are detected. This isn't that useful anymore since Discord can notify
you when something is posted. However, it makes a lower tone beep any time an
exception is caught that might be working checking.

You will probably occasionally get errors if the hunt site is slammed and
doesn't respond to every request. The script should catch these and continue
to poll, but keep an eye on it. It will print tracebacks when this happens.

If you lose your `puzzles.json` cache file, running this command would
re-notify about every puzzle so far. You probably don't want that. Instead,
if you run `./scrape_log.py -s` it will fetch puzzles once and save a new cache.
It will think all puzzles are new, but it won't post to Discord.

If you're doing some local testing with some new puzzles without `-d` to post
to Discord but you want to post after you're sure it does the right thing,
also omit `-s` so that it won't save the cache. When you run the script again
with `-d` again (and presumably `-s`) it will see those same puzzles as still
new and post about them.

If you don't have uv installed, running the script as `./scrape_log.py` will not
work because its shebang assumes running the script as `uv run scrape_log.py`.
Instead, manually activate your virtualenv with `source .venv/bin/activate` and
either change the shebang to `#!/usr/bin/env python` or run it as
`python scrape_log.py`.
