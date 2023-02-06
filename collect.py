import requests
import pandas as pd

from bs4 import BeautifulSoup
from requests_html import HTMLSession, AsyncHTMLSession

import time
from tqdm import tqdm

from pathlib import Path


# https://computer.masas-record-storage-container.com/2021/03/01/requestshtml/
# https://it-syoya-engineer.com/python-requests-html/
# https://qiita.com/uitspitss/items/f131ea79dffd58bc01ae

def collect_cards_async(url: str) -> list:
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


def download_image(url: str, output_filepath: Path):
    res = requests.get(url)
    img = res.content

    with output_filepath.open("wb") as f:
        f.write(img)


if __name__ == "__main__":
    url = "https://www.pokemon-card.com/card-search/index.php?keyword=&se_ta=&regulation_sidebar_form=XY&pg=&illust=&sm_and_keyword=true"

    # カード画像のURLのリストを取得
    cards = []
    last_page_idx = 120
    for i in tqdm(range(1, last_page_idx + 1)):
        cards = cards + collect_cards_async(url + f"&page={i}")
        time.sleep(20)

    # DataFrameに整形する
    base_image_url = "https://www.pokemon-card.com"
    cards = pd.DataFrame([{
        "pokemon-name": card.attrs["alt"],
        "image_url": base_image_url + card.attrs["src"],
    } for card in cards])

    # 画像名とカテゴリ(?)のURLから取得
    path_urls = list(map(lambda x: Path(x), cards["image_url"]))
    cards["image_name"] = list(map(lambda x: x.name, path_urls))
    cards["expansion"] = list(map(lambda x: x.parts[-2], path_urls))

    # 画像を取得
    for img_url, img_name in tqdm(zip(cards["image_url"], cards["image_name"])):
        output_filepath = Path(f"./images/{img_name}")
        download_image(img_url, output_filepath)
        time.sleep(1)
