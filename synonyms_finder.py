import streamlit as st
import requests
import re
import json
from collections import OrderedDict

def get_wiktionary_synonyms(word, lang='uk'):
    """Отримати синоніми з Wiktionary"""
    try:
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
        st.error(f"Помилка Wiktionary: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Замінник синонімів", layout="centered")
    st.title("🔍 Замінник синонімів")
    
    # Завантажити власний словник
    custom_dict = {}
    with st.sidebar:
        st.header("Налаштування ⚙️")
        dict_file = st.file_uploader(
            "Завантажити власний словник (JSON)",
            type=["json"],
            help="Приклад: {'word': ['синонім1', 'синонім2']}"
        )
        if dict_file:
            try:
                custom_dict = json.load(dict_file)
                st.success(f"Завантажено {len(custom_dict)} записів!")
            except Exception as e:
                st.error(f"Помилка завантаження словника: {str(e)}")

    # Головний інтерфейс
    input_text = st.text_area(
        "Введіть текст:",
        "",
        help="Введіть текст для заміни слів на синоніми",
        placeholder="наприклад, \"Приклад тексту для обробки\"",
        height=150
    )

    if st.button("Обробити текст"):
        if not input_text.strip():
            st.error("Будь ласка, введіть текст!")
            return

        # Токенізація тексту на слова та не-слова
        tokens = re.findall(r'\w+|\W+', input_text)
        modified_tokens = []
        synonym_report = {}

        for token in tokens:
            if re.match(r'^\w+$', token) and token.isalpha():
                original_word = token
                search_word = original_word.lower()

                # Отримати синоніми з обох джерел
                custom_synonyms = custom_dict.get(search_word, [])
                wiki_synonyms = get_wiktionary_synonyms(search_word)

                # Знайти перший доступний синонім
                first_synonym = None
                source = None
                if custom_synonyms:
                    first_synonym = custom_synonyms[0]
                    source = 'custom'
                elif wiki_synonyms:
                    first_synonym = wiki_synonyms[0]
                    source = 'wiktionary'

                if first_synonym:
                    modified_tokens.append(first_synonym)
                    synonym_report[original_word] = {
                        'replaced_with': first_synonym,
                        'custom_synonyms': custom_synonyms,
                        'wiki_synonyms': wiki_synonyms,
                        'source': source
                    }
                else:
                    modified_tokens.append(original_word)
            else:
                modified_tokens.append(token)

        # Відновити змінений текст
        modified_text = ''.join(modified_tokens)

        # Відобразити результати
        st.subheader("Змінений текст")
        st.text_area("Результат", modified_text, height=300, key="modified_text")

        # Показати блоки синонімів
        if synonym_report:
            st.subheader("Замінені слова")
            for word, data in synonym_report.items():
                source_name = "Власний" if data['source'] == 'custom' else "Wiktionary"
                with st.expander(f"{word} → {data['replaced_with']} ({source_name})"):
                    if data['custom_synonyms']:
                        st.write(f"**Користувацькі синоніми:** {', '.join(data['custom_synonyms'])}")
                    if data['wiki_synonyms']:
                        st.write(f"**Синоніми з Wiktionary:** {', '.join(data['wiki_synonyms'])}")
            
            # Додати кнопку для завантаження
            st.download_button(
                label="Завантажити змінений текст",
                data=modified_text,
                file_name="замінений_текст.txt",
                mime="text/plain"
            )
        else:
            st.warning("Жодне слово не було замінено синонімами.")

if __name__ == "__main__":
    main()