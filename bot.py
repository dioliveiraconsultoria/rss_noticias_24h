import os
import json
import requests
import feedparser


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
        "Histórico salvo."
    )


# ==========================================
# ENVIAR PARA TELEGRAM
# ==========================================

def send_telegram(title, link):

    message = (
        f"📰 <b>{title}</b>\n\n"
        f"🔗 <b>Leia a matéria:</b>\n"
        f"{link}"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_TOKEN}/sendMessage"
    )

    data = {

        "chat_id": TELEGRAM_CHAT_ID,

        "text": message,

        "parse_mode": "HTML",

        "disable_web_page_preview": False
    }

    response = requests.post(
        url,
        data=data,
        timeout=30
    )

    if response.ok:

        print(
            "Mensagem enviada:"
        )

        print(title)

        return True

    else:

        print(
            "Erro Telegram:"
        )

        print(response.text)

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


    if not TELEGRAM_TOKEN:

        raise Exception(
            "TELEGRAM_TOKEN não configurado."
        )


    if not TELEGRAM_CHAT_ID:

        raise Exception(
            "TELEGRAM_CHAT_ID não configurado."
        )


    # --------------------------------------
    # CARREGAR HISTÓRICO
    # --------------------------------------

    history = load_history()

    published = history["published"]


    print(
        f"Notícias no histórico: {len(published)}"
    )


    # --------------------------------------
    # CARREGAR RSS
    # --------------------------------------

    with open(
        "feeds.json",
        "r",
        encoding="utf-8"
    ) as file:

        feeds = json.load(file)


    total_new = 0


    # --------------------------------------
    # VERIFICAR FONTES
    # --------------------------------------

    for feed in feeds:

        source_name = feed["name"]

        source_url = feed["url"]


        print()
        print(
            "===================================="
        )

        print(
            f"Fonte: {source_name}"
        )

        print(
            "===================================="
        )


        rss = feedparser.parse(
            source_url
        )


        # Últimas 20 notícias
        entries = rss.entries[:20]


        # ----------------------------------
        # NOTÍCIAS
        # ----------------------------------

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


            # ----------------------------------
            # VERIFICAR DUPLICAÇÃO
            # ----------------------------------

            if link in published:

                print(
                    "IGNORADA - já publicada:"
                )

                print(title)

                continue


            print()
            print(
                "NOVA NOTÍCIA:"
            )

            print(title)

            print(link)


            # ----------------------------------
            # PUBLICAR
            # ----------------------------------

            success = send_telegram(
                title,
                link
            )


            if success:

                # Adiciona ao histórico
                published.append(link)

                total_new += 1


                # Salva imediatamente
                save_history(
                    history
                )


                print(
                    "SALVA NO HISTÓRICO"
                )


    print()
    print(
        "===================================="
    )

    print(
        f"NOVAS PUBLICAÇÕES: {total_new}"
    )

    print(
        f"TOTAL NO HISTÓRICO: {len(published)}"
    )

    print(
        "===================================="


if __name__ == "__main__":

    main()
