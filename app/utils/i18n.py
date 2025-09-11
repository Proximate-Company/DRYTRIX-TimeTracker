import os
import io
import time
from typing import Optional


def _needs_compile(po_path: str, mo_path: str) -> bool:
    try:
        if not os.path.exists(mo_path):
            return True
        return os.path.getmtime(po_path) > os.path.getmtime(mo_path)
    except Exception:
        return True


def compile_po_to_mo(po_path: str, mo_path: str) -> bool:
    """Compile a .po file to .mo using Babel's message tools if available.

    Returns True on success, False otherwise.
    """
    try:
        from babel.messages.pofile import read_po
        from babel.messages.mofile import write_mo

        with open(po_path, 'r', encoding='utf-8') as po_file:
            catalog = read_po(po_file)
        os.makedirs(os.path.dirname(mo_path), exist_ok=True)
        with open(mo_path, 'wb') as mo_file:
            write_mo(mo_file, catalog)
        return True
    except Exception:
        return False


def ensure_translations_compiled(translations_dir: str) -> None:
    """Compile all .po catalogs under translations_dir if missing/stale.

    Structure expected: translations/<lang>/LC_MESSAGES/messages.po
    """
    try:
        if not translations_dir:
            return
        if not os.path.isabs(translations_dir):
            # Resolve relative to current working directory
            translations_dir = os.path.abspath(translations_dir)
        if not os.path.isdir(translations_dir):
            return
        for lang in os.listdir(translations_dir):
            lang_dir = os.path.join(translations_dir, lang, 'LC_MESSAGES')
            if not os.path.isdir(lang_dir):
                continue
            po_path = os.path.join(lang_dir, 'messages.po')
            mo_path = os.path.join(lang_dir, 'messages.mo')
            if os.path.exists(po_path) and _needs_compile(po_path, mo_path):
                compile_po_to_mo(po_path, mo_path)
    except Exception:
        # Non-fatal; i18n will fall back to msgid if mo missing
        pass


