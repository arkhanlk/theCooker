import json
import streamlit as st

# Caminho fixo do seu arquivo
JSON_PATH = r"D:\.py\AR\AR\data\arcraiders_dump2.json"

st.set_page_config(page_title="ARC Raiders Data Viewer", layout="wide")

st.title("ARC Raiders — Visualizador de Dados")
st.write("Explore o conteúdo extraído do arcraiders_dump.json")

# ---------------------------
# Carregar JSON
# ---------------------------
@st.cache_data
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

data = load_json(JSON_PATH)

st.success(f"Arquivo carregado com {len(data)} páginas.")

# ---------------------------
# Seleção da página
# ---------------------------

allowed = ['ARC', 'Augments', 'Healing', 'Loot', 'Maps', 'Quests', 'Quick Use', 'Shields', 'Skills', 'Speranza', 'Weapons', 'Workshop']

filtered_data = [item for item in data if item.get("title") in allowed]

titles = [item["title"] for item in filtered_data]

selected_title = st.selectbox("Selecione uma página:", titles)
page = filtered_data[titles.index(selected_title)]

st.header(selected_title)

# ---------------------------
# Mostrar texto
# ---------------------------
st.subheader("Texto (com </> preservado)")
st.text_area("Conteúdo", page.get("text", ""), height=300)

# ---------------------------
# Mostrar infobox
# ---------------------------
if page.get("infobox"):
    st.subheader("Infobox")
    st.json(page["infobox"])

# ---------------------------
# Mostrar tabelas segmentadas
# ---------------------------
if page.get("tables_segmented"):
    st.subheader("Tabelas")
    for i, table in enumerate(page["tables_segmented"]):
        st.write(f"**Tabela {i+1}:**")
        st.table(table)

# ---------------------------
# Mostrar links
# ---------------------------
if page.get("links"):
    st.subheader("Links internos")
    st.write(page["links"])

# ---------------------------
# Mostrar imagens
# ---------------------------
if page.get("images"):
    st.subheader("Imagens referenciadas")
    st.write(page["images"])
