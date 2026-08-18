import os
import json
import hashlib
import requests
import feedparser


TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

DATABASE_FILE = "published.json"


def load_published():

    if not os.path.exists(DATABASE_FILE):
        return set()

    try:
        with open(DATABASE_FILE, "r", encoding="utf-8") as file:
            return set(json.load(file))

    except Exception:
        return set()


def save_published(published):

    with open(
        DATABASE_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            published,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(
        f"Histórico salvo: {len(published)} notícias"
    )


def create_id(link):

    return hashlib.md5(
        link.encode("utf-8")
    ).hexdigest()


def get_image(entry):

    # Tenta encontrar imagem no media_content
    if "media_content" in entry:

        for media in entry.media_content:

            if "url" in media:
                return media["url"]


    # Tenta encontrar imagem no media_thumbnail
    if "media_thumbnail" in entry:

        for media in entry.media_thumbnail:

            if "url" in media:
                return media["url"]


    # Tenta encontrar imagem em enclosures
    if "enclosures" in entry:

        for enclosure in entry.enclosures:

            if "url" in enclosure:

                url = enclosure["url"]

                if any(
                    ext in url.lower()
                    for ext in [".jpg", ".jpeg", ".png", ".webp"]
                ):
                    return url


    return None


def send_telegram(title, link, image):

    caption = (
    f"📰 <b>{title}</b>\n\n"
    f"🔗 <b>Leia a matéria:</b>\n"
    f"{link}"
)


    # Se encontrou imagem
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


    response = requests.post(
        url,
        data=data,
        timeout=30
    )


    if not response.ok:

        print(
            "Erro ao enviar para Telegram:",
            response.text
        )


    return response.ok


def main():

    if not TELEGRAM_TOKEN:

        raise Exception(
            "TELEGRAM_TOKEN não configurado."
        )


    if not TELEGRAM_CHAT_ID:

        raise Exception(
            "TELEGRAM_CHAT_ID não configurado."
        )


    with open(
        "feeds.json",
        "r",
        encoding="utf-8"
    ) as file:

        feeds = json.load(file)


    published = load_published()


    for feed in feeds:

        print(
            f"Verificando: {feed['name']}"
        )


        rss = feedparser.parse(
            feed["url"]
        )


        for item in reversed(
            rss.entries[:20]
        ):

            title = item.get(
                "title",
                "Sem título"
            )


            link = item.get("link")


            if not link:

                continue


            news_id = create_id(link)


            if news_id in published:

                continue


            image = get_image(item)


            success = send_telegram(
                title,
                link,
                image
            )


            if success:

                published.add(news_id)


                print(
                    "Publicado:",
                    title
                )


    save_published(published)


if __name__ == "__main__":

    main()
