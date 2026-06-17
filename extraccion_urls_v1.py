from playwright.sync_api import sync_playwright
import pandas as pd
import random

OBJETIVO = 200

with sync_playwright() as p:

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

    nombres_procesados = set()
    urls_procesadas = set()

    resultados = []

    errores = 0
    scroll_num = 0

    while len(resultados) < OBJETIVO:

        favoritos = page.locator(
            ".msg-conversation-card__participant-names"
        )

        visibles = favoritos.count()

        print(
            f"\nSCROLL {scroll_num} | "
            f"Visibles: {visibles} | "
            f"Procesados: {len(resultados)}"
        )

        for i in range(visibles):

            if len(resultados) >= OBJETIVO:
                break

            try:

                nombre = favoritos.nth(i).inner_text()
                nombre = " ".join(nombre.split())

                if not nombre:
                    continue

                if nombre in nombres_procesados:
                    continue

                nombres_procesados.add(nombre)

                print(
                    f"\n[{len(resultados)+1}/{OBJETIVO}] "
                    f"{nombre}"
                )

                # Pausa antes del clic
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

                # Simula lectura del chat
                page.wait_for_timeout(
                    random.randint(4000, 8000)
                )

                links = page.locator("a")

                url_encontrada = None

                for j in range(links.count()):

                    try:

                        href = links.nth(j).get_attribute("href")

                        if href and "/in/" in href:

                            url_encontrada = href
                            break

                    except:
                        pass

                if not url_encontrada:

                    print("No se encontró URL")
                    continue

                if url_encontrada in urls_procesadas:

                    print("URL duplicada")
                    continue

                urls_procesadas.add(url_encontrada)

                resultados.append({
                    "Nombre": nombre,
                    "LinkedIn_URL": url_encontrada
                })

                # Backup cada 10 registros
                if len(resultados) % 10 == 0:
                    pd.DataFrame(
                        resultados
                    ).to_excel(
                        "backup_linkedin.xlsx",
                        index=False
                    )

                    print(
                        f"Backup guardado ({len(resultados)} registros)"
                    )

                print(
                    f"OK | URLs únicas: "
                    f"{len(urls_procesadas)}"
                )

                # Pausa entre contactos
                page.wait_for_timeout(
                    random.randint(2000, 5000)
                )

                # Descanso normal cada 10
                if len(resultados) % 10 == 0:
                    pausa = random.randint(
                        30000,
                        60000
                    )

                    print(
                        f"\nDescanso normal "
                        f"{pausa/1000:.0f}s"
                    )

                    page.wait_for_timeout(pausa)

                # Descanso extendido cada 20
                if len(resultados) % 20 == 0:
                    pausa = random.randint(
                        60000,
                        120000
                    )

                    print(
                        f"\nDescanso extendido "
                        f"{pausa/1000:.0f}s"
                    )

                    page.wait_for_timeout(pausa)

                if len(resultados) % 50 == 0:
                    pausa = random.randint(
                        180000,
                        300000
                    )

                    print(
                        f"\nPausa larga de seguridad "
                        f"{pausa/1000:.0f}s"
                    )

                    page.wait_for_timeout(pausa)

            except Exception as e:

                errores += 1

                print(
                    f"\nERROR ({errores}) con:"
                )

                print(nombre)

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
    f"\nScrollando {desplazamiento}px"
)

try:

    contenedor = page.locator(
        ".msg-overlay-list-bubble__content--scrollable"
    ).first

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

    print(
        "\nERROR EN SCROLL"
    )

    print(str(e))

    print(
        "\nEsperando antes de reintentar..."
    )

    page.wait_for_timeout(
        random.randint(
            5000,
            10000
        )
    )

    try:

        contenedor = page.locator(
            ".msg-overlay-list-bubble__content--scrollable"
        ).first

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

        print(
            "\nNo se pudo recuperar el contenedor."
        )

        print(
            "Recargando Mensajes..."
        )

        page.goto(
            "https://www.linkedin.com/messaging/"
        )

        page.wait_for_timeout(
            random.randint(
                8000,
                12000
            )
        )

    df = pd.DataFrame(resultados)

    archivo = "linkedin_200_contactos.xlsx"

    df["Fecha_Extraccion"] = pd.Timestamp.now()

    df.to_excel(
        archivo,
        index=False
    )

    print("\n====================")
    print("FINALIZADO")
    print("====================")
    print(f"Registros: {len(df)}")
    print(f"URLs únicas: {len(urls_procesadas)}")
    print(f"Errores: {errores}")
    print(f"Archivo: {archivo}")

    input("\nPulsa Enter para cerrar...")

    context.close()