# LinkedIn Messages CRM Builder

Automatizacion personal en Python para construir una base CRM a partir de conversaciones visibles en LinkedIn Messages.

El proyecto usa Playwright con Microsoft Edge y un perfil persistente ya autenticado. El objetivo es recorrer conversaciones de LinkedIn Messages, extraer datos visibles y consolidarlos en archivos Excel por tandas, minimizando acciones innecesarias sobre la cuenta.

## Objetivo

Construir una base maestra de contactos a partir de conversaciones de LinkedIn Messages, sin abrir perfiles y sin navegar fuera del area de mensajes.

Campos generados:

- `ID`
- `Nombre`
- `Headline`
- `Correos`
- `LinkedIn_URL`
- `Ultima_Interaccion`
- `Fecha_Extraccion`
- `Tanda`

## Enfoque de bajo riesgo

El script esta disenado para reducir interacciones innecesarias:

- La versión actual evita abrir perfiles de LinkedIn.
- No realiza busquedas.
- No navega fuera de LinkedIn Messages.
- No hace scroll dentro del historial de mensajes.
- Extrae `Headline` y `Correos` solo si ya estan visibles.
- Usa pausas aleatorias entre acciones.
- Incluye descansos periodicos durante la ejecucion.
- Procesa contactos por tandas para evitar sesiones demasiado largas.

## Flujo general

1. Abre LinkedIn Messages.
2. El usuario abre manualmente la seccion Favoritos.
3. El script recorre la lista visible de conversaciones.
4. Abre cada conversacion no procesada.
5. Extrae informacion visible.
6. Guarda resultados por tanda.
7. Actualiza un archivo maestro consolidado.
8. Hace backups periodicos.

## Arquitectura

El proyecto se encuentra dividido en tres etapas principales:

### diagnostico_favoritos.py

Valida la carga dinámica de conversaciones y permite estimar el volumen de contactos disponibles.

### extraccion_urls_v1.py

Primera versión utilizada para validar la extracción de URLs de LinkedIn desde conversaciones.

### linkedin_messages_crm.py

Versión principal actualmente en desarrollo.

Gestiona:

- Procesamiento por tandas.
- Consolidación de datos.
- Backups.
- Exportación de resultados.
- Reanudación de ejecuciones previas.

## Trabajo por tandas

El script esta pensado para ejecutarse en tandas, por ejemplo de 100 contactos.

Configuracion recomendada:

```python
OBJETIVO = 100
NOMBRE_TANDA = "tanda_1"
```

Para la siguiente ejecucion solo se cambia el nombre de la tanda:

```python
OBJETIVO = 100
NOMBRE_TANDA = "tanda_2"
```

El archivo `linkedin_master.xlsx` funciona como memoria entre ejecuciones. Al iniciar una nueva tanda, el script carga ese archivo y salta contactos ya procesados.

Ejemplo de plan para 521 contactos:

```text
tanda_1: 100 contactos
tanda_2: 100 contactos
tanda_3: 100 contactos
tanda_4: 100 contactos
tanda_5: 100 contactos
tanda_6: contactos restantes
```

## Archivos generados

Durante la ejecucion se generan archivos locales como:

```text
linkedin_master.xlsx
linkedin_tanda_1.xlsx
linkedin_tanda_2.xlsx
backup_tanda_1.xlsx
backup_tanda_2.xlsx
```

Estos archivos pueden contener nombres, URLs, correos y otros datos personales. No deben subirse al repositorio.

## Instalacion

Crear y activar un entorno virtual:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Instalar dependencias:

```bash
pip install playwright pandas openpyxl
playwright install
```

El script usa Microsoft Edge mediante Playwright:

```python
channel="msedge"
```

## Uso

1. Iniciar sesion en LinkedIn desde Microsoft Edge.
2. Ejecutar el script.
3. Esperar a que abra LinkedIn Messages.
4. Abrir manualmente la seccion Favoritos.
5. Volver a la consola y presionar Enter.
6. Dejar que el script procese la tanda configurada.

## Recomendaciones operativas

Para reducir riesgo operativo:

- Usar tandas pequenas, idealmente de 100 contactos o menos.
- Evitar correr muchas tandas seguidas.
- Dejar varias horas entre tandas.
- No correr el script si LinkedIn muestra verificaciones, captchas o errores de carga.
- Revisar los archivos generados despues de cada tanda.
- Mantener `linkedin_master.xlsx`, ya que permite continuar sin reprocesar contactos.

## Privacidad y seguridad

Antes de subir el proyecto a GitHub, verificar que no se incluyan:

- Archivos Excel con contactos reales.
- Backups generados.
- Carpeta del perfil persistente del navegador.
- Capturas de pantalla con datos personales.
- Logs con nombres, correos o URLs.
- Rutas locales del equipo.
- Credenciales, cookies, tokens o variables sensibles.

Se recomienda crear un archivo `.gitignore` con reglas como:

```gitignore
# Perfil persistente de navegador
linkedin_profile/

# Archivos generados
*.xlsx
*.xls
*.csv

# Backups y salidas
backup_*.xlsx
linkedin_master.xlsx
linkedin_tanda_*.xlsx
linkedin_*_contactos*.xlsx

# Capturas, logs y temporales
*.png
*.jpg
*.jpeg
*.webp
*.log

# Python
__pycache__/
*.pyc
.venv/
venv/
.env
```

## Limitaciones

- `Headline` solo se extrae si esta visible en la conversacion o en elementos ya renderizados.
- `Correos` solo se extraen si aparecen visibles en el texto cargado del chat.
- El script no intenta completar datos faltantes abriendo perfiles o recorriendo historiales extensos.
- LinkedIn puede cambiar selectores del DOM, por lo que pueden requerirse ajustes futuros.

## Estado actual

Funcionalidades validadas:

- Extracción de nombres.
- Extracción de URLs de LinkedIn.
- Extracción de última interacción.
- Procesamiento por tandas.
- Consolidación en archivo maestro.
- Backups automáticos.

Funcionalidades en desarrollo:

- Extracción de headline.
- Extracción de correos visibles.

## Aviso

Este proyecto esta pensado para uso personal y responsable. Revisar siempre los terminos de uso de LinkedIn y las normativas aplicables de privacidad y proteccion de datos antes de utilizar automatizaciones sobre informacion de contactos.
