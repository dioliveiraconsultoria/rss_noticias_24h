import os
import json
import requests
import feedparser
from bs4 import BeautifulSoup


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HISTORY_FILE = "published.json"


# ==========================================
# CARREGAR HISTÓRICO
# ==========================================

def load_history():

    if not os.path.exists(HISTORY_FILE):

        return {
            "published": []
        }

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

        return {
            "published": []
        }


# ==========================================
# SALVAR HISTÓRICO
# ==========================================

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
        f"Histórico salvo: {len(history['published'])} notícias"
    )


# ==========================================
# ENVIAR PARA TELEGRAM
# ==========================================

def get_image_from_rss(item):

    # Tenta encontrar imagem em media_content

    if "media_content" in item:

        for media in item.media_content:

            url = media.get("url")

            if url:

                return url


    # Tenta encontrar imagem em media_thumbnail

    if "media_thumbnail" in item:

        for media in item.media_thumbnail:

            url = media.get("url")

            if url:

                return url


    # Tenta encontrar imagem em enclosures

    if "enclosures" in item:

        for enclosure in item.enclosures:

            url = enclosure.get("url")

            if url:

                return url


    return None

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
                "Não foi possível abrir a página:"
                f" {response.status_code}"
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

            image = og_image.get("content")

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

            image = twitter_image.get("content")

            if image:

                return image


        # ==================================
        # PRIMEIRA IMAGEM DA PÁGINA
        # ==================================

        image_tag = soup.find(
            "img"
        )


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

def get_news_image(item, link):

    print(
        "Procurando imagem no RSS..."
    )


    # Primeiro tenta pelo RSS

    image = get_image_from_rss(
        item
    )


    if image:

        print(
            "Imagem encontrada no RSS:"
        )

        print(image)

        return image


    # Se não encontrou, procura na página

    print(
        "Imagem não encontrada no RSS."
    )

    print(
        "Procurando imagem na página..."
    )


    image = get_image_from_page(
        link
    )


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


def send_telegram(title, link, image):

    caption = (
        f"📰 <b>{title}</b>\n\n"
        f"🔗 <b>Leia a matéria:</b>\n"
        f"{link}"
    )


    # ==================================
    # SE EXISTIR FOTO
    # ==================================

    if image:

        url = (
            f"https://api.telegram.org/"
            f"bot{TELEGRAM_TOKEN}/sendPhoto"
        )


        data = {

            "chat_id": TELEGRAM_CHAT_ID,

            "photo": image,

            "caption": caption,

            "parse_mode": "HTML"
        }


    # ==================================
    # SE NÃO EXISTIR FOTO
    # ==================================

    else:

        url = (
            f"https://api.telegram.org/"
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
# PRINCIPAL
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
    # VERIFICAR CONFIGURAÇÕES
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
    # CARREGAR HISTÓRICO
    # ======================================

    history = load_history()

    published = history["published"]


    print(
        f"Notícias no histórico: {len(published)}"
    )


    # ======================================
    # CARREGAR FONTES RSS
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
        f"Fontes RSS encontradas: {len(feeds)}"
    )


    total_new = 0


    # ======================================
    # VERIFICAR CADA FONTE
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
        # LER RSS
        # ==================================

        try:

            rss = feedparser.parse(
                source_url
            )

        except Exception as error:

            print(
                f"Erro ao consultar RSS: {error}"
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
        # PROCESSAR NOTÍCIAS
        # ==================================

        # Verifica somente as 20 mais recentes

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

                print(
                    "Notícia sem link. Ignorando."
                )

                continue


            # ==================================
            # VERIFICAR DUPLICAÇÃO
            # ==================================

            if link in published:

                print(
                    f"IGNORADA - já publicada: {title}"
                )

                continue


            # ==================================
            # NOVA NOTÍCIA
            # ==================================

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
            # PROCURAR IMAGEM
            # ==================================
           image = get_news_image(
            item,
            link
)
            # ==================================
            # PUBLICAR NO TELEGRAM
            # ==================================

            success = send_telegram(
            title,
            link,
            image
)
            # ==================================
            # SALVAR NO HISTÓRICO
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
                    "Não foi salva porque "
                    "o Telegram não confirmou o envio."
                )


    # ======================================
    # RESULTADO FINAL
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
# INICIAR BOT
# ==========================================

if __name__ == "__main__":

    main()
