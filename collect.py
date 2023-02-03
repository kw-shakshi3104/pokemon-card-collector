import requests

from bs4 import BeautifulSoup
from requests_html import HTMLSession, AsyncHTMLSession

import time
from tqdm import tqdm


# https://computer.masas-record-storage-container.com/2021/03/01/requestshtml/
# https://it-syoya-engineer.com/python-requests-html/
# https://qiita.com/uitspitss/items/f131ea79dffd58bc01ae

def collect_cards(url: str) -> list:
    # res = requests.get(url)
    # html = res.text

    session = AsyncHTMLSession()

    async def process():
        res = await session.get(url)
        await res.html.arender(timeout=0, wait=5, sleep=5)
        return res

    res = session.run(process)[0]
    html = res.html.html

    soup = BeautifulSoup(html, "html.parser")

    # 画像を取得
    elements = soup.find_all('img')
    # カード画像のみに絞る
    cards = [element for element in elements if '/assets/images/card_images/' in element.attrs['src']]

    return cards


if __name__ == "__main__":
    url = "https://www.pokemon-card.com/card-search/index.php?keyword=&se_ta=&regulation_sidebar_form=XY&pg=&illust=&sm_and_keyword=true"
    # res = requests.get(url)
    # html = res.text

    cards = []
    last_page_idx = 120
    for i in tqdm(range(1, last_page_idx + 1)):
        cards += collect_cards(url + f"&page={i}")
        time.sleep(10)
