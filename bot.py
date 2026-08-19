import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HISTORY_FILE = "published.json"


# ==========================================
# HISTÓRICO
# ==========================================

def load_history():

    if not os.path.exists(HISTORY_FILE):
        return {"published": []}

    try:

        with open(
            HISTORY_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if "published" not in data:
                data["published"] = []

            return data

    except Exception as error:

        print(
            "Erro ao ler histórico:",
            error
        )

        return {"published": []}


def save_history(history):

    with open(
        HISTORY_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            history,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Histórico salvo: "
        f"{len(history['published'])} notícias"
    )


# ==========================================
# IMAGEM DO RSS
# ==========================================

def get_image_from_rss(item):

    # media_content

    if "media_content" in item:

        for media in item.media_content:

            image = media.get("url")

            if image:
                return image


    # media_thumbnail

    if "media_thumbnail" in item:

        for media in item.media_thumbnail:

            image = media.get("url")

            if image:
                return image


    # enclosures

    if "enclosures" in item:

        for enclosure in item.enclosures:

            image = enclosure.get("url")

            if image:
                return image


    return None


# ==========================================
# IMAGEM DA PÁGINA
# ==========================================

def get_image_from_page(link):

    try:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/131.0 Safari/537.36"
            )
        }


        response = requests.get(
            link,
            headers=headers,
            timeout=15
        )


        if not response.ok:

            print(
                "Não foi possível abrir a página:",
                response.status_code
            )

            return None


        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )


        # ==================================
        # OG IMAGE
        # ==================================

        og_image = soup.find(
            "meta",
            property="og:image"
        )


        if og_image:

            image = og_image.get(
                "content"
            )

            if image:
                return image


        # ==================================
        # TWITTER IMAGE
        # ==================================

        twitter_image = soup.find(
            "meta",
            attrs={
                "name": "twitter:image"
            }
        )


        if twitter_image:

            image = twitter_image.get(
                "content"
            )

            if image:
                return image


        # ==================================
        # PRIMEIRA IMAGEM
        # ==================================

        image_tag = soup.find("img")


        if image_tag:

            image = (
                image_tag.get("src")
                or image_tag.get("data-src")
            )


            if image:
                return image


    except Exception as error:

        print(
            "Erro ao procurar imagem:",
            error
        )


    return None


# ==========================================
# BUSCAR IMAGEM
# ==========================================

def get_news_image(item, link):

    print(
        "Procurando imagem no RSS..."
    )


    image = get_image_from_rss(item)


    if image:

        print(
            "Imagem encontrada no RSS:"
        )

        print(image)

        return image


    print(
        "Imagem não encontrada no RSS."
    )

    print(
        "Procurando imagem na página..."
    )


    image = get_image_from_page(link)


    if image:

        print(
            "Imagem encontrada na página:"
        )

        print(image)

        return image


    print(
        "Nenhuma imagem encontrada."
    )

    return None


# ==========================================
# TELEGRAM
# ==========================================

def send_telegram(
    title,
    link,
    image
):

    caption = (
        f"📰 <b>{title}</b>\n\n"
        f"🔗 <b>Leia a matéria:</b>\n"
        f"{link}"
    )


    # ======================================
    # COM IMAGEM
    # ======================================

    if image:

        url = (
            "https://api.telegram.org/"
            f"bot{TELEGRAM_TOKEN}/sendPhoto"
        )


        data = {

            "chat_id": TELEGRAM_CHAT_ID,

            "photo": image,

            "caption": caption,

            "parse_mode": "HTML"
        }


    # ======================================
    # SEM IMAGEM
    # ======================================

    else:

        url = (
            "https://api.telegram.org/"
            f"bot{TELEGRAM_TOKEN}/sendMessage"
        )


        data = {

            "chat_id": TELEGRAM_CHAT_ID,

            "text": caption,

            "parse_mode": "HTML",

            "disable_web_page_preview": False
        }


    try:

        response = requests.post(
            url,
            data=data,
            timeout=30
        )


        if response.ok:

            print(
                "Mensagem enviada com sucesso."
            )

            return True


        print(
            "Erro Telegram:"
        )

        print(
            response.text
        )

        return False


    except Exception as error:

        print(
            "Erro ao enviar para Telegram:",
            error
        )

        return False


# ==========================================
# BOT PRINCIPAL
# ==========================================

def main():

    print(
        "===================================="
    )

    print(
        "BOT RSS - INICIANDO"
    )

    print(
        "===================================="
    )


    # ======================================
    # CONFIGURAÇÕES
    # ======================================

    if not TELEGRAM_TOKEN:

        raise Exception(
            "TELEGRAM_TOKEN não configurado."
        )


    if not TELEGRAM_CHAT_ID:

        raise Exception(
            "TELEGRAM_CHAT_ID não configurado."
        )


    # ======================================
    # HISTÓRICO
    # ======================================

    history = load_history()

    published = history["published"]


    print(
        f"Notícias no histórico: "
        f"{len(published)}"
    )


    # ======================================
    # RSS
    # ======================================

    try:

        with open(
            "feeds.json",
            "r",
            encoding="utf-8"
        ) as file:

            feeds = json.load(file)

    except Exception as error:

        raise Exception(
            f"Erro ao abrir feeds.json: {error}"
        )


    print(
        f"Fontes RSS encontradas: "
        f"{len(feeds)}"
    )


    total_new = 0


    # ======================================
    # FONTES
    # ======================================

    for feed in feeds:

        source_name = feed.get(
            "name",
            "Fonte sem nome"
        )

        source_url = feed.get(
            "url",
            ""
        )


        print()
        print(
            "===================================="
        )

        print(
            f"Fonte: {source_name}"
        )

        print(
            f"RSS: {source_url}"
        )

        print(
            "===================================="
        )


        if not source_url:

            print(
                "RSS sem URL. Ignorando."
            )

            continue


        # ==================================
        # CONSULTAR RSS
        # ==================================

        try:

            rss = feedparser.parse(
                source_url
            )

        except Exception as error:

            print(
                "Erro ao consultar RSS:",
                error
            )

            continue


        if not rss.entries:

            print(
                "Nenhuma notícia encontrada."
            )

            continue


        print(
            f"Notícias encontradas no RSS: "
            f"{len(rss.entries)}"
        )


        # ==================================
        # ÚLTIMAS 20 NOTÍCIAS
        # ==================================

        entries = rss.entries[:20]


        for item in entries:

            title = item.get(
                "title",
                "Sem título"
            ).strip()


            link = item.get(
                "link",
                ""
            ).strip()


            if not link:

                continue


            # ==================================
            # DUPLICAÇÃO
            # ==================================

            if link in published:

                print(
                    f"IGNORADA - já publicada: "
                    f"{title}"
                )

                continue


            print()
            print(
                "NOVA NOTÍCIA:"
            )

            print(
                f"Título: {title}"
            )

            print(
                f"Link: {link}"
            )


            # ==================================
            # BUSCAR IMAGEM
            # ==================================

            image = get_news_image(
                item,
                link
            )


            # ==================================
            # ENVIAR TELEGRAM
            # ==================================

            success = send_telegram(
                title,
                link,
                image
            )


            # ==================================
            # SALVAR HISTÓRICO
            # ==================================

            if success:

                published.append(
                    link
                )

                total_new += 1


                save_history(
                    history
                )


                print(
                    "SALVA NO HISTÓRICO!"
                )

            else:

                print(
                    "Notícia não salva no histórico."
                )


    # ======================================
    # RESULTADO
    # ======================================

    print()

    print(
        "===================================="
    )

    print(
        "RESULTADO DA EXECUÇÃO"
    )

    print(
        "===================================="
    )

    print(
        f"Novas publicações: {total_new}"
    )

    print(
        f"Total no histórico: {len(published)}"
    )

    print(
        "===================================="
    )


# ==========================================
# INICIAR
# ==========================================

if __name__ == "__main__":

    main()
