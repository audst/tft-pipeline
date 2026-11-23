from dataclasses import dataclass

PLATFORM_TO_REGION = {"na1": "americas", "br1": "americas", "euw1": "europe", "kr": "asia"}


@dataclass(frozen=True)
class Config:
    api_key: str
    platform: str = "na1"