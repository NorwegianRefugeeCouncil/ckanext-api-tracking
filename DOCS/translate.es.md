# 🈯 Internacionalización en `ckanext-api-tracking`

Este documento describe los pasos necesarios para extraer cadenas traducibles y generar archivos `.po` para traducciones en CKAN.

---

## 🐳 1. Ingresar al contenedor CKAN

Desde el host:

```bash
make bash
```

Esto ejecuta:

```bash
docker compose exec ckan_base bash
```

---

## 🧪 2. Activar entorno virtual y navegar a la extensión

```bash
source venv/bin/activate
cd src_extensions/ckanext-api-tracking/
```

---

## 🏗️ 3. Extraer mensajes traducibles

```bash
python setup.py extract_messages
```

📄 Esto genera el archivo `.pot` en:

```
ckanext/api_tracking/i18n/ckanext-api-tracking.pot
```

---

## 🌍 4. Inicializar archivo `.po` para un idioma (ej. español)

```bash
python setup.py init_catalog -l es -i ckanext/api_tracking/i18n/ckanext-api-tracking.pot -d ckanext/api_tracking/i18n/
```

📁 Esto crea:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po
```

---

## 📝 5. Editar archivo `.po`

Podés usar:

- [Poedit](https://poedit.net/)
- Plugin `gettext` en VS Code
- O cualquier editor de texto plano

Traducí cada `msgid` rellenando el `msgstr`.

---

## ✅ 6. Compilar el archivo `.mo` (opcional)

Una vez traducido el `.po`, compilalo:

```bash
python setup.py compile_catalog -l es -d ckanext/api_tracking/i18n/
```

Esto genera:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.mo
```

---

## 📤 7. (Opcional) Copiar los archivos a tu máquina local

Desde tu máquina, identificá el contenedor:

```bash
docker ps
```

Luego copiá el `.po` o `.pot`:

```bash
docker cp <nombre_contenedor>:/app/src_extensions/ckanext-api-tracking/ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po .
```

---

## 🧾 Notas

- El parámetro `-l` es obligatorio en `init_catalog`.
- Asegurate de tener instalado `babel` en tu entorno virtual.

---
