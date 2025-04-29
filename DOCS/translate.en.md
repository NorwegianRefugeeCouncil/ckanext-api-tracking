# 🈯 Internationalization in `ckanext-api-tracking`

This document describes the steps required to extract translatable strings and generate `.po` files for translations in the `ckanext-api-tracking` extension.

---

## 🐳 1. Enter the CKAN container

From the host:

```bash
make bash
```

This runs:

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
pybabel extract -F babel.cfg \
  -o ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  ckanext/api_tracking
```

This creates the `.pot` file at:

```
ckanext/api_tracking/i18n/ckanext-api-tracking.pot
```

---

## 🌍 4. Initialize a `.po` file for a language (e.g., Spanish)

```bash
pybabel init -i ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  -d ckanext/api_tracking/i18n \
  -l es
```

This generates:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po
```

---

## 📝 5. Edit the `.po` file

You can use:

- [Poedit](https://poedit.net/)
- **gettext** plugin in VS Code
- Or any plain text editor

Translate each `msgid` by filling in its `msgstr`.

---

## 🔄 6. Update translations after changes

If you modify strings or templates, re-run extract and then update:

```bash
pybabel extract -F babel.cfg \
  -o ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  ckanext/api_tracking

pybabel update -i ckanext/api_tracking/i18n/ckanext-api-tracking.pot \
  -d ckanext/api_tracking/i18n \
  -l es
```

---

## ✅ 7. Compile the `.mo` file

```bash
pybabel compile -d ckanext/api_tracking/i18n
```

This creates:

```
ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.mo
```

---

## 📤 8. Copy files to your local machine (optional)

Identify the container:

```bash
docker ps
```

Then copy:

```bash
docker cp <container>:/app/src_extensions/ckanext-api-tracking/ckanext/api_tracking/i18n/es/LC_MESSAGES/ckanext-api-tracking.po .
docker cp <container>:/app/src_extensions/ckanext-api-tracking/ckanext/api_tracking/i18n/ckanext-api-tracking.pot .
```

---

## 🧾 Notes

- The `-l` flag is mandatory for both `init` and `update`.
- Ensure `babel` and localization dependencies are installed in your virtual environment.
- The `babel.cfg` file defines extractors and options (keywords, template paths).
