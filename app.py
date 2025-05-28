import streamlit as st
import pandas as pd
import re
from pathlib import Path
from SPARQLWrapper import SPARQLWrapper, JSON # Import SPARQLWrapper

# Konfigurasi halaman
st.set_page_config(
    page_title="Pencarian Naskah Jawa",
    page_icon="📜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load CSS
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
    sparql_endpoint = "http://LAPTOP-3RKM154R:7200/repositories/AksaraJawa"
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
        # Fallback ke karakter dari contoh yang diberikan user
        # Ini penting jika koneksi ke GraphDB gagal atau data kosong
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

# Fungsi pencarian dengan grouping dan word boundary
def search_text(df, query, search_type="all"):
    if df.empty or not query.strip():
        return pd.DataFrame(), {}
    
    query = query.strip()
    results = pd.DataFrame()
    
    if search_type in ["all", "latin"]:
        # Pencarian presisi dalam kolom isiLatin dengan word boundary
        latin_matches = df[df['isiLatin'].astype(str).str.contains(rf'\b{re.escape(query.lower())}\b', 
                                                      case=False, na=False, regex=True)]
        results = pd.concat([results, latin_matches], ignore_index=True)
    
    if search_type in ["all", "translation"]:
        # Pencarian presisi dalam kolom arti dengan word boundary
        translation_matches = df[df['arti'].astype(str).str.contains(rf'\b{re.escape(query.lower())}\b', 
                                                        case=False, na=False, regex=True)]
        results = pd.concat([results, translation_matches], ignore_index=True)
    
    if search_type in ["all", "javanese"]:
        # Pencarian dalam kolom isiAksaraJawa dengan metode yang lebih fleksibel
        # Cari exact match terlebih dahulu
        exact_matches = df[df['isiAksaraJawa'].astype(str).str.contains(re.escape(query), na=False, regex=True)]
        results = pd.concat([results, exact_matches], ignore_index=True)
        
        # Jika tidak ada exact match, coba pencarian dengan word boundary yang lebih longgar
        if exact_matches.empty:
            # Cari dengan pola yang mempertimbangkan spasi dan tanda baca aksara Jawa
            pattern = rf'{re.escape(query)}'
            loose_matches = df[df['isiAksaraJawa'].astype(str).str.contains(pattern, na=False, regex=True)]
            results = pd.concat([results, loose_matches], ignore_index=True)
    
    # Hapus duplikat
    results = results.drop_duplicates(subset=['s']).reset_index(drop=True) # Gunakan 's' (URI) untuk identifikasi unik
    
    # Group results by unique words/phrases
    grouped_results = group_search_results(results, query)
    
    return results, grouped_results

# Fungsi untuk mengelompokkan hasil pencarian
def group_search_results(df, query):
    if df.empty:
        return {}
    
    grouped = {}

    kata_results = df[df['type'] == 'Kata']
    paragraf_results = df[df['type'] == 'Paragraf']
    
    # Process 'Kata' entries first
    for idx, row in df[df['type'] == 'Kata'].iterrows():
        isi_latin = row['isiLatin'] if pd.notna(row['isiLatin']) else ''
        arti = row['arti'] if pd.notna(row['arti']) else ''
        isi_aksara_jawa = row['isiAksaraJawa'] if pd.notna(row['isiAksaraJawa']) else ''

        # Determine if this 'Kata' is an exact match for the query
        is_exact_query_match = (pd.notna(isi_latin) and isi_latin.lower() == query.lower()) or \
                               (pd.notna(isi_aksara_jawa) and isi_aksara_jawa == query)

        if is_exact_query_match:
            # If it's an exact Kata match, create a group based on the Kata itself
            group_key = f"Kata: {isi_latin} ({isi_aksara_jawa})"
            main_word = isi_latin
            main_javanese = isi_aksara_jawa
            main_translation = arti
        else:
            # If it's a 'Kata' but not an exact match to the query (e.g., query is 'ing' but 'ing' also appears in another 'Kata' like 'ingkang')
            # This case might be less common if search_text is precise, but handle it.
            group_key = f"Kata: {isi_latin} ({isi_aksara_jawa}) - Terkait '{query}'"
            main_word = isi_latin
            main_javanese = isi_aksara_jawa
            main_translation = arti

        if group_key not in grouped:
            grouped[group_key] = {
                'main_word': main_word,
                'main_javanese': main_javanese,
                'main_translation': main_translation,
                'occurrences': [],
                'total_count': 0
            }
        
        # Add the current row as an occurrence to its determined group
        occurrence = {
            'type': row['type'],
            'javanese': isi_aksara_jawa,
            'latin': isi_latin,
            'translation': arti,
            'paragraph_reference': get_paragraph_reference(row),
            'full_sentence': get_full_sentence(row),
            'source_info': get_source_info(row),
            'found_in': {
                'latin': bool(re.search(rf'\b{re.escape(query.lower())}\b', isi_latin.lower(), re.IGNORECASE)),
                'translation': bool(re.search(rf'\b{re.escape(query.lower())}\b', arti.lower(), re.IGNORECASE)),
                'javanese': bool(re.search(rf'{re.escape(query)}', isi_aksara_jawa))
            }
        }
        grouped[group_key]['occurrences'].append(occurrence)
        grouped[group_key]['total_count'] += 1

    # Process 'Paragraf' entries
    for idx, row in df[df['type'] == 'Paragraf'].iterrows():
        isi_latin = row['isiLatin'] if pd.notna(row['isiLatin']) else ''
        arti = row['arti'] if pd.notna(row['arti']) else ''
        isi_aksara_jawa = row['isiAksaraJawa'] if pd.notna(row['isiAksaraJawa']) else ''

        paragraph_id = row['s'].split('#')[-1] if pd.notna(row['s']) else 'Unknown_Paragraf'
        
        # Get a snippet of the Javanese text for the subtitle
        javanese_snippet = isi_aksara_jawa.strip()
        if len(javanese_snippet) > 70: # Adjust length as needed to fit the display
            javanese_snippet = javanese_snippet[:70] + "..."
        elif len(javanese_snippet) == 0:
            javanese_snippet = "..." # Fallback if empty
        
        # Use the paragraph ID in the group key for uniqueness
        group_key = f"Paragraf: {paragraph_id} (Query: {query})"
        main_word = f"Mencari: {query}" # Matches the image style for paragraph searches
        main_javanese = javanese_snippet # Use a snippet of the actual Javanese from the paragraph
        main_translation = extract_translation_context(arti, query) # Contextual translation

        if group_key not in grouped:
            grouped[group_key] = {
                'main_word': main_word,
                'main_javanese': main_javanese,
                'main_translation': main_translation,
                'occurrences': [],
                'total_count': 0
            }
        
        # Add the current row as an occurrence to its determined group
        occurrence = {
            'type': row['type'],
            'javanese': isi_aksara_jawa,
            'latin': isi_latin,
            'translation': arti,
            'paragraph_reference': get_paragraph_reference(row),
            'full_sentence': get_full_sentence(row),
            'source_info': get_source_info(row),
            'found_in': {
                'latin': bool(re.search(rf'\b{re.escape(query.lower())}\b', isi_latin.lower(), re.IGNORECASE)),
                'translation': bool(re.search(rf'\b{re.escape(query.lower())}\b', arti.lower(), re.IGNORECASE)),
                'javanese': bool(re.search(rf'{re.escape(query)}', isi_aksara_jawa))
            }
        }
        grouped[group_key]['occurrences'].append(occurrence)
        grouped[group_key]['total_count'] += 1
    
    return grouped

# Helper functions untuk referensi yang lebih lengkap
def get_paragraph_reference(row):
    """Dapatkan referensi paragraf yang lebih detail"""
    reference_parts = []
    
    # Cek berbagai kolom yang mungkin berisi informasi referensi
    # 'munculDalamParagraf' adalah properti dari Kata ke Paragraf
    if 'munculDalamParagraf' in row and pd.notna(row['munculDalamParagraf']):
        reference_parts.append(f"Paragraf: {row['munculDalamParagraf']}")
    
    # Jika entitas itu sendiri adalah Paragraf, gunakan URI-nya
    if row['type'] == 'Paragraf' and 's' in row and pd.notna(row['s']):
        paragraph_id = row['s'].split('#')[-1] # Ambil bagian setelah '#'
        if not reference_parts: # Hanya tambahkan jika belum ada referensi paragraf
            reference_parts.append(f"Paragraf: {paragraph_id}")
    
    # Tambahkan informasi baris/indeks jika ada (dari DataFrame lokal)
    # Ini mungkin tidak relevan lagi jika data dari GraphDB tidak memiliki indeks baris
    if hasattr(row, 'name') and row.name is not None:
        if not any("Entri" in part for part in reference_parts): # Hindari duplikasi jika sudah ada
            reference_parts.append(f"Entri: {row.name + 1}")
    
    return " | ".join(reference_parts) if reference_parts else "Referensi tidak tersedia"

def get_full_sentence(row):
    """Dapatkan kalimat lengkap jika tersedia. Untuk GraphDB, isiLatin/isiAksaraJawa/arti dari Paragraf sudah bisa dianggap full sentence."""
    parts = []
    if pd.notna(row['isiAksaraJawa']):
        parts.append(f"Aksara Jawa: {row['isiAksaraJawa']}")
    if pd.notna(row['isiLatin']):
        parts.append(f"Latin: {row['isiLatin']}")
    if pd.notna(row['arti']):
        parts.append(f"Arti: {row['arti']}")
    
    return " | ".join(parts) if parts else "Konteks tidak tersedia"

def get_source_info(row):
    """Dapatkan informasi sumber yang lebih detail. Untuk data ini, sumber adalah GraphDB itu sendiri."""
    return "Sumber: GraphDB AksaraJawa"

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
        pattern = rf'\b{re.escape(query.lower())}\b'
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
    except:
        pass
    
    return text

# Fungsi untuk highlight text dengan word boundary
def highlight_text(text, query):
    if not text or not query:
        return text
    
    # Escape HTML special characters
    import html
    text_escaped = html.escape(str(text))
    query_escaped = html.escape(str(query))
    
    # Use word boundary untuk highlight yang presisi untuk Latin/Terjemahan
    # Untuk Aksara Jawa, highlight exact match
    try:
        # Cek apakah query adalah Aksara Jawa (berisi karakter Unicode Javanese)
        is_javanese_query = any('\ua980' <= char <= '\ua9df' for char in query)

        if is_javanese_query:
            # Untuk Aksara Jawa, cukup cari substring exact
            pattern = re.escape(query)
        else:
            # Untuk Latin/Terjemahan, gunakan word boundary
            pattern = rf'\b{re.escape(query)}\b'
        
        highlighted = re.sub(pattern, f'<span class="highlighted-text">\\g<0></span>', text_escaped, flags=re.IGNORECASE if not is_javanese_query else 0)
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
    <div style="text-align: center; margin: 2rem 0 1.5rem 0;">
        <h3 style="color: #1e3a8a; margin-bottom: 0.5rem;">⌨️ Keyboard Aksara Jawa</h3>
        <p style="color: #64748b; font-size: 0.9rem;">Tersedia {0} karakter unik dari dataset</p>
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
        <div style="
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                font-weight: 600;
            ">Aksara Dasar</h4>
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
            <div style="
                background: white;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border: 1px solid #e2e8f0;
            ">
                <h4 style="
                    text-align: center;
                    color: #1e40af;
                    margin-bottom: 1rem;
                    font-size: 1.2rem;
                    font-weight: 600;
                ">Sandhangan Vokal</h4>
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
            <div style="
                background: white;
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border: 1px solid #e2e8f0;
            ">
                <h4 style="
                    text-align: center;
                    color: #1e40af;
                    margin-bottom: 1rem;
                    font-size: 1.2rem;
                    font-weight: 600;
                ">Tanda Baca & Simbol</h4>
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
    
    # Baris bawah untuk control dan contoh
    col3, col4 = st.columns(2, gap="large")
    
    # 4. Section Kontrol
    with col3:
        st.markdown("""
        <div style="
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                font-weight: 600;
            ">Kontrol</h4>
        """, unsafe_allow_html=True)
        
        # Tombol control dalam grid yang rapi
        control_col1, control_col2 = st.columns(2)
        
        with control_col1:
            if st.button(
                "⎵ Spasi", 
                key="add_space", 
                help="Tambahkan spasi",
                use_container_width=True
            ):
                if 'search_query' not in st.session_state:
                    st.session_state.search_query = ""
                st.session_state.search_query += " "
                st.rerun()
        
        with control_col2:
            if st.button(
                "🗑️ Hapus", 
                key="clear_search", 
                help="Hapus semua teks pencarian",
                use_container_width=True
            ):
                st.session_state.search_query = ""
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # 5. Section Contoh Pencarian
    with col4:
        st.markdown("""
        <div style="
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                font-weight: 600;
            ">Contoh Pencarian</h4>
        """, unsafe_allow_html=True)
        
        # Contoh kata-kata populer dari dataset
        example_words = ["ꦠꦠ꧀ꦏꦭ", "ꦤꦼꦒꦫꦶ", "ꦱꦸꦫꦥꦿꦶꦁꦒ", "ꦲꦶꦁ"]
        
        example_col1, example_col2 = st.columns(2)
        
        for i, word in enumerate(example_words):
            target_col = example_col1 if i % 2 == 0 else example_col2
            with target_col:
                if st.button(
                    f"📝 {word}", 
                    key=f"example_{i}", 
                    help=f"Coba cari: {word}",
                    use_container_width=True
                ):
                    st.session_state.search_query = word
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Tampilkan karakter lainnya jika ada
    if others:
        st.markdown("""
        <div style="
            background: white;
            border-radius: 12px;
            padding: 1rem;
            margin-top: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1.2rem;
                font-weight: 600;
            ">Karakter Lainnya</h4>
        """, unsafe_allow_html=True)
        
        chars_per_row = 8
        rows = [others[i:i + chars_per_row] for i in range(0, len(others), chars_per_row)]
        
        for row_idx, char_row in enumerate(rows):
            cols_inner = st.columns(len(char_row))
            for col_idx, char in enumerate(char_row):
                with cols_inner[col_idx]:
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
    
    # Tutup container utama
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Tips penggunaan
    st.markdown("""
    <div style="
        text-align: center;
        margin-top: 1rem;
        padding: 1rem;
        background: #f1f5f9;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
    ">
        <p style="margin: 0; color: #475569; font-size: 0.9rem;">
            💡 <strong>Tips:</strong> Klik karakter untuk menambahkan ke pencarian, 
            gunakan tombol spasi untuk memisahkan kata, dan hapus untuk membersihkan pencarian.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tampilkan karakter lainnya jika ada
    if others:
        st.markdown('<div class="keyboard-section keyboard-section-small">', unsafe_allow_html=True)
        st.markdown('<h5 class="section-title">Karakter Lainnya</h5>', unsafe_allow_html=True)
        st.markdown('<div class="keyboard-grid keyboard-grid-small">', unsafe_allow_html=True)
        
        chars_per_row = 6
        rows = [others[i:i + chars_per_row] for i in range(0, len(others), chars_per_row)]
        
        for row_idx, char_row in enumerate(rows):
            st.markdown('<div class="keyboard-row">', unsafe_allow_html=True)
            cols_inner = st.columns(len(char_row))
            for col_idx, char in enumerate(char_row):
                with cols_inner[col_idx]:
                    if st.button(char, key=f"other_{row_idx}_{col_idx}", 
                               help=f"Tambahkan {char} (U+{ord(char):04X})"):
                        if 'search_query' not in st.session_state:
                            st.session_state.search_query = ""
                        st.session_state.search_query += char
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Fungsi untuk menampilkan statistik
def display_statistics(df):
    if df.empty:
        return
    
    total_entries = len(df)
    paragraf_count = len(df[df['type'] == 'Paragraf']) if 'type' in df.columns else 0
    kata_count = len(df[df['type'] == 'Kata']) if 'type' in df.columns else 0
    
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-number">{total_entries}</div>
            <div class="stat-label">Total Entri</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-number">{paragraf_count}</div>
            <div class="stat-label">Paragraf</div>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
        <div class="stat-card">
            <div class="stat-number">{kata_count}</div>
            <div class="stat-label">Kata</div>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# Fungsi untuk menampilkan hasil dengan grouping
def display_grouped_results(grouped_results, query):
    if not grouped_results:
        st.markdown('''
        <div class="no-results-icon">🔍</div>
            <div class="no-results-text">Tidak ada hasil ditemukan</div>
            <div class="no-results-subtext">Coba gunakan kata kunci yang berbeda</div>
        </div>
        ''', unsafe_allow_html=True)
        return
    
    # Total groups now refers to the number of distinct words/paragraphs found
    total_groups = len(grouped_results)
    total_occurrences = sum(group['total_count'] for group in grouped_results.values())
    
    st.markdown(f"<h3>Hasil Pencarian: {total_groups} entri unik dengan {total_occurrences} kemunculan</h3>", unsafe_allow_html=True)
    
    # Sort groups to display 'Kata' first, then 'Paragraf'
    sorted_group_keys = sorted(grouped_results.keys(), 
                               key=lambda k: (0 if k.startswith("Kata:") else 1, k))

    for group_key in sorted_group_keys:
        group_data = grouped_results[group_key]
        
        # Create unique key for this result group
        result_id = f"result_{hash(group_key) % 100000}"
        is_expanded = result_id in st.session_state.expanded_results
        
        # Header with expand/collapse functionality
        expand_icon = "▼" if is_expanded else "▶"
        
        st.markdown(f'''
        <div class="grouped-result">
            <div class="result-header" onclick="toggleResult('{result_id}')">
                <div class="result-header-main">
                    <div class="result-title">{expand_icon} {group_data['main_word']}</div>
                    <div class="result-subtitle">{group_data['main_javanese']}</div>
                </div>
                <div class="result-count">{group_data['total_count']} kemunculan</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Toggle button for expanding/collapsing
        if st.button(f"{'Tutup' if is_expanded else 'Lihat Detail'} ({group_data['total_count']} kemunculan)", 
                    key=f"toggle_{result_id}"):
            if is_expanded:
                st.session_state.expanded_results.discard(result_id)
            else:
                st.session_state.expanded_results.add(result_id)
            st.rerun()
        
        # Show details if expanded
        if is_expanded:
            st.markdown("---")
            for i, occurrence in enumerate(group_data['occurrences']):
                with st.container():
                    # Enhanced context label with more detailed reference
                    st.markdown(f'''
                    <div class="context-label-enhanced">
                        <div class="context-type">{occurrence["type"]}</div>
                        <div class="context-reference">{occurrence["paragraph_reference"]}</div>
                        <div class="context-source">{occurrence["source_info"]}</div>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        st.markdown("*Aksara Jawa:*")
                        highlighted_javanese = highlight_text(occurrence['javanese'], query) if occurrence['found_in']['javanese'] else occurrence['javanese']
                        st.markdown(f'<div class="javanese-text">{highlighted_javanese}</div>', unsafe_allow_html=True)
                        
                        st.markdown("*Transliterasi:*")
                        highlighted_latin = highlight_text(occurrence['latin'], query) if occurrence['found_in']['latin'] else occurrence['latin']
                        st.markdown(f'<div class="latin-text">{highlighted_latin}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown("*Terjemahan:*")
                        highlighted_translation = highlight_text(occurrence['translation'], query) if occurrence['found_in']['translation'] else occurrence['translation']
                        st.markdown(f'<div class="translation-text">{highlighted_translation}</div>', unsafe_allow_html=True)
                        
                        # Show where the match was found
                        found_locations = []
                        if occurrence['found_in']['javanese']:
                            found_locations.append("Aksara Jawa")
                        if occurrence['found_in']['latin']:
                            found_locations.append("Latin")
                        if occurrence['found_in']['translation']:
                            found_locations.append("Terjemahan")
                        
                        if found_locations:
                            st.markdown(f"*Ditemukan dalam:* {', '.join(found_locations)}")
                    
                    # Show full sentence context if available
                    if occurrence['full_sentence'] and occurrence['full_sentence'] != "Konteks tidak tersedia":
                        st.markdown("*Konteks Kalimat Lengkap:*")
                        highlighted_sentence = highlight_text(occurrence['full_sentence'], query)
                        st.markdown(f'<div class="sentence-context">{highlighted_sentence}</div>', unsafe_allow_html=True)
                    
                    if i < len(group_data['occurrences']) - 1:
                        st.markdown("---")
            
            st.markdown("<br>", unsafe_allow_html=True)

# JavaScript untuk toggle functionality
def add_toggle_script():
    st.markdown("""
    <script>
    function toggleResult(resultId) {
        // This will be handled by the Streamlit button click
        console.log('Toggle result:', resultId);
    }
    </script>
    """, unsafe_allow_html=True)

# Main app
def main():
    load_css()
    
    # Header
    st.markdown('''
    <div class="main-container">
        <div class="header-container">
            <h1 class="header-title">📜 Pencarian Naskah Jawa</h1>
            <p class="header-subtitle">Jelajahi kekayaan naskah Jawa dengan pencarian semantik</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Initialize session state for expanded results at the very beginning of main()
    if 'expanded_results' not in st.session_state:
        st.session_state.expanded_results = set()

    # Load data
    df = load_data_from_graphdb() 
    
    if df.empty:
        st.stop()
    
    # Display statistics
    display_statistics(df)
    
    # Search container
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    
    # Search input
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Initialize session state for search query
        if 'search_query' not in st.session_state:
            st.session_state.search_query = ""
        
        query = st.text_input(
            "Masukkan kata kunci pencarian:",
            value=st.session_state.search_query,
            placeholder="Contoh: tatkala, ketika, atau aksara Jawa dari dataset",
            help="Anda dapat mencari menggunakan aksara Latin, terjemahan Indonesia, atau aksara Jawa"
        )
        
        # Update session state
        st.session_state.search_query = query
    
    with col2:
        search_type = st.selectbox(
            "Jenis Pencarian:",
            ["all", "latin", "translation", "javanese"],
            format_func=lambda x: {
                "all": "🌍 Semua",
                "latin": "🔤 Latin", 
                "translation": "🇮🇩 Terjemahan",
                "javanese": "ꦗꦮ Aksara Jawa"
            }[x]
        )
    
    # Clear search button
    if st.button("🗑 Bersihkan", help="Bersihkan kotak pencarian"):
        st.session_state.search_query = ""
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Javanese keyboard
    with st.expander("⌨ Keyboard Aksara Jawa", expanded=False):
        create_javanese_keyboard(df)
    
    # Search and display results
    if query:
        with st.spinner("Mencari..."):
            results, grouped_results = search_text(df, query, search_type)
            add_toggle_script()
            display_grouped_results(grouped_results, query)
    else:
        # Show sample entries when no search
        st.markdown("### Contoh Entri")
        sample_data = df.head(5)
        # Create dummy grouped results for sample display
        sample_grouped = {}
        for idx, row in sample_data.iterrows():
            # Untuk contoh, buat key yang unik berdasarkan isi entri
            key = f"Contoh Entri {idx+1}: {row['isiLatin']}" if pd.notna(row['isiLatin']) else f"Contoh Entri {idx+1}"
            sample_grouped[key] = {
                'main_word': row['isiLatin'] if pd.notna(row['isiLatin']) else 'N/A',
                'main_javanese': row['isiAksaraJawa'] if pd.notna(row['isiAksaraJawa']) else 'N/A',
                'main_translation': row['arti'] if pd.notna(row['arti']) else 'N/A',
                'occurrences': [{
                    'type': row['type'],
                    'javanese': row['isiAksaraJawa'] if pd.notna(row['isiAksaraJawa']) else 'N/A',
                    'latin': row['isiLatin'] if pd.notna(row['isiLatin']) else 'N/A',
                    'translation': row['arti'] if pd.notna(row['arti']) else 'N/A',
                    'paragraph_reference': get_paragraph_reference(row),
                    'full_sentence': get_full_sentence(row),
                    'source_info': get_source_info(row),
                    'found_in': {'latin': False, 'translation': False, 'javanese': False}
                }],
                'total_count': 1
            }
        display_grouped_results(sample_grouped, "")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #64748b; font-size: 0.9rem; padding: 2rem;'>
        <p>Aplikasi Pencarian Naskah Jawa | Mahasiswa TI UNPAD</p>
        <p>Gunakan keyboard aksara Jawa di atas untuk pencarian dengan aksara asli</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
