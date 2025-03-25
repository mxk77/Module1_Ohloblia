import streamlit as st
import requests
import re
import json
from collections import OrderedDict

def get_wiktionary_synonyms(word, lang='uk'):
    """Отримання синонімів з Wiktionary"""
    try:
        # Конвертуємо слово до нижнього регістру для пошуку
        search_word = word.lower()
        url = "https://en.wiktionary.org/w/api.php"
        params = {
            "action": "parse",
            "page": search_word,
            "format": "json",
            "prop": "wikitext",
            "section": 1
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        wikitext = data.get("parse", {}).get("wikitext", {}).get("*", "")
        
        synonyms = []
        syn_pattern = re.compile(r'\{\{syn\|' + lang + r'\|([^}]+)\}\}')
        matches = syn_pattern.findall(wikitext)
        
        for match in matches:
            synonyms.extend([x.strip() for x in match.split('|') if x.strip()])
        
        return list(OrderedDict.fromkeys(synonyms))
    except Exception as e:
        st.error(f"Помилка отримання даних з Вікісловника: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Пошук синонімів", layout="centered")
    st.title("🔍 Пошук синонімів")
    
    # Завантаження власного словника
    custom_dict = {}
    with st.sidebar:
        st.header("Налаштування")
        dict_file = st.file_uploader(
            "Завантажте власний словник (JSON)",
            type=["json"],
            help="Приклад: {'слово': ['синонім1', 'синонім2']}"
        )
        if dict_file:
            try:
                custom_dict = json.load(dict_file)
                st.success(f"Завантажено {len(custom_dict)} записів!")
            except Exception as e:
                st.error(f"Помилка завантаження файлу: {str(e)}")

    # Головний інтерфейс з підтримкою Enter
    word = st.text_input(
        "Введіть одне слово:",
        "",
        key="search_input",
        help="Натисніть Enter для пошуку",
        placeholder="наприклад: \"гарний\""
    ).strip()

    # Обробка пошуку при натиску кнопки або Enter
    if st.button("Пошук") or st.session_state.get("search_input"):
        # Валідація введення
        if not word:
            st.error("Будь ласка, введіть слово!")
            return
        if len(word.split()) > 1:
            st.error("Введіть тільки одне слово без пробілів!")
            return

        # Нормалізація слова
        original_word = word
        search_word = word.lower()
        
        # Зберігаємо синоніми за джерелами
        synonyms = {
            "custom": [],
            "wiktionary": []
        }

        # Пошук у власному словнику
        if custom_dict:
            custom_synonyms = custom_dict.get(search_word, [])
            if custom_synonyms:
                synonyms["custom"] = custom_synonyms

        # Пошук у Вікісловнику
        wiki_synonyms = get_wiktionary_synonyms(search_word)
        if wiki_synonyms:
            synonyms["wiktionary"] = wiki_synonyms

        # Відображення результатів
        total_found = sum(len(v) for v in synonyms.values())
        if total_found > 0:
            st.success(f"Знайдено {total_found} синонімів для слова '{original_word}':")
            
            # Відображення груп
            if synonyms["custom"]:
                with st.expander(f"🔖 З власного словника ({len(synonyms['custom'])})"):
                    st.write(", ".join(synonyms["custom"]))
            
            if synonyms["wiktionary"]:
                with st.expander(f"🌐 З Вікісловника ({len(synonyms['wiktionary'])})"):
                    st.write(", ".join(synonyms["wiktionary"]))

            # Експорт результатів
            export_data = "\n".join(
                [f"{source}: {', '.join(words)}" 
                 for source, words in synonyms.items() if words]
            )
            st.download_button(
                label="Завантажити всі синоніми",
                data=export_data,
                file_name=f"синоніми_{search_word}.txt",
                mime="text/plain"
            )
        else:
            st.warning("Синоніми не знайдені в обраних джерелах.")

if __name__ == "__main__":
    main()