import requests
from bs4 import BeautifulSoup


class Ezyhack:
    url = "https://ezyhack.ru/load/chity_dlja_minecraft/collapseloader-loader-chitov-na-minecraft/4-1-0-3244"

    def parse(self, proxy: str) -> str:
        attempts = 0
        while True:
            if attempts >= 3:
                return "Failed to parse"

            try:
                response = requests.get(
                    self.url, timeout=2, proxies={"http": proxy, "https": proxy}
                )
                response.raise_for_status()

                bs = BeautifulSoup(response.content, "lxml")
            except requests.exceptions.RequestException as e:
                attempts += 1
                continue

            if bs:
                return bs.find("span", class_="fa-eye").parent.text.replace(" ", "")
