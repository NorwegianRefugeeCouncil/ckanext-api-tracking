# 🈯 Internacionalización en `ckanext-api-tracking`

Este documento describe los pasos necesarios para extraer cadenas traducibles y generar archivos `.po` para traducciones en la extensión `ckanext-api-tracking`.

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
pybabel extract -F babel.cfg \
  -o ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  ckanext/api_tracking
```

Esto genera el archivo `.pot` en:

```
ckanext/api_tracking/i18n/ckanext-api-tracking.pot
```

---

## 🌍 4. Inicializar archivo `.po` para un idioma (ej. español)

```bash
pybabel init -i ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  -d ckanext/api_tracking/i18n \
  -l es
```

Esto crea:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po
```

---

## 📝 5. Editar archivo `.po`

Podés usar:

- [Poedit](https://poedit.net/)
- Plugin **gettext** en VS Code
- O cualquier editor de texto plano

Traducí cada `msgid` completando su `msgstr`.

---

## 🔄 6. Actualizar traducciones tras cambios

Si modificaste cadenas o plantillas, primero vuelve a extraer y luego actualiza:

```bash
pybabel extract -F babel.cfg \
  -o ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  ckanext/api_tracking

pybabel update -i ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  -d ckanext/api_tracking/i18n \
  -l es
```

---

## ✅ 7. Compilar el archivo `.mo`

```bash
pybabel compile -d ckanext/api_tracking/i18n
```

Esto genera:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.mo
```

---

## 📤 8. Copiar archivos a máquina local (opcional)

Identificá el contenedor:

```bash
docker ps
```

Luego copiá:

```bash
docker cp <contenedor>:/app/src_extensions/ckanext-api-tracking/ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po .
docker cp <contenedor>:/app/src_extensions/ckanext-api-tracking/ckanext/api_tracking/i18n/ckanext-api-tracking.pot .
```

---

## 🧾 Notas

- El parámetro `-l` es obligatorio en `init` y `update`.
- Asegurate de tener instalado `babel` y las dependencias de localización en tu entorno virtual.
- El fichero `babel.cfg` define extractores y opciones (keywords, rutas de plantillas).
