import streamlit as st
import pandas as pd
import re
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON

# Konfigurasi halaman
st.set_page_config(
    page_title="Pencarian Naskah Jawa",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS dari file eksternal
def load_css():
    css_file = Path("styles.css")
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("File styles.css tidak ditemukan. Pastikan file CSS ada di direktori yang sama.")

# Load data from GraphDB
@st.cache_data # Cache data untuk performa
def load_data_from_graphdb():
    # Ganti dengan URL endpoint GraphDB Anda
    sparql_endpoint = "http://854f-103-125-116-42.ngrok-free.app/repositories/AksaraJawa"
    sparql = SPARQLWrapper(sparql_endpoint)

    # SPARQL query untuk mengambil semua data Paragraf dan Kata
    # Memastikan semua properti yang relevan diambil
    query = """
    PREFIX ex: <http://example.org/pupuh#>
    SELECT ?s ?type ?isiLatin ?isiAksaraJawa ?arti ?munculDalamParagraf
    WHERE {
        {
            ?s a ex:Paragraf .
            OPTIONAL { ?s ex:isiLatin ?isiLatin . }
            OPTIONAL { ?s ex:isiAksaraJawa ?isiAksaraJawa . }
            OPTIONAL { ?s ex:arti ?arti . }
            BIND("Paragraf" AS ?type)
        } UNION {
            ?s a ex:Kata .
            OPTIONAL { ?s ex:latin ?isiLatin . }
            OPTIONAL { ?s ex:aksaraJawa ?isiAksaraJawa . }
            OPTIONAL { ?s ex:arti ?arti . }
            OPTIONAL { ?s ex:munculDalamParagraf ?munculDalamParagrafUri .
                       BIND(STRAFTER(STR(?munculDalamParagrafUri), "http://example.org/pupuh#") AS ?munculDalamParagraf) }
            BIND("Kata" AS ?type)
        }
    }
    """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        data = []
        for result in results["results"]["bindings"]:
            row = {
                "s": result["s"]["value"], # URI dari entitas
                "type": result["type"]["value"],
                "isiLatin": result["isiLatin"]["value"] if "isiLatin" in result else None,
                "isiAksaraJawa": result["isiAksaraJawa"]["value"] if "isiAksaraJawa" in result else None,
                "arti": result["arti"]["value"] if "arti" in result else None,
                "munculDalamParagraf": result["munculDalamParagraf"]["value"] if "munculDalamParagraf" in result else None
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        st.error(f"Error loading data from GraphDB: {str(e)}")
        st.info("Pastikan GraphDB berjalan dan dapat diakses dari aplikasi ini.")
        return pd.DataFrame()

# Fungsi untuk mendapatkan karakter aksara Jawa unik dari dataset
@st.cache_data
def get_unique_javanese_chars(df):
    """Ekstrak karakter aksara Jawa unik dari dataset"""
    if df.empty or 'isiAksaraJawa' not in df.columns:
        sample_text = """꧋ꦥꦸꦤꦶꦏ‌ꦱꦼꦂꦫꦠ꧀‌ꦏꦒꦸꦁꦔꦤ꧀ꦤꦶꦥꦸꦤ꧀ꦚꦚꦃ​ꦱꦏꦺꦧꦼꦂ‌​ꦲꦶꦁ​ꦱꦸꦫꦥꦿꦶꦁꦒ꧋
꧁ꦥꦸꦃꦠꦼꦩ꧀ꦧꦁ​ꦲꦱ꧀ꦩꦫꦢꦺꦴꦤ꧂
꧃ꦠꦠ꧀ꦏꦭꦮꦶꦮꦶꦠ꧀ꦠꦶꦤꦸꦭꦶꦱ꧀ꦲꦶꦁ​ꦢꦶꦠꦼꦤ꧀꧈​ꦔꦲꦢ꧀ꦥꦸꦤꦶꦏ​ꦥꦸꦏꦸꦭ꧀ꦱꦥ꧀ꦠ​ꦲꦶꦁ​ဝꦪꦃꦲꦺ꧈​ꦏဝꦤ꧀ꦭꦶꦏꦸꦂ​ꦲꦶꦁ​ꦏꦁ​ꦠꦁ​ꦒꦭ꧀​ꦤꦼꦁ​ꦒꦶꦃ​ꦲꦶꦁ​ꦯꦯꦶ​​ꦱꦥꦂ꧈​ꦠꦲꦸꦤ꧀ꦤꦭꦶꦥ꧀ꦢꦸꦏ꧀ꦠꦶꦤꦸꦫꦸꦤ꧀​​ꦗꦼꦗꦼꦒꦶꦁ​ꦩꦺꦴꦁ​ꦱ​ꦏꦠꦶꦒ꧉"""
        
        all_chars = set()
        for char in sample_text:
            # Filter hanya karakter aksara Jawa (Unicode range: U+A980-U+A9DF)
            if '\ua980' <= char <= '\ua9df':
                all_chars.add(char)
        
        return sorted(list(all_chars))
    
    # Kumpulkan semua karakter dari kolom aksara Jawa
    all_chars = set()
    for text in df['isiAksaraJawa'].dropna():
        for char in str(text):
            # Filter hanya karakter aksara Jawa (Unicode range: U+A980-U+A9DF)
            if '\ua980' <= char <= '\ua9df':
                all_chars.add(char)
    
    # Urutkan karakter
    sorted_chars = sorted(list(all_chars))
    return sorted_chars

# Fungsi pencarian dengan presisi tinggi dan word boundary yang tepat
def search_text(df, query, search_type="all"):
    if df.empty or not query.strip():
        return pd.DataFrame(), {}
    
    query = query.strip()
    results = pd.DataFrame()
    
    # Cek apakah query adalah aksara Jawa
    is_javanese_query = any('\ua980' <= char <= '\ua9df' for char in query)
    
    if search_type in ["all", "latin"]:
        # Pencarian presisi dalam kolom isiLatin dengan word boundary ketat
        if is_javanese_query:
            # Jika query aksara Jawa, skip pencarian latin
            pass
        else:
            # Gunakan word boundary yang ketat untuk Latin
            # \b untuk word boundary standar, ditambah pengecekan spasi dan tanda baca
            pattern = rf'(?:^|[\s\-.,;:!?()[\]{{}}"\'/\\]){re.escape(query.lower())}(?=[\s\-.,;:!?()[\]{{}}"\'/\\]|$)'
            latin_matches = df[df['isiLatin'].astype(str).str.contains(pattern, case=False, na=False, regex=True)]
            results = pd.concat([results, latin_matches], ignore_index=True)
    
    if search_type in ["all", "translation"]:
        # Pencarian presisi dalam kolom arti dengan word boundary ketat
        if is_javanese_query:
            # Jika query aksara Jawa, skip pencarian terjemahan
            pass
        else:
            pattern = rf'(?:^|[\s\-.,;:!?()[\]{{}}"\'/\\]){re.escape(query.lower())}(?=[\s\-.,;:!?()[\]{{}}"\'/\\]|$)'
            translation_matches = df[df['arti'].astype(str).str.contains(pattern, case=False, na=False, regex=True)]
            results = pd.concat([results, translation_matches], ignore_index=True)
    
    if search_type in ["all", "javanese"]:
        # Pencarian dalam kolom isiAksaraJawa dengan exact matching yang lebih presisi
        if is_javanese_query:
            # Untuk aksara Jawa, gunakan exact match dengan word boundary aksara Jawa
            # Aksara Jawa memiliki pemisah kata yang berbeda (spasi, tanda baca Jawa)
            javanese_separators = r'[\s\u00A0\u2000-\u200F\u2028\u2029\uA9C1-\uA9CD\uA9CF-\uA9D9\uA9DE\uA9DF]'
            pattern = rf'(?:^|{javanese_separators}){re.escape(query)}(?={javanese_separators}|$)'
            exact_matches = df[df['isiAksaraJawa'].astype(str).str.contains(pattern, na=False, regex=True)]
            results = pd.concat([results, exact_matches], ignore_index=True)
        else:
            # Jika query bukan aksara Jawa, skip pencarian aksara Jawa atau cari transliterasi
            pass
    
    # Hapus duplikat berdasarkan URI unik
    results = results.drop_duplicates(subset=['s']).reset_index(drop=True)
    
    # Group results by their content (e.g., all "pada" words together)
    grouped_by_content = group_results_by_content(results, query)

    # Restructure results into top-level Kata and Paragraf groups
    final_grouped_results = restructure_results_for_display(grouped_by_content, query)
    
    return results, final_grouped_results

# New: Function to group results by content for 'Kata' and by context for 'Paragraf'
def group_results_by_content(df, query):
    if df.empty:
        return {}
    
    grouped = {}
    query_lower = query.lower()
    is_javanese_query = any('\ua980' <= char <= '\ua9df' for char in query)

    def is_exact_word_match(text, query_term, is_javanese=False):
        if pd.isna(text) or not text.strip():
            return False
        text_str = str(text)
        if is_javanese:
            javanese_separators = r'[\s\u00A0\u2000-\u200F\u2028\u2029\uA9C1-\uA9CD\uA9CF-\uA9D9\uA9DE\uA9DF]'
            pattern = rf'(?:^|{javanese_separators}){re.escape(query_term)}(?={javanese_separators}|$)'
            return bool(re.search(pattern, text_str))
        else:
            pattern = rf'(?:^|[\s\-.,;:!?()[\]{{}}"\'/\\]){re.escape(query_term.lower())}(?=[\s\-.,;:!?()[\]{{}}"\'/\\]|$)'
            return bool(re.search(pattern, text_str.lower()))

    for idx, row in df.iterrows():
        s_uri = row['s']
        isi_latin = row['isiLatin'] if pd.notna(row['isiLatin']) else ''
        arti = row['arti'] if pd.notna(row['arti']) else ''
        isi_aksara_jawa = row['isiAksaraJawa'] if pd.notna(row['isiAksaraJawa']) else ''
        
        is_latin_exact_match = is_exact_word_match(isi_latin, query, False) if not is_javanese_query else False
        is_javanese_exact_match = is_exact_word_match(isi_aksara_jawa, query, True) if is_javanese_query else False
        
        # Determine the key for this level of grouping
        current_group_key = ""
        
        if row['type'] == 'Kata' and (is_latin_exact_match or is_javanese_exact_match):
            current_group_key = f"Kata: '{query}'"
            main_word = query
            # If this is the first time we see this exact word as a main group, grab its Javanese/Translation
            if current_group_key not in grouped:
                main_javanese = isi_aksara_jawa if pd.notna(isi_aksara_jawa) else ""
                main_translation = arti if pd.notna(arti) else ""
            else:
                main_javanese = grouped[current_group_key]['main_javanese']
                main_translation = grouped[current_group_key]['main_translation']

        elif row['type'] == 'Paragraf':
            paragraph_id = s_uri.split('#')[-1] if pd.notna(s_uri) else 'Unknown_Paragraf'
            current_group_key = f"Paragraf: {paragraph_id} - Mengandung '{query}'"
            main_word = f"Mencari: {query}"
            main_javanese = extract_javanese_context(isi_aksara_jawa, query, 100)
            main_translation = extract_translation_context(arti, query, 100)

        elif row['type'] == 'Kata': # Substring match for Kata, or translation match
            current_group_key = f"Kata: '{isi_latin}' ({isi_aksara_jawa}) - Mengandung '{query}'"
            main_word = isi_latin
            main_javanese = isi_aksara_jawa
            main_translation = arti
        
        if current_group_key not in grouped:
            grouped[current_group_key] = {
                'main_word': main_word,
                'main_javanese': main_javanese,
                'main_translation': main_translation,
                'occurrences': [],
                'total_count': 0,
                'type': row['type'] # Keep track of original type for restructuring
            }
        
        occurrence_detail = {
            's_uri': s_uri, # Keep URI for uniqueness within occurrence list if needed later
            'type': row['type'],
            'javanese': isi_aksara_jawa,
            'latin': isi_latin,
            'translation': arti,
            'paragraph_reference': get_paragraph_reference(row),
            'found_in': {
                'latin': is_latin_exact_match, # still refer to exact word match
                'translation': is_exact_word_match(arti, query, False) if not is_javanese_query else False,
                'javanese': is_javanese_exact_match
            }
        }
        grouped[current_group_key]['occurrences'].append(occurrence_detail)
        grouped[current_group_key]['total_count'] += 1
    
    return grouped

# New: Function to restructure results for top-level Kata and Paragraf groups
def restructure_results_for_display(grouped_by_content, query):
    final_grouped_results = {
        "Kata": {
            "label": "Kata",
            "main_word": query, # Representative for the overall word group
            "sub_groups": {},
            "total_occurrences": 0
        },
        "Paragraf": {
            "label": "Paragraf",
            "main_word": query, # Representative for the overall paragraph group
            "sub_groups": {},
            "total_occurrences": 0
        }
    }

    for group_key, group_data in grouped_by_content.items():
        if group_data['type'] == 'Kata':
            final_grouped_results["Kata"]["sub_groups"][group_key] = group_data
            final_grouped_results["Kata"]["total_occurrences"] += group_data['total_count']
        elif group_data['type'] == 'Paragraf':
            final_grouped_results["Paragraf"]["sub_groups"][group_key] = group_data
            final_grouped_results["Paragraf"]["total_occurrences"] += group_data['total_count']
    
    return final_grouped_results

# Helper functions untuk referensi yang lebih lengkap
def get_paragraph_reference(row):
    """Dapatkan referensi paragraf yang lebih detail"""
    reference_parts = []
    
    # 'munculDalamParagraf' adalah properti dari Kata ke Paragraf
    if 'munculDalamParagraf' in row and pd.notna(row['munculDalamParagraf']):
        reference_parts.append(f"Paragraf: {row['munculDalamParagraf']}")
    
    # Jika entitas itu sendiri adalah Paragraf, gunakan URI-nya
    if row['type'] == 'Paragraf' and 's' in row and pd.notna(row['s']):
        paragraph_id = row['s'].split('#')[-1] # Ambil bagian setelah '#'
        if not reference_parts: # Hanya tambahkan jika belum ada referensi paragraf
            reference_parts.append(f"Paragraf: {paragraph_id}")
    
    return " | ".join(reference_parts) if reference_parts else "Referensi tidak tersedia"

# Helper functions for context extraction
def extract_javanese_context(text, query, context_length=50):
    if not text or not query:
        return text
    
    # Untuk aksara Jawa, ambil konteks di sekitar query
    try:
        pattern = rf'{re.escape(query)}'
        match = re.search(pattern, text)
        if match:
            start_idx = match.start()
            start = max(0, start_idx - context_length)
            end = min(len(text), start_idx + len(query) + context_length)
            context = text[start:end]
            # Tambahkan ellipsis jika terpotong
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."
            return context
    except:
        pass
    return text

def extract_translation_context(text, query, context_length=100):
    if not text or not query:
        return text
    
    try:
        # Gunakan pattern yang sama dengan pencarian utama
        pattern = rf'(?:^|[\s\-.,;:!?()[\]{{}}"\'/\\]){re.escape(query.lower())}(?=[\s\-.,;:!?()[\]{{}}"\'/\\]|$)'
        match = re.search(pattern, text.lower())
        if match:
            start_idx = match.start()
            start = max(0, start_idx - context_length)
            end = min(len(text), start_idx + len(query) + context_length)
            context = text[start:end]
            # Tambahkan ellipsis jika terpotong
            if start > 0:
                context = "..." + context
            if end < len(text):
                context = context + "..."
            return context
    except Exception as e:
        # Fallback if regex fails, return original text
        return text
    
    return text

# Fungsi untuk highlight text dengan word boundary yang presisi
def highlight_text(text, query):
    if not text or not query:
        return text
    
    # Escape HTML special characters
    import html
    text_escaped = html.escape(str(text))
    query_escaped = html.escape(str(query))
    
    try:
        # Cek apakah query adalah Aksara Jawa (berisi karakter Unicode Javanese)
        is_javanese_query = any('\ua980' <= char <= '\ua9df' for char in query)

        if is_javanese_query:
            # Untuk Aksara Jawa, gunakan word boundary aksara Jawa
            javanese_separators = r'[\s\u00A0\u2000-\u200F\u2028\u2029\uA9C1-\uA9CD\uA9CF-\uA9D9\uA9DE\uA9DF]'
            pattern = rf'(?:^|({javanese_separators}))({re.escape(query)})(?=({javanese_separators})|$)'
            highlighted = re.sub(pattern, r'\1<span class="highlighted-text">\2</span>\3', text_escaped)
        else:
            # Untuk Latin/Terjemahan, gunakan word boundary yang ketat
            pattern = rf'(?:^|([\s\-.,;:!?()[\]{{}}"\'/\\]))({re.escape(query)})(?=([\s\-.,;:!?()[\]{{}}"\'/\\])|$)'
            highlighted = re.sub(pattern, r'\1<span class="highlighted-text">\2</span>\3', text_escaped, flags=re.IGNORECASE)
        
        return highlighted
    except Exception as e:
        # Fallback jika regex gagal
        st.warning(f"Highlighting error: {e}. Falling back to simple replace.")
        return text_escaped.replace(query_escaped, f'<span class="highlighted-text">{query_escaped}</span>')

# Keyboard aksara Jawa berdasarkan dataset
def create_javanese_keyboard(df):
    """Membuat keyboard aksara Jawa dengan layout profesional seperti foto"""
    
    # Dapatkan karakter aksara Jawa unik dari dataset
    javanese_chars = get_unique_javanese_chars(df)
    
    if not javanese_chars:
        st.info("Tidak ada karakter aksara Jawa ditemukan dalam dataset.")
        return
    
    # Header keyboard
    st.markdown("""
    <div class="keyboard-header-container">
        <h3 class="keyboard-header-title">⌨ Keyboard Aksara Jawa</h3>
        <p class="keyboard-header-subtitle">Tersedia {0} karakter unik dari dataset</p>
    </div>
    """.format(len(javanese_chars)), unsafe_allow_html=True)
    
    # Kelompokkan karakter berdasarkan fungsi dengan definisi yang lebih spesifik
    consonants = []
    vowel_marks = []
    punctuation = []
    others = []
    
    # Definisi range yang lebih tepat berdasarkan Unicode Javanese block
    for char in javanese_chars:
        char_code = ord(char)
        # Aksara dasar (Ha, Na, Ca, Ra, Ka, dst)
        if 0xA980 <= char_code <= 0xA9B2:
            consonants.append(char)
        # Sandhangan vokal (wulu, suku, taling, dst)
        elif 0xA9B3 <= char_code <= 0xA9C0:
            vowel_marks.append(char)
        # Tanda baca dan simbol
        elif char_code >= 0xA9C1:
            punctuation.append(char)
        else:
            others.append(char)
    
    # 1. Section Aksara Dasar (bagian paling besar)
    if consonants:
        st.markdown("""
        <div class="keyboard-section-card">
            <h4 class="keyboard-section-heading">Aksara Dasar</h4>
        """, unsafe_allow_html=True)
        
        # Grid untuk aksara dasar dengan spacing yang konsisten
        chars_per_row = 10
        rows = [consonants[i:i + chars_per_row] for i in range(0, len(consonants), chars_per_row)]
        
        for row_idx, char_row in enumerate(rows):
            cols = st.columns(len(char_row))
            for col_idx, char in enumerate(char_row):
                with cols[col_idx]:
                    if st.button(
                        char, 
                        key=f"cons_{row_idx}_{col_idx}",
                        help=f"Tambahkan {char} (U+{ord(char):04X})",
                        use_container_width=True
                    ):
                        if 'search_query' not in st.session_state:
                            st.session_state.search_query = ""
                        st.session_state.search_query += char
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Layout 2x2 untuk section lainnya
    col1, col2 = st.columns(2, gap="large")
    
    # 2. Section Sandhangan Vokal
    with col1:
        if vowel_marks:
            st.markdown("""
            <div class="keyboard-section-card">
                <h4 class="keyboard-section-heading">Sandhangan Vokal</h4>
            """, unsafe_allow_html=True)
            
            chars_per_row = 5
            rows = [vowel_marks[i:i + chars_per_row] for i in range(0, len(vowel_marks), chars_per_row)]
            
            for row_idx, char_row in enumerate(rows):
                cols_inner = st.columns(len(char_row))
                for col_idx, char in enumerate(char_row):
                    with cols_inner[col_idx]:
                        if st.button(
                            char, 
                            key=f"vowel_{row_idx}_{col_idx}",
                            help=f"Tambahkan {char} (U+{ord(char):04X})",
                            use_container_width=True
                        ):
                            if 'search_query' not in st.session_state:
                                st.session_state.search_query = ""
                            st.session_state.search_query += char
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 3. Section Tanda Baca & Simbol
    with col2:
        if punctuation:
            st.markdown("""
            <div class="keyboard-section-card">
                <h4 class="keyboard-section-heading">Tanda Baca & Simbol</h4>
            """, unsafe_allow_html=True)
            
            chars_per_row = 5
            rows = [punctuation[i:i + chars_per_row] for i in range(0, len(punctuation), chars_per_row)]
            
            for row_idx, char_row in enumerate(rows):
                cols_inner = st.columns(len(char_row))
                for col_idx, char in enumerate(char_row):
                    with cols_inner[col_idx]:
                        if st.button(
                            char, 
                            key=f"punct_{row_idx}_{col_idx}",
                            help=f"Tambahkan {char} (U+{ord(char):04X})",
                            use_container_width=True
                        ):
                            if 'search_query' not in st.session_state:
                                st.session_state.search_query = ""
                            st.session_state.search_query += char
                            st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Section Karakter Lainnya (jika ada)
    if others:
        st.markdown("""
        <div class="keyboard-section-card">
            <h4 class="keyboard-section-heading">Karakter Lainnya</h4>
        """, unsafe_allow_html=True)
        
        chars_per_row = 8
        rows = [others[i:i + chars_per_row] for i in range(0, len(others), chars_per_row)]
        
        for row_idx, char_row in enumerate(rows):
            cols = st.columns(len(char_row))
            for col_idx, char in enumerate(char_row):
                with cols[col_idx]:
                    if st.button(
                        char, 
                        key=f"other_{row_idx}_{col_idx}",
                        help=f"Tambahkan {char} (U+{ord(char):04X})",
                        use_container_width=True
                    ):
                        if 'search_query' not in st.session_state:
                            st.session_state.search_query = ""
                        st.session_state.search_query += char
                        st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Kontrol keyboard (Hanya tombol Hapus Karakter Terakhir)
    st.markdown("""
    <div class="keyboard-controls-container">
    """, unsafe_allow_html=True)
    
    # Hanya satu kolom untuk tombol "Hapus Karakter Terakhir"
    col1, col2, col3 = st.columns([1,2,1]) # Menggunakan 3 kolom untuk centering
    
    with col2: # Menempatkan tombol di kolom tengah
        if st.button("⌫ Hapus Karakter Terakhir", help="Hapus satu karakter terakhir", use_container_width=True, key="keyboard_delete_button"):
            if 'search_query' in st.session_state and st.session_state.search_query:
                st.session_state.search_query = st.session_state.search_query[:-1]
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# Fungsi untuk menampilkan hasil pencarian dengan format yang lebih baik
def display_search_results(final_grouped_results, query):
    total_results_found = False
    for group_type, data in final_grouped_results.items():
        if data["total_occurrences"] > 0:
            total_results_found = True
            break
    
    if not total_results_found:
        st.info("🔍 Tidak ada hasil ditemukan untuk pencarian tersebut.")
        return
    
    # Header hasil
    total_kata_occurrences = final_grouped_results["Kata"]["total_occurrences"]
    total_paragraf_occurrences = final_grouped_results["Paragraf"]["total_occurrences"]
    
    st.markdown(f"""
    <div class="search-results-summary">
        <h2 class="search-results-summary-title">📝 Hasil Pencarian</h2>
        <p class="search-results-summary-text">
            Ditemukan <strong>{total_kata_occurrences + total_paragraf_occurrences}</strong> kemunculan untuk "<em>{query}</em>"
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tampilkan top-level groups (Kata and Paragraf)
    for group_type, group_data in final_grouped_results.items():
        if group_data["total_occurrences"] > 0:
            with st.expander(f"📑 {group_data['label']} ({group_data['total_occurrences']} kemunculan)", expanded=True):
                
                # Sort sub_groups alphabetically by key for consistent display
                sorted_sub_groups = sorted(group_data['sub_groups'].items())

                for sub_group_key, sub_group_data in sorted_sub_groups:
                    st.markdown(f"#### {sub_group_key} (Total: {sub_group_data['total_count']})")
                    
                    # Information about the main matched item for this sub-group
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(f"""
                        <div class="group-info-card">
                            <h4 class="group-info-title">Informasi Utama</h4>
                            <p class="group-info-item"><strong>Kata/Frasa:</strong> {sub_group_data['main_word']}</p>
                            <p class="group-info-item"><strong>Aksara Jawa:</strong> <span class="javanese-content">{sub_group_data['main_javanese']}</span></p>
                            <p class="group-info-item"><strong>Arti:</strong> {sub_group_data['main_translation']} </p>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.metric("Kemunculan Sub-Grup", sub_group_data['total_count'])

                    st.markdown("##### 💾 Detail Setiap Kemunculan:")
                    
                    # Display individual occurrences within the sub-group
                    for occ_idx, occurrence in enumerate(sub_group_data['occurrences'], 1):
                        type_tag_class = "type-tag-kata" if occurrence['type'] == 'Kata' else "type-tag-paragraf"
                        
                        st.markdown(f"""
                        <div class="occurrence-card">
                            <div class="occurrence-header">
                                <span class="type-tag-base {type_tag_class}">{occurrence['type']}</span>
                                <span class="occurrence-reference">{occurrence['paragraph_reference']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        if occurrence['javanese']:
                            highlighted_javanese = highlight_text(occurrence['javanese'], query)
                            st.markdown(f"""
                            <div class="occurrence-text-block">
                                <strong class="occurrence-text-label">Aksara Jawa:</strong><br>
                                <span class="javanese-content">
                                    {highlighted_javanese}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if occurrence['latin']:
                            highlighted_latin = highlight_text(occurrence['latin'], query)
                            st.markdown(f"""
                            <div class="occurrence-text-block">
                                <strong class="occurrence-text-label">Latin:</strong><br>
                                <span class="latin-content">
                                    {highlighted_latin}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if occurrence['translation']:
                            highlighted_translation = highlight_text(occurrence['translation'], query)
                            st.markdown(f"""
                            <div class="occurrence-text-block">
                                <strong class="occurrence-text-label">Terjemahan:</strong><br>
                                <span class="translation-content">
                                    {highlighted_translation}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        found_in_indicators = []
                        if occurrence['found_in']['javanese']:
                            found_in_indicators.append("🔸 Aksara Jawa")
                        if occurrence['found_in']['latin']:
                            found_in_indicators.append("🔹 Latin")
                        if occurrence['found_in']['translation']:
                            found_in_indicators.append("🔺 Terjemahan")
                        
                        if found_in_indicators:
                            st.markdown(f"""
                            <div class="found-in-footer">
                                <small class="found-in-text">
                                    <strong>Ditemukan dalam:</strong> {' | '.join(found_in_indicators)}
                                </small>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.markdown("---") # Separator between occurrences
    
    if total_results_found:
        st.info(f"💡 Tips: Hasil yang ditampilkan disorot secara otomatis.")


# Main application
def main():
    # Load CSS
    load_css()
    
    # Header aplikasi
    st.markdown("""
    <div class="app-main-header-container">
        <h1 class="app-main-header-title">📜 Pencarian Naskah Jawa</h1>
        <p class="app-main-header-subtitle">Sistem Pencarian Presisi untuk Teks Aksara Jawa dari GraphDB</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    with st.spinner("🔄 Memuat data dari GraphDB..."):
        df = load_data_from_graphdb()
    
    if df.empty:
        st.error("❌ Tidak dapat memuat data dari GraphDB. Pastikan GraphDB berjalan dan dapat diakses.")
        st.info("""
        Panduan Troubleshooting:
        1. Pastikan GraphDB berjalan di http://854f-103-125-116-42.ngrok-free.app/repositories/AksaraJawa
        2. Pastikan repository 'AksaraJawa' sudah dibuat dan berisi data
        3. Pastikan tidak ada firewall yang memblokir koneksi
        4. Cek apakah SPARQLWrapper terinstal: pip install SPARQLWrapper
        """)
        return
    
    # Info dataset
    st.success(f"✅ Berhasil memuat {len(df)} entri dari GraphDB")
    
    # Tabs untuk organisasi fitur
    tab1, tab2 = st.tabs(["🔍 Pencarian", "📊 Dataset"]) # Removed Keyboard tab
    
    with tab1:
        # Input pencarian dengan session state
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        
        # Search interface
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "🔍 Masukkan kata atau frasa yang ingin dicari:",
                value=st.session_state.search_query,
                placeholder="Contoh: punika, ꦥꦸꦤꦶꦏ, atau sebuah kata dalam bahasa Indonesia",
                help="Gunakan keyboard aksara Jawa di bawah untuk input aksara Jawa",
                key="search_input"
            )
            
            # Update session state jika input berubah
            if search_query != st.session_state.search_query:
                st.session_state.search_query = search_query
        
        with col2:
            search_type = st.selectbox(
                "Cari dalam:",
                ["all", "latin", "javanese", "translation"],
                format_func=lambda x: {
                    "all": "🌍 Semua",
                    "latin": "🔤 Latin",
                    "javanese": "✒️ Aksara Jawa",
                    "translation": "🇮🇩 Terjemahan"
                }[x],
                help="Pilih jenis teks yang ingin dicari"
            )

        # Keyboard can be closed and opened (expand)
        with st.expander("⌨ Tampilkan/Sembunyikan Keyboard Aksara Jawa", expanded=False):
            # Display current search query (moved from original tab2)
            if 'search_query' in st.session_state and st.session_state.search_query:
                st.markdown(f"""
                <div class="current-query-display">
                    <h4 class="current-query-label">Teks Pencarian Saat Ini:</h4>
                    <div class="current-query-text">{st.session_state.search_query}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Keyboard (moved from original tab2)
            create_javanese_keyboard(df)

        # Tombol pencarian dan kontrol
        st.markdown("---") # Separator before action buttons
        col_btn1, col_btn2, col_btn3 = st.columns([2, 2, 2])
        
        with col_btn1:
            search_button = st.button("🔍 Cari", type="primary", use_container_width=True)
        
        with col_btn2:
            if st.button("🗑️ Bersihkan", use_container_width=True):
                st.session_state.search_query = ""
                st.rerun()
        
        with col_btn3:
            if st.button("📤 Contoh Pencarian", use_container_width=True):
                # Pilih contoh pencarian secara acak
                examples = ["punika", "ꦥꦸꦤꦶꦏ", "adalah", "dalam", "yang"]
                import random
                st.session_state.search_query = random.choice(examples)
                st.rerun()
        
        # Lakukan pencarian
        if search_query.strip() and search_button: # Only search when button is clicked
            with st.spinner("🔎 Mencari..."):
                results_df, final_grouped_results = search_text(df, search_query, search_type)
            
            # Tampilkan hasil
            display_search_results(final_grouped_results, search_query)
            
    with tab2: # This is now the "Dataset" tab
        st.markdown("""
        <div class="app-main-header-container-2">
            <h2 class="app-main-header-title-2">📊 Dataset GraphDB - Informasi detail tentang dataset naskah Jawa</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if not df.empty:
            total_entries = len(df)
            kata_count = len(df[df['type'] == 'Kata'])
            paragraf_count = len(df[df['type'] == 'Paragraf'])
            unique_javanese_chars = len(get_unique_javanese_chars(df))

            st.markdown(f"""
            <div class="custom-info-box">
                <div style="display: flex; justify-content: flex-start; padding: 10px 20px; gap: 300px;">
                    <div>
                        <p style="margin: 0; font-size: 1.2rem; font-weight: 450;">Total Entri</p>
                        <h2 style="margin: 0; font-size: 1.2rem; font-weight: 800">{total_entries}</h2>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 1.2rem; font-weight: 450;">Jumlah Kata</p>
                        <h2 style="margin: 0; font-size: 1.2rem; font-weight: 800">{kata_count}</h2>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 1.2rem; font-weight: 450;">Jumlah Paragraf</p>
                        <h2 style="margin: 0; font-size: 1.2rem; font-weight: 800">{paragraf_count}</h2>
                    </div>
                    <div>
                        <p style="margin: 0; font-size: 1.2rem; font-weight: 450;">Karakter Aksara Jawa</p>
                        <h2 style="margin: 0; font-size: 1.2rem; font-weight: 800">{unique_javanese_chars}</h2>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
            # Info koneksi GraphDB
            st.markdown("""
            <div class="app-main-header-container-2">
                <h2 class="app-main-header-title-2">🔗 Informasi Koneksi</h2>
            </div>
            <div class="custom-info-box">
                <p><strong>Sumber Data:</strong> GraphDB Repository 'AksaraJawa'</p>
                <p><strong>Endpoint:</strong> <a href="http://854f-103-125-116-42.ngrok-free.app" target="_blank">http://854f-103-125-116-42.ngrok-free.app</a></p>
                <p><strong>Status:</strong> ✅ Terhubung dan data berhasil dimuat</p>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.warning("Tidak ada data untuk ditampilkan. Pastikan koneksi ke GraphDB berhasil.")

if __name__ == "__main__":
    main()