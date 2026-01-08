import typing


class Puzzle(typing.TypedDict):
  url: str
  round: str
  name: str
  desc: typing.NotRequired[str]
  state: typing.NotRequired[typing.Literal["unlockable", "unlocked"]]
  isRound: typing.NotRequired[bool]
  isMeta: typing.NotRequired[bool]
