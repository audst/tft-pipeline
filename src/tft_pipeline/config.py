import os
from dataclasses import dataclass

from dotenv import load_dotenv

PLATFORM_TO_REGION = {"na1": "americas", "br1": "americas", "euw1": "europe", "kr": "asia"}

@dataclass(frozen=True)
class Config:
    api_key: str
    platform: str = "na1"

    @property
    def region(self) -> str:
        return PLATFORM_TO_REGION[self.platform]

    @property
    def platform_url(self) -> str:
        return f"https://{self.platform}.api.riotgames.com"

    @property
    def region_url(self) -> str:
        return f"https://{self.region}.api.riotgames.com"

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        key = (os.environ.get("RIOT_API_KEY") or "").strip()
        if not key:
            raise SystemExit("RIOT_API_KEY is missing or empty. Set it in .env.")
        return cls(api_key=key, platform=os.environ.get("RIOT_PLATFORM", "na1"))