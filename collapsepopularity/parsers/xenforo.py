import requests
from bs4 import BeautifulSoup


class Xenforo:
    def __init__(self, url: str, thread_id: int):
        self.url = url
        self.thread_id = thread_id

    def parse(self) -> str:
        while True:
            try:
                response = requests.get(self.url, timeout=2)
                response.raise_for_status()
                bs = BeautifulSoup(response.content, 'lxml')
            except requests.exceptions.RequestException:
                continue

            if bs:
                return bs.find('a', href=f"/threads/{str(self.thread_id)}/").parent.parent.parent.find(class_='structItem-cell--meta').findAll('dd')[-1].text
