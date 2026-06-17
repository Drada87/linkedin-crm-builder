from playwright.sync_api import sync_playwright
import pandas as pd
import random
import re
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================

inicio = datetime.now()

# Cantidad de contactos nuevos a procesar en esta ejecución.
OBJETIVO = 100

# Cambiar solo este valor en cada tanda:
# tanda_1, tanda_2, tanda_3, etc.
NOMBRE_TANDA = "tanda_2"

# Archivo consolidado entre todas las tandas.
ARCHIVO_MAESTRO = "linkedin_master.xlsx"

# Archivos propios de la tanda actual.
ARCHIVO_SALIDA = f"linkedin_{NOMBRE_TANDA}.xlsx"
ARCHIVO_BACKUP = f"backup_{NOMBRE_TANDA}.xlsx"

# Limite preventivo para evitar que una tanda quede scrolleando sin fin.
MAX_SCROLLS = 120


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def limpiar_texto(texto):
    """Normaliza espacios y convierte valores vacios en string vacio."""
    if not texto:
        return ""

    return " ".join(str(texto).split())


def cargar_master():
    """
    Carga el archivo maestro si existe.

    El master funciona como memoria entre tandas:
    permite saltar contactos ya procesados sin depender de la posicion
    exacta que ocupan en LinkedIn Messages.
    """
    nombres = set()
    urls = set()
    total_master = 0

    try:
        df_master = pd.read_excel(ARCHIVO_MAESTRO)

        if "LinkedIn_URL" in df_master.columns:
            df_master = df_master.drop_duplicates(
                subset=["LinkedIn_URL"],
                keep="first"
            )

        total_master = len(df_master)

        if "Nombre" in df_master.columns:
            nombres.update(
                df_master["Nombre"]
                .dropna()
                .astype(str)
                .map(limpiar_texto)
                .tolist()
            )

        if "LinkedIn_URL" in df_master.columns:
            urls.update(
                df_master["LinkedIn_URL"]
                .dropna()
                .astype(str)
                .map(limpiar_texto)
                .tolist()
            )

        print(
            f"Master cargado: "
            f"{total_master} registros | "
            f"{len(nombres)} nombres | "
            f"{len(urls)} URLs"
        )

    except FileNotFoundError:
        print("No existe master previo. Iniciando desde cero.")

    except Exception as e:
        print("No se pudo cargar el master.")
        print(str(e))

    return nombres, urls, total_master


def guardar_resultados(resultados):
    """
    Guarda la tanda actual y actualiza el archivo maestro.

    Se puede llamar varias veces durante la ejecucion. Si ya existen filas
    previas de la misma tanda, el master queda limpio por deduplicacion de URL.
    """
    if not resultados:
        return

    df_tanda = pd.DataFrame(resultados)

    df_tanda["Fecha_Extraccion"] = pd.Timestamp.now()
    df_tanda["Tanda"] = NOMBRE_TANDA

    # Archivo individual de la tanda.
    df_tanda.to_excel(
        ARCHIVO_SALIDA,
        index=False
    )

    # Backup de la tanda.
    df_tanda.to_excel(
        ARCHIVO_BACKUP,
        index=False
    )

    try:
        df_master = pd.read_excel(ARCHIVO_MAESTRO)
        df_final = pd.concat(
            [df_master, df_tanda],
            ignore_index=True
        )

    except FileNotFoundError:
        df_final = df_tanda

    if "LinkedIn_URL" in df_final.columns:
        df_final = df_final.drop_duplicates(
            subset=["LinkedIn_URL"],
            keep="first"
        )

    df_final.to_excel(
        ARCHIVO_MAESTRO,
        index=False
    )


def extraer_info_visible(page, nombre):
    """
    Extrae informacion solo si ya esta visible en la conversacion.

    No abre perfiles.
    No hace busquedas.
    No hace scroll dentro del historial.
    No navega fuera de Messages.
    """
    correos = set()
    headline = ""

    # Correos visibles en el texto actualmente renderizado del chat.
    try:
        texto_chat = page.locator(
            ".msg-s-message-list"
        ).first.inner_text(timeout=2000)

        encontrados = re.findall(
            r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
            texto_chat
        )

        for correo in encontrados:
            correos.add(correo.strip())

    except:
        pass

    # Posibles headlines visibles en elementos con atributo title.
    try:
        candidatos = page.locator(
            ".msg-s-message-list div[title], "
            ".msg-entity-lockup__entity-info div[title]"
        )

        for h in range(candidatos.count()):

            try:
                candidato = candidatos.nth(h)

                if not candidato.is_visible():
                    continue

                texto = candidato.get_attribute("title")

                if not texto:
                    texto = candidato.inner_text(timeout=1000)

                texto = limpiar_texto(texto)

                if not texto:
                    continue

                if texto == nombre:
                    continue

                if texto.startswith("Estado:"):
                    continue

                if texto.startswith("Movil"):
                    continue

                if texto.startswith("Móvil"):
                    continue

                if "@" in texto:
                    continue

                if "linkedin.com" in texto.lower():
                    continue

                if len(texto) < 25:
                    continue

                headline = texto
                break

            except:
                pass

    except:
        pass

    return {
        "Headline": headline,
        "Correos": ", ".join(sorted(correos))
    }


def obtener_contenedor_lista(page):
    """
    Busca el contenedor scrolleable de la lista izquierda de conversaciones.
    Se dejan dos opciones porque LinkedIn puede variar clases segun vista.
    """
    selectores = [
        ".msg-overlay-list-bubble__content--scrollable",
        ".msg-conversations-container__conversations-list"
    ]

    for selector in selectores:
        try:
            contenedor = page.locator(selector)

            if contenedor.count() > 0:
                return contenedor.first

        except:
            pass

    return None


# ============================================================
# EJECUCION PRINCIPAL
# ============================================================

with sync_playwright() as p:

    # Usa Edge con perfil persistente ya autenticado.
    context = p.chromium.launch_persistent_context(
        user_data_dir="linkedin_profile",
        channel="msedge",
        headless=False
    )

    page = context.new_page()

    page.goto("https://www.linkedin.com/messaging/")

    page.wait_for_timeout(5000)

    input("Abre Favoritos y pulsa Enter...")

    conversaciones = page.get_by_label(
        "Lista de conversaciones"
    )

    nombres_procesados, urls_procesadas, total_master = cargar_master()

    resultados = []

    errores = 0
    scroll_num = 0

    while len(resultados) < OBJETIVO and scroll_num <= MAX_SCROLLS:

        favoritos = page.locator(
            ".msg-conversation-card__participant-names"
        )

        tarjetas = page.locator(
            ".msg-conversation-card"
        )

        visibles = favoritos.count()

        print(
            f"\nSCROLL {scroll_num} | "
            f"Visibles: {visibles} | "
            f"Nuevos en tanda: {len(resultados)}"
        )

        for i in range(visibles):

            if len(resultados) >= OBJETIVO:
                break

            try:
                nombre = favoritos.nth(i).inner_text()
                nombre = limpiar_texto(nombre)

                if not nombre:
                    continue

                # Salta contactos ya guardados en el master o ya vistos en esta tanda.
                if nombre in nombres_procesados:
                    continue

                ultima_interaccion = ""

                try:
                    tarjeta = tarjetas.nth(i)

                    ultima_interaccion = tarjeta.locator(
                        "time.msg-conversation-card__time-stamp"
                    ).first.inner_text(timeout=1500)

                    ultima_interaccion = limpiar_texto(
                        ultima_interaccion
                    )

                except:
                    pass

                print(
                    f"\n[{len(resultados) + 1}/{OBJETIVO}] "
                    f"{nombre}"
                )

                if ultima_interaccion:
                    print(f"Ultima interaccion: {ultima_interaccion}")

                # Pausa antes del click.
                page.wait_for_timeout(
                    random.randint(1500, 3000)
                )

                locator = conversaciones.get_by_text(
                    nombre,
                    exact=False
                ).first

                locator.scroll_into_view_if_needed()

                page.wait_for_timeout(
                    random.randint(500, 1500)
                )

                locator.click(timeout=10000)

                # Tiempo de lectura simulado.
                page.wait_for_timeout(
                    random.randint(4000, 8000)
                )

                info_visible = extraer_info_visible(
                    page,
                    nombre
                )

                headline = info_visible["Headline"]
                correos = info_visible["Correos"]

                links = page.locator("a")

                url_encontrada = None

                for j in range(links.count()):

                    try:
                        href = links.nth(j).get_attribute("href")

                        if href and "/in/" in href:
                            url_encontrada = limpiar_texto(href)
                            break

                    except:
                        pass

                if not url_encontrada:
                    print("No se encontro URL")
                    nombres_procesados.add(nombre)
                    continue

                if url_encontrada in urls_procesadas:
                    print("URL duplicada")
                    nombres_procesados.add(nombre)
                    continue

                nombres_procesados.add(nombre)
                urls_procesadas.add(url_encontrada)

                resultados.append({
                    "ID": total_master + len(resultados) + 1,
                    "Nombre": nombre,
                    "Headline": headline,
                    "Correos": correos,
                    "LinkedIn_URL": url_encontrada,
                    "Ultima_Interaccion": ultima_interaccion
                })

                if len(resultados) % 10 == 0:
                    guardar_resultados(resultados)

                    print(
                        f"Backup y master actualizados "
                        f"({len(resultados)} registros nuevos)"
                    )

                print(
                    f"OK | Nuevos en tanda: "
                    f"{len(resultados)}"
                )

                page.wait_for_timeout(
                    random.randint(2000, 5000)
                )

                if len(resultados) % 10 == 0:
                    pausa = random.randint(
                        30000,
                        60000
                    )

                    print(
                        f"\nDescanso normal "
                        f"{pausa / 1000:.0f}s"
                    )

                    page.wait_for_timeout(pausa)

                if len(resultados) % 20 == 0:
                    pausa = random.randint(
                        60000,
                        120000
                    )

                    print(
                        f"\nDescanso extendido "
                        f"{pausa / 1000:.0f}s"
                    )

                    page.wait_for_timeout(pausa)

                if len(resultados) % 50 == 0:
                    pausa = random.randint(
                        180000,
                        300000
                    )

                    print(
                        f"\nPausa larga de seguridad "
                        f"{pausa / 1000:.0f}s"
                    )

                    page.wait_for_timeout(pausa)

            except Exception as e:

                errores += 1

                print(f"\nERROR ({errores}) con:")

                try:
                    print(nombre)
                except:
                    print("Nombre no disponible")

                print(str(e))

                continue

        if len(resultados) >= OBJETIVO:
            break

        scroll_num += 1

        desplazamiento = random.randint(
            800,
            1400
        )

        print(
            f"\nScrollando lista {desplazamiento}px"
        )

        try:
            contenedor = obtener_contenedor_lista(page)

            if not contenedor:
                raise Exception("No se encontro contenedor scrolleable.")

            contenedor.evaluate(
                f"(el) => el.scrollTop += {desplazamiento}"
            )

            page.wait_for_timeout(
                random.randint(
                    3000,
                    6000
                )
            )

        except Exception as e:

            print("\nERROR EN SCROLL")
            print(str(e))
            print("\nEsperando antes de reintentar...")

            page.wait_for_timeout(
                random.randint(
                    5000,
                    10000
                )
            )

            try:
                contenedor = obtener_contenedor_lista(page)

                if not contenedor:
                    raise Exception("No se recupero el contenedor.")

                contenedor.evaluate(
                    f"(el) => el.scrollTop += {desplazamiento}"
                )

                page.wait_for_timeout(
                    random.randint(
                        3000,
                        6000
                    )
                )

            except:
                print("\nNo se pudo recuperar el contenedor.")
                print("Recargando Messages...")

                page.goto(
                    "https://www.linkedin.com/messaging/"
                )

                page.wait_for_timeout(
                    random.randint(
                        8000,
                        12000
                    )
                )

    guardar_resultados(resultados)

    fin = datetime.now()

    segundos = (fin - inicio).total_seconds()

    print("\n====================")
    print("TIEMPOS")
    print("====================")

    print(
        "Inicio:",
        inicio.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "Fin:",
        fin.strftime("%Y-%m-%d %H:%M:%S")
    )

    print(
        "Duracion:",
        fin - inicio
    )

    if segundos > 0:
        print(
            f"Contactos/hora: "
            f"{round(len(resultados) / (segundos / 3600), 2)}"
        )

    print("\n====================")
    print("RESUMEN")
    print("====================")
    print(f"Tanda: {NOMBRE_TANDA}")
    print(f"Nuevos procesados: {len(resultados)}")
    print(f"Errores: {errores}")
    print(f"Scrolls realizados: {scroll_num}")
    print(f"Salida tanda: {ARCHIVO_SALIDA}")
    print(f"Backup tanda: {ARCHIVO_BACKUP}")
    print(f"Master: {ARCHIVO_MAESTRO}")

    if scroll_num > MAX_SCROLLS:
        print("\nSe alcanzo MAX_SCROLLS antes del objetivo.")

    input("\nPulsa Enter para cerrar...")
