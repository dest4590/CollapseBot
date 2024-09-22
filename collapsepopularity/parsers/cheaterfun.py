import requests
from bs4 import BeautifulSoup


class CheaterFun:
    url = 'https://cheater.fun/cheat-loaders/8966-collapseloader-minecraft-cheat-loader.html'

    def parse(self, proxy: str) -> str:
        attempts = 0
        while True:
            if attempts >= 3:
                return 'Failed to parse'
            
            try:
                response = requests.get(
                    self.url,
                    timeout=2,
                    proxies={'http': proxy, 'https': proxy}
                )
                response.raise_for_status()

                bs = BeautifulSoup(response.content, 'lxml')
            except requests.exceptions.RequestException:
                attempts += 1
                continue

            if bs:
                t = bs.find('div', class_='fs-8 text-muted').text.replace('\n', '').replace(' ', '')
                return t[t.find('Views')+6:]