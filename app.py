import streamlit as st
import pandas as pd
import re
from pathlib import Path

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

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("dataset/pupuh.csv")
        return df
    except FileNotFoundError:
        st.error("File pupuh.csv tidak ditemukan. Pastikan file CSV ada di direktori yang sama.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Fungsi untuk mendapatkan karakter aksara Jawa unik dari dataset
@st.cache_data
def get_unique_javanese_chars(df):
    """Ekstrak karakter aksara Jawa unik dari dataset"""
    if df.empty or 'isiAksaraJawa' not in df.columns:
        # Fallback ke karakter dari contoh yang diberikan user
        sample_text = """꧋ꦥꦸꦤꦶꦏ‌ꦱꦼꦂꦫꦠ꧀‌ꦏꦒꦸꦁꦔꦤ꧀ꦤꦶꦥꦸꦤ꧀ꦚꦚꦃ​ꦱꦏꦺꦧꦼꦂ‌​ꦲꦶꦁ​ꦱꦸꦫꦥꦿꦶꦁꦒ꧋
꧁ꦥꦸꦃꦠꦼꦩ꧀ꦧꦁ​ꦲꦱ꧀ꦩꦫꦢꦺꦴꦤ꧂
꧃ꦠꦠ꧀ꦏꦭꦮꦶꦮꦶꦠ꧀ꦠꦶꦤꦸꦭꦶꦱ꧀ꦲꦶꦁ​ꦢꦶꦠꦼꦤ꧀꧈​ꦔꦲꦢ꧀ꦥꦸꦤꦶꦏ​ꦥꦸꦏꦸꦭ꧀ꦱꦥ꧀ꦠ​ꦲꦶꦁ​ꦮꦪꦃꦲꦺ꧈​ꦏꦮꦤ꧀ꦭꦶꦏꦸꦂ​ꦲꦶꦁ​ꦏꦁ​ꦠꦁ​ꦒꦭ꧀​ꦤꦼꦁ​ꦒꦶꦃ​ꦲꦶꦁ​ꦯꦯꦶ​​ꦱꦥꦂ꧈​ꦠꦲꦸꦤ꧀ꦤꦭꦶꦥ꧀ꦢꦸꦏ꧀ꦠꦶꦤꦸꦫꦸꦤ꧀​​ꦗꦼꦗꦼꦒꦶꦁ​ꦩꦺꦴꦁ​ꦱ​ꦏꦠꦶꦒ꧉"""
        
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
        latin_matches = df[df['isiLatin'].str.contains(rf'\b{re.escape(query.lower())}\b', 
                                                      case=False, na=False, regex=True)]
        results = pd.concat([results, latin_matches], ignore_index=True)
    
    if search_type in ["all", "translation"]:
        # Pencarian presisi dalam kolom arti dengan word boundary
        translation_matches = df[df['arti'].str.contains(rf'\b{re.escape(query.lower())}\b', 
                                                        case=False, na=False, regex=True)]
        results = pd.concat([results, translation_matches], ignore_index=True)
    
    if search_type in ["all", "javanese"]:
        # Pencarian dalam kolom isiAksaraJawa dengan metode yang lebih fleksibel
        # Cari exact match terlebih dahulu
        exact_matches = df[df['isiAksaraJawa'].str.contains(re.escape(query), na=False, regex=True)]
        results = pd.concat([results, exact_matches], ignore_index=True)
        
        # Jika tidak ada exact match, coba pencarian dengan word boundary yang lebih longgar
        if exact_matches.empty:
            # Cari dengan pola yang mempertimbangkan spasi dan tanda baca aksara Jawa
            pattern = rf'{re.escape(query)}'
            loose_matches = df[df['isiAksaraJawa'].str.contains(pattern, na=False, regex=True)]
            results = pd.concat([results, loose_matches], ignore_index=True)
    
    # Hapus duplikat
    results = results.drop_duplicates().reset_index(drop=True)
    
    # Group results by unique words/phrases
    grouped_results = group_search_results(results, query)
    
    return results, grouped_results

# Fungsi untuk mengelompokkan hasil pencarian
def group_search_results(df, query):
    if df.empty:
        return {}
    
    grouped = {}
    
    for idx, row in df.iterrows():
        # Tentukan kata kunci utama yang ditemukan dengan pencarian presisi
        found_in_latin = bool(re.search(rf'\b{re.escape(query.lower())}\b', 
                                       row['isiLatin'].lower() if pd.notna(row['isiLatin']) else '', 
                                       re.IGNORECASE))
        found_in_translation = bool(re.search(rf'\b{re.escape(query.lower())}\b', 
                                             row['arti'].lower() if pd.notna(row['arti']) else '', 
                                             re.IGNORECASE))
        found_in_javanese = bool(re.search(rf'(?<!\S){re.escape(query)}(?!\S)', 
                                          row['isiAksaraJawa'] if pd.notna(row['isiAksaraJawa']) else ''))
        
        # Buat key untuk grouping
        if row['type'] == 'Kata':
            # Untuk kata, group berdasarkan kata itu sendiri
            group_key = f"{row['isiLatin']} ({row['isiAksaraJawa']})"
            main_word = row['isiLatin']
            main_javanese = row['isiAksaraJawa']
            main_translation = row['arti']
        else:
            # Untuk paragraf, group berdasarkan query yang ditemukan
            group_key = f"Paragraf mengandung '{query}'"
            main_word = f"Mencari: {query}"
            main_javanese = extract_javanese_context(row['isiAksaraJawa'], query)
            main_translation = extract_translation_context(row['arti'], query)
        
        if group_key not in grouped:
            grouped[group_key] = {
                'main_word': main_word,
                'main_javanese': main_javanese,
                'main_translation': main_translation,
                'occurrences': [],
                'total_count': 0
            }
        
        # Tambahkan occurrence dengan informasi referensi yang lebih lengkap
        occurrence = {
            'type': row['type'],
            'javanese': row['isiAksaraJawa'],
            'latin': row['isiLatin'],
            'translation': row['arti'],
            'paragraph_reference': get_paragraph_reference(row),
            'full_sentence': get_full_sentence(row),
            'source_info': get_source_info(row),
            'found_in': {
                'latin': found_in_latin,
                'translation': found_in_translation,
                'javanese': found_in_javanese
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
    possible_ref_columns = ['munculDalamParagraf', 'paragraph', 'paragraf', 'bab', 'chapter']
    
    for col in possible_ref_columns:
        if col in row and pd.notna(row[col]):
            reference_parts.append(f"{col.replace('munculDalamParagraf', 'Paragraf')}: {row[col]}")
    
    # Jika ada nomor baris atau indeks
    if 'baris' in row and pd.notna(row['baris']):
        reference_parts.append(f"Baris: {row['baris']}")
    elif hasattr(row, 'name') and row.name is not None:
        reference_parts.append(f"Entri: {row.name + 1}")
    
    return " | ".join(reference_parts) if reference_parts else "Referensi tidak tersedia"

def get_full_sentence(row):
    """Dapatkan kalimat lengkap jika tersedia"""
    # Cek kolom yang mungkin berisi kalimat lengkap
    possible_sentence_columns = ['kalimat', 'sentence', 'fullText', 'context']
    
    for col in possible_sentence_columns:
        if col in row and pd.notna(row[col]):
            return row[col]
    
    # Jika tidak ada kalimat lengkap, gabungkan informasi yang ada
    parts = []
    if pd.notna(row['isiAksaraJawa']):
        parts.append(f"Aksara Jawa: {row['isiAksaraJawa']}")
    if pd.notna(row['isiLatin']):
        parts.append(f"Latin: {row['isiLatin']}")
    if pd.notna(row['arti']):
        parts.append(f"Arti: {row['arti']}")
    
    return " | ".join(parts) if parts else "Konteks tidak tersedia"

def get_source_info(row):
    """Dapatkan informasi sumber yang lebih detail"""
    source_parts = []
    
    # Cek berbagai kolom sumber
    possible_source_columns = ['sumber', 'source', 'book', 'manuscript', 'naskah']
    
    for col in possible_source_columns:
        if col in row and pd.notna(row[col]):
            source_parts.append(f"{col.title()}: {row[col]}")
    
    # Tambahkan informasi tambahan jika ada
    if 'penulis' in row and pd.notna(row['penulis']):
        source_parts.append(f"Penulis: {row['penulis']}")
    if 'tahun' in row and pd.notna(row['tahun']):
        source_parts.append(f"Tahun: {row['tahun']}")
    
    return " | ".join(source_parts) if source_parts else "Sumber tidak diketahui"

# Helper functions
def extract_javanese_context(text, query, context_length=50):
    if not text or not query:
        return text
    
    # Untuk aksara Jawa, ambil konteks di sekitar query dengan word boundary
    try:
        pattern = rf'(?<!\S){re.escape(query)}(?!\S)'
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

def extract_source_paragraph(row):
    if 'munculDalamParagraf' in row and pd.notna(row['munculDalamParagraf']):
        return row['munculDalamParagraf']
    elif 'sumber' in row and pd.notna(row['sumber']):
        return f"Sumber: {row['sumber']}"
    else:
        return "Tidak diketahui"

# Fungsi untuk highlight text dengan word boundary
def highlight_text(text, query):
    if not text or not query:
        return text
    
    # Escape HTML special characters
    import html
    text = html.escape(str(text))
    query_escaped = html.escape(str(query))
    
    # Use word boundary untuk highlight yang presisi
    try:
        pattern = rf'\b({re.escape(query)})\b'
        highlighted = re.sub(pattern, f'<span class="highlighted-text">\\1</span>', text, flags=re.IGNORECASE)
        return highlighted
    except:
        # Fallback jika regex gagal
        return text.replace(query_escaped, f'<span class="highlighted-text">{query_escaped}</span>')

# Keyboard aksara Jawa berdasarkan dataset
# Ganti fungsi create_javanese_keyboard yang ada (sekitar baris 200-340) dengan kode berikut:

# Ganti fungsi create_javanese_keyboard yang ada (sekitar baris 200-340) dengan kode berikut:

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
    
    # Container utama keyboard
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    ">
    """, unsafe_allow_html=True)
    
    # 1. Section Aksara Dasar (bagian paling besar)
    if consonants:
        st.markdown("""
        <div style="
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1.1rem;
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
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border: 1px solid #e2e8f0;
                min-height: 200px;
            ">
                <h4 style="
                    text-align: center;
                    color: #1e40af;
                    margin-bottom: 1rem;
                    font-size: 1rem;
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
                padding: 1.5rem;
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(0,0,0,0.05);
                border: 1px solid #e2e8f0;
                min-height: 200px;
            ">
                <h4 style="
                    text-align: center;
                    color: #1e40af;
                    margin-bottom: 1rem;
                    font-size: 1rem;
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
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
            min-height: 150px;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1rem;
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
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
            min-height: 150px;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1rem;
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
            padding: 1.5rem;
            margin-top: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        ">
            <h4 style="
                text-align: center;
                color: #1e40af;
                margin-bottom: 1rem;
                font-size: 1rem;
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
    
    total_groups = len(grouped_results)
    total_occurrences = sum(group['total_count'] for group in grouped_results.values())
    
    st.markdown(f"<h3>Hasil Pencarian: {total_groups} kata/frasa unik dengan {total_occurrences} kemunculan</h3>", unsafe_allow_html=True)
    
    # Initialize session state for expanded results
    if 'expanded_results' not in st.session_state:
        st.session_state.expanded_results = set()
    
    for group_key, group_data in grouped_results.items():
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
    
    # Load data
    df = load_data()
    
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
            key = f"{row['isiLatin']} ({row['isiAksaraJawa']})"
            sample_grouped[key] = {
                'main_word': row['isiLatin'],
                'main_javanese': row['isiAksaraJawa'],
                'main_translation': row['arti'],
                'occurrences': [{
                    'type': row['type'],
                    'javanese': row['isiAksaraJawa'],
                    'latin': row['isiLatin'],
                    'translation': row['arti'],
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