from playwright.sync_api import sync_playwright

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir="linkedin_profile",
        channel="msedge",
        headless=False
    )

    page = context.new_page()

    # Abre directamente el perfil que ya sabemos funciona
    page.goto(
        "https://www.linkedin.com/in/jose-nasimoff-23387311b/"
    )

    page.wait_for_timeout(5000)

    try:

        nombre = page.locator("h1").inner_text()

        empresa = page.locator(
            ".text-body-medium.break-words"
        ).inner_text()

        ubicacion = page.locator(
            ".text-body-small.inline.t-black--light.break-words"
        ).inner_text()

        url = page.url

        print("\n====================")
        print("DATOS EXTRAIDOS")
        print("====================")
        print("Nombre:", nombre)
        print("Empresa:", empresa)
        print("Ubicación:", ubicacion)
        print("URL:", url)
        print("====================\n")

    except Exception as e:

        print("ERROR:")
        print(e)

    input("Pulsa Enter para cerrar...")

    context.close()