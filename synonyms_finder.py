import streamlit as st
import requests
import re
import json
from collections import OrderedDict

def get_wiktionary_synonyms(word, lang='uk'):
    """Get synonyms from Wiktionary"""
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
        st.error(f"Wiktionary error: {str(e)}")
        return []

def main():
    st.set_page_config(page_title="Synonym Replacer", layout="centered")
    st.title("🔍 Synonym Replacer")
    
    # Load custom dictionary
    custom_dict = {}
    with st.sidebar:
        st.header("Settings")
        dict_file = st.file_uploader(
            "Upload custom dictionary (JSON)",
            type=["json"],
            help="Example: {'word': ['synonym1', 'synonym2']}"
        )
        if dict_file:
            try:
                custom_dict = json.load(dict_file)
                st.success(f"Loaded {len(custom_dict)} entries!")
            except Exception as e:
                st.error(f"Error loading dictionary: {str(e)}")

    # Main interface
    input_text = st.text_area(
        "Enter text:",
        "",
        help="Enter text to replace words with synonyms",
        placeholder="e.g., \"A sample text to process\"",
        height=150
    )

    if st.button("Process Text"):
        if not input_text.strip():
            st.error("Please enter some text!")
            return

        # Tokenize text into words and non-words
        tokens = re.findall(r'\w+|\W+', input_text)
        modified_tokens = []
        synonym_report = {}

        for token in tokens:
            if re.match(r'^\w+$', token) and token.isalpha():
                original_word = token
                search_word = original_word.lower()

                # Get synonyms from both sources
                custom_synonyms = custom_dict.get(search_word, [])
                wiki_synonyms = get_wiktionary_synonyms(search_word)

                # Find first available synonym
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

        # Rebuild modified text
        modified_text = ''.join(modified_tokens)

        # Display results
        st.subheader("Modified Text")
        st.text_area("Result", modified_text, height=300, key="modified_text")

        # Show synonym blocks
        if synonym_report:
            st.subheader("Replaced Words")
            for word, data in synonym_report.items():
                with st.expander(f"{word} → {data['replaced_with']} ({data['source']})"):
                    if data['custom_synonyms']:
                        st.write(f"**Custom synonyms:** {', '.join(data['custom_synonyms'])}")
                    if data['wiki_synonyms']:
                        st.write(f"**Wiktionary synonyms:** {', '.join(data['wiki_synonyms'])}")
            
            # Add download button
            st.download_button(
                label="Download Modified Text",
                data=modified_text,
                file_name="synonym_replaced_text.txt",
                mime="text/plain"
            )
        else:
            st.warning("No words were replaced with synonyms.")

if __name__ == "__main__":
    main()