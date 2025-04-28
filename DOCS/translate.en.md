# 🈯 Internationalization in `ckanext-api-tracking`

This document describes the steps required to extract translatable strings and generate `.po` files for translations in CKAN.

---

## 🐳 1. Enter the CKAN container

From the host:

```bash
make bash
```

This executes:

```bash
docker compose exec ckan_base bash
```

---

## 🧪 2. Activate the virtual environment and navigate to the extension

```bash
source venv/bin/activate
cd src_extensions/ckanext-api-tracking/
```

---

## 🏗️ 3. Extract translatable messages

```bash
python setup.py extract_messages
```

📄 This generates the `.pot` file at:

```
ckanext/api_tracking/i18n/ckanext-api-tracking.pot
```

---

## 🌍 4. Initialize a `.po` file for a language (e.g., Spanish)

```bash
python setup.py init_catalog -l es -i ckanext/api_tracking/i18n/ckanext-api-tracking.pot -d ckanext/api_tracking/i18n/
```

📁 This creates:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po
```

---

## 📝 5. Edit the `.po` file

You can use:

- [Poedit](https://poedit.net/)
- `gettext` plugin in VS Code
- Or any plain text editor

Translate each `msgid` by filling in the `msgstr`.

---

## ✅ 6. Compile the `.mo` file (optional)

Once the `.po` file is translated, compile it:

```bash
python setup.py compile_catalog -l es -d ckanext/api_tracking/i18n/
```

This generates:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.mo
```

---

## 📤 7. (Optional) Copy the files to your local machine

From your machine, identify the container:

```bash
docker ps
```

Then copy the `.po` or `.pot` file:

```bash
docker cp <container_name>:/app/src_extensions/ckanext-api-tracking/ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po .
```

---

## 🧾 Notes

- The `-l` parameter is mandatory in `init_catalog`.
- Make sure `babel` is installed in your virtual environment.

---
