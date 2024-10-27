import os
import re
import lxml.html as html
from lxml import etree
import requests
import pandas as pd
import telebot


def parse_jonnesway_search(word):
    url = "https://www.jonnesway.ru/default/catalog/product-search-by-string/query/"+word
    lxml_text = etree.HTML(requests.get(url).text)
    products = lxml_text.xpath("/html/body/div[1]/div[2]/div[2]/div[3]/table/*")

    products_links = []
    for i in products:
        i = etree.HTML(html.tostring(i, encoding="unicode"))
        i = html.tostring(i.xpath("/html/body/tr/td/h4/a")[0], encoding="unicode")
        i = i.split("href=\"")[1].split("\">")[0]
        products_links.append("https://www.jonnesway.ru"+i)

    parced_data = {} # "link":{data}
    for i in products_links:
        parced_data[i] = parse_jonnesway_product(i)

    return parced_data


def parse_jonnesway_product(url):
    if "jonnesway.ru/product" not in url:
        print("Ошибка в URL!")
        return None

    lxml_text = etree.HTML(requests.get(url).text)

    product_name = lxml_text.xpath("//h1[@class='product-header']")[0].text
    product_price = re.sub("[ ]", "", lxml_text.xpath("/html/body/div[1]/div[2]/div[2]/div[3]/table/tr/td[2]/div")[0].text).replace("р.", "")

    specs_table_raw = lxml_text.xpath('//*[@id="description"]/div[1]/div/table/*')
    specs_table = {}
    for i in specs_table_raw:
        specs_table[i[0].text] = i[1].text

    try:
        return {"name": product_name,
                "price": float(product_price),
                "specs": specs_table}
    except:
        return {"name": product_name,
                "price": product_price,
                "specs": specs_table}


def form_excel(search_r, file_name="output"):
    df = pd.DataFrame({"name":[], "link":[], "price":[], "code":[], "number":[], "item":[], "streak":[], "country":[]})
    for i in parse_jonnesway_search(search_r).items():

        try: code = i[1]["specs"]["Код товара"]
        except: code = None
        try: number = i[1]["specs"]["Количество в упаковке"]
        except: number = None
        try: item = i[1]["specs"]["Артикул"]
        except: item = None
        try: streak = i[1]["specs"]["Штрих-код"]
        except: streak = None
        try: country = i[1]["specs"]["Страна производитель"]
        except: country = None

        df2 = pd.DataFrame({"name": i[1]["name"],
                        "link": [i[0]],
                        "price": [i[1]["price"]],
                        "code": [code],
                        "number": [number],
                        "item": [item],
                        "streak": [streak],
                        "country": [country]})
        print(df2)
        df = pd.concat([df, df2], ignore_index=True)
        df.reset_index()

    df.to_excel(file_name + ".xlsx")
    df.to_csv(file_name+".csv")


bot = telebot.TeleBot("8041611539:AAFW_9pGUvUQ-HvBA-vEcNrwJAFEsijmy_g")


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, "Напишите, что Вы хотите найти")


@bot.message_handler(content_types=["text"])
def answer(message):
    form_excel(message.text, str(message.chat.id))
    bot.send_document(message.chat.id,open(str(message.chat.id)+".xlsx", "rb"))
    bot.send_document(message.chat.id, open(str(message.chat.id) + ".csv", "rb"))
    os.remove(str(message.chat.id)+".xlsx")


bot.infinity_polling()

