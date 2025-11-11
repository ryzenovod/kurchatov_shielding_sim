import os, io, json, zipfile, datetime
import streamlit as st

TEXTS = {
    "RU": {
        "title": "Экспорт / Импорт сценариев",
        "current": "Текущие сценарии",
        "export_json": "Скачать все сценарии (JSON)",
        "export_zip": "Скачать архив (ZIP)",
        "import_label": "Загрузите JSON или ZIP со сценариями",
        "import_btn": "Импортировать",
        "import_ok": "Импортировано сценариев: {n}. Конфликты: {c}.",
        "strategy": "Стратегия при совпадении имён",
        "strat_overwrite": "Перезаписывать",
        "strat_keep": "Сохранять мои",
        "strat_rename": "Переименовывать импортируемые (добавлять суффикс)"
    },
    "EN": {
        "title": "Scenarios export / import",
        "current": "Current scenarios",
        "export_json": "Download all scenarios (JSON)",
        "export_zip": "Download archive (ZIP)",
        "import_label": "Upload JSON or ZIP with scenarios",
        "import_btn": "Import",
        "import_ok": "Imported: {n}. Conflicts: {c}.",
        "strategy": "Name conflict strategy",
        "strat_overwrite": "Overwrite",
        "strat_keep": "Keep mine",
        "strat_rename": "Rename imported (suffix)"
    }
}

def T(lang, key):
    return TEXTS.get(lang, TEXTS["RU"]).get(key, key)

st.set_page_config(page_title="Scenarios I/O", layout="wide")
lang = st.sidebar.selectbox("Язык / Language", ["RU", "EN"], index=0)

st.title(T(lang, "title"))

os.makedirs("scenarios", exist_ok=True)
path = "scenarios/my_scenarios.json"
try:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    data = {}

st.subheader(T(lang, "current"))
st.json(data)

# Export buttons
buf = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
st.download_button(T(lang, "export_json"), data=buf, file_name="scenarios.json", mime="application/json")

# ZIP export
zip_buf = io.BytesIO()
with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("scenarios.json", buf)
zip_buf.seek(0)
st.download_button(T(lang, "export_zip"), data=zip_buf, file_name="scenarios.zip", mime="application/zip")

# Import
st.subheader(T(lang, "import_label"))
uploaded = st.file_uploader(" ", type=["json", "zip"])

strategy = st.selectbox(T(lang, "strategy"),
                        [T(lang, "strat_overwrite"), T(lang, "strat_keep"), T(lang, "strat_rename")],
                        index=2)

if st.button(T(lang, "import_btn")) and uploaded is not None:
    # Load incoming scenarios dict
    incoming = None
    if uploaded.type == "application/zip" or uploaded.name.lower().endswith(".zip"):
        try:
            z = zipfile.ZipFile(uploaded)
            # Take first *.json in archive
            name = next((n for n in z.namelist() if n.lower().endswith(".json")), None)
            if name:
                incoming = json.loads(z.read(name).decode("utf-8"))
        except Exception:
            st.error("ZIP read error")
    else:
        try:
            incoming = json.loads(uploaded.read().decode("utf-8"))
        except Exception:
            st.error("JSON read error")

    if isinstance(incoming, dict):
        conflicts = 0
        imported = 0
        for k, v in incoming.items():
            if k in data:
                conflicts += 1
                if strategy == T(lang, "strat_overwrite"):
                    data[k] = v
                    imported += 1
                elif strategy == T(lang, "strat_keep"):
                    continue
                else:
                    # rename
                    suffix = " (imported)"
                    new_key = k + suffix
                    idx = 1
                    while new_key in data:
                        idx += 1
                        new_key = f"{k}{suffix} {idx}"
                    data[new_key] = v
                    imported += 1
            else:
                data[k] = v
                imported += 1
        # Save back
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        st.success(T(lang, "import_ok").format(n=imported, c=conflicts))
    else:
        st.error("No scenarios found in uploaded file")
