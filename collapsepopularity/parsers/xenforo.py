import requests
from bs4 import BeautifulSoup


class Xenforo:
    def __init__(self, url: str, thread_id: int):
        self.url = url
        self.thread_id = thread_id

    def parse(self) -> str:
        attempts = 0
        while True:
            if attempts >= 3:
                return 'Failed to parse'
            
            try:
                response = requests.get(self.url, timeout=2)
                response.raise_for_status()
                bs = BeautifulSoup(response.content, 'lxml')
            except requests.exceptions.RequestException:
                attempts += 1
                continue

            if bs:
                return bs.find('a', href=f"/threads/{str(self.thread_id)}/").parent.parent.parent.find(class_='structItem-cell--meta').findAll('dd')[-1].text
