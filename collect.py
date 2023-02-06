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

def collect_cards_html(html):
    soup = BeautifulSoup(html, "html.parser")
    # 画像を取得
    elements = soup.find_all('img')
    # カード画像のみに絞る
    cards = [element for element in elements if '/assets/images/card_images/' in element.attrs['src']]
    return cards


def collect_cards_async(url: str) -> (list, int):
    session = AsyncHTMLSession()

    async def process():
        res = await session.get(url)
        await res.html.arender(timeout=0, wait=5, sleep=5)
        return res

    res = session.run(process)[0]
    html = res.html.html

    cards = collect_cards_html(html)
    return cards, res.status_code


def collect_cards(url: str) -> (list, int):
    session = HTMLSession()

    res = session.get(url)
    res.html.render(sleep=10)

    cards = collect_cards_html(res.html)
    return cards, res.status_code


# DataFrameに整形する
def to_dataframe(df: list) -> pd.DataFrame:
    base_image_url = "https://www.pokemon-card.com"
    df = pd.DataFrame([{
        "pokemon-name": card.attrs["alt"],
        "image_url": base_image_url + card.attrs["src"],
    } for card in df])

    # 画像名とカテゴリ(?)のURLから取得
    path_urls = list(map(lambda x: Path(x), df["image_url"]))
    df["image_name"] = list(map(lambda x: x.name, path_urls))
    df["expansion"] = list(map(lambda x: x.parts[-2], path_urls))

    return df


def download_image(url: str, output_filepath: Path):
    res = requests.get(url)
    img = res.content

    with output_filepath.open("wb") as f:
        f.write(img)


if __name__ == "__main__":
    url = "https://www.pokemon-card.com/card-search/index.php?keyword=&se_ta=&regulation_sidebar_form=XY&pg=&illust=&sm_and_keyword=true"

    # カード画像のURLのリストを取得
    cards = pd.DataFrame()
    last_page_idx = 120
    for i in tqdm(range(1, last_page_idx + 1)):
        # スクレイピング
        temp, status = collect_cards_async(url + f"&page={i}")
        # temp, status = collect_cards(url + f"&page={i}")

        if status == requests.codes.ok and len(temp) > 0:
            # DataFrameへ整形
            card_ = to_dataframe(temp)

            # 画像を取得
            for img_url, img_name in tqdm(zip(card_["image_url"], card_["image_name"])):
                output_filepath = Path(f"outputs/{img_name}")
                download_image(img_url, output_filepath)
                time.sleep(1)

            # リストに追加
            cards = pd.concat([cards, card_], ignore_index=True)

        time.sleep(10)

    # 画像のリストを出力
    cards.to_csv("./outputs/pokemon_card_list.csv", index=False, encoding='utf-8_sig')
