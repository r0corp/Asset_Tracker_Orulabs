# Translations

This app uses [Flask-Babel](https://python-babel.github.io/flask-babel/) for
multi-language support. English (`en`) is the default language; Indonesian
(`id`) is the second supported language.

## How it works

- Wrap any user-facing text in templates with `{{ _('Text here') }}`.
- Wrap any user-facing text in Python (flash messages, etc.) with
  `from flask_babel import gettext as _` then `_("Text here")`.
- For strings that must be translated outside of a request context (e.g.
  `login_manager.login_message`, set once at app startup), use
  `lazy_gettext` instead of `gettext`.
- Sidebar menu labels are stored as data in the `menu_items` table
  (`Manajemen Menu` / `Menu`), not template literals, so they don't get
  picked up automatically by `pybabel extract`. When you rename a menu
  label or add a new one, add a matching `msgid`/`msgstr` pair by hand to
  each `.po` file (see `translate_catalog.py` at the project root for the
  pattern already used for the built-in menu items).

## Adding a new language

1. Add the language to `config.py`:
   ```python
   LANGUAGES = {
       "en": ("English", "\U0001F1EC\U0001F1E7"),
       "id": ("Bahasa Indonesia", "\U0001F1EE\U0001F1E9"),
       "fr": ("Français", "\U0001F1EB\U0001F1F7"),  # example
   }
   ```
   The second value is the flag emoji shown in the header dropdown.

2. Initialize the catalog for the new language:
   ```bash
   pybabel init -i messages.pot -d app/translations -l fr
   ```

3. Fill in the `msgstr` values in
   `app/translations/fr/LC_MESSAGES/messages.po` (a plain text file - any
   text editor, or a tool like Poedit, works).

4. Compile:
   ```bash
   pybabel compile -d app/translations
   ```

5. Restart the app. The new language appears automatically in the header
   dropdown - no other code changes needed.

## After adding/changing translatable strings in code

```bash
# 1. Re-scan the codebase for {{ _('...') }} / _("...") calls
pybabel extract -F babel.cfg -o messages.pot app

# 2. Merge the new/changed strings into each language's .po file
#    (keeps existing translations, marks new ones for translation)
pybabel update -i messages.pot -d app/translations

# 3. Translate the new entries in each .po file, then compile
pybabel compile -d app/translations
```

## Current coverage

As of this writing, essentially the entire app is fully translated
(EN/ID): the app shell (sidebar, header, footer, language switcher,
dark/light mode toggle), login page, dashboard (`/dashboard`), the
"Asset" home page (`index.html`, served at `/`), user profile, Master
Data (Categories, Locations, Departments, Vendors), the full Asset
module (list, detail, add/edit forms, import/import result, QR/label
printing), the full Movement module (report, per-asset history/list,
global list, add/correct forms, detail/QR/verification/correction
pages, including the public no-login verification page), Warranty
(dashboard, alerts, notifications, per-asset history), Company data,
User management, Role management (including the CRUD permission
matrix and Excel import), Menu management, Backup/Restore, Audit Log,
and Clear Cache — including their flash messages. Data values (asset
names, user-entered free text, audit log descriptions, Excel column
headers used by the import parser) are intentionally left untranslated
since they are not UI chrome. Any newly added page should follow the
same `{{ _('...') }}` pattern.
