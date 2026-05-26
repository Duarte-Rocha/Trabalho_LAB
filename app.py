import streamlit as st
import re
from io import BytesIO
from xhtml2pdf import pisa

# ---------------------------------------------------------
# IMPORTAÇÕES
# ---------------------------------------------------------
from modules.extraction import extract_pdf, extract_docx, extract_txt

from modules.preprocess import (
    preparar_para_normalizacao,
    validar_resposta,
    limpeza_final,
    formatar_para_ui,
    remover_repeticoes,
    remover_linhas_duplicadas,
    remover_blocos_duplicados,
    limpar_ruido_final,
)

from modules.slm_api import enviar_para_slm

# ---------------------------------------------------------
# CONFIGURAÇÃO
# ---------------------------------------------------------
st.set_page_config(page_title="Pipeline de Texto", layout="wide")

st.title("TP2 – Pipeline de Texto")
st.write("Carrega um ficheiro para analisar e normalizar o texto.")

# ---------------------------------------------------------
# SESSION STATE
# ---------------------------------------------------------
defaults = {
    "texto_original": "",
    "texto_limpo": "",
    "chunks": [],
    "prompts": [],
    "texto_normalizado": "",
    "idioma": "",
    "tamanho": 800
}

for key, value in defaults.items():
    st.session_state.setdefault(key, value)

# ---------------------------------------------------------
# EXTRAÇÃO
# ---------------------------------------------------------
def extrair_texto(file):
    if file.type == "application/pdf":
        return extract_pdf(file)
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_docx(file)
    elif file.type == "text/plain":
        return extract_txt(file)
    return ""

# ---------------------------------------------------------
# UPLOAD
# ---------------------------------------------------------
uploaded_file = st.file_uploader("📄 Escolhe um ficheiro", ["pdf", "docx", "txt"])

if uploaded_file:
    st.session_state["texto_original"] = extrair_texto(uploaded_file)
    st.success("Ficheiro carregado com sucesso!")

# ---------------------------------------------------------
# TABS
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "Texto Original",
    "Texto Limpo",
    "Normalização",
    "Comparação"
])

# ---------------------------------------------------------
# TAB 1
# ---------------------------------------------------------
with tab1:
    if st.session_state["texto_original"]:
        st.text_area("Texto:", st.session_state["texto_original"], height=400)
    else:
        st.info("Carrega um ficheiro")

# ---------------------------------------------------------
# TAB 2
# ---------------------------------------------------------
with tab2:
    if st.session_state["texto_original"]:

        if st.button("Limpar Texto"):
            from modules.cleaning import limpar_texto
            st.session_state["texto_limpo"] = limpar_texto(st.session_state["texto_original"])
            st.success("Texto limpo ✅")

        st.text_area("Resultado:", st.session_state["texto_limpo"], height=400)

    else:
        st.warning("Carrega primeiro um ficheiro")

# ---------------------------------------------------------
# TAB 3
# ---------------------------------------------------------
with tab3:

    texto_limpo = st.session_state["texto_limpo"]

    if not texto_limpo:
        st.warning("Primeiro limpa o texto")
    else:

        st.session_state["tamanho"] = st.slider("Chunk size", 400, 3000, st.session_state["tamanho"])

        if st.button("Gerar Chunks"):
            idioma, chunks, prompts = preparar_para_normalizacao(texto_limpo, st.session_state["tamanho"])
            st.session_state["chunks"] = chunks
            st.session_state["prompts"] = prompts
            st.session_state["idioma"] = idioma
            st.success(f"{len(chunks)} chunks")

        for i, c in enumerate(st.session_state.get("chunks", [])):
            with st.expander(f"Chunk {i+1}"):
                st.text(c)

        if st.session_state.get("prompts"):
            with st.expander("📌 Ver Prompt"):
                st.text(st.session_state["prompts"][0])

        if st.button("Normalizar"):

            resultados = []
            total = len(st.session_state["chunks"])
            progresso = st.progress(0)

            for i, prompt in enumerate(st.session_state["prompts"]):
                chunk = st.session_state["chunks"][i]

                try:
                    resposta = enviar_para_slm(prompt, chunk)
                except:
                    resposta = chunk

                resposta = limpeza_final(resposta)

                resultados.append(resposta if validar_resposta(chunk, resposta) else chunk)

                progresso.progress((i + 1) / total)

            # ✅ FIX BLOCO
            texto_final = "\n\n".join(resultados)

            texto_final = limpeza_final(texto_final)
            texto_final = remover_repeticoes(texto_final)
            texto_final = remover_linhas_duplicadas(texto_final)
            texto_final = remover_blocos_duplicados(texto_final)
            texto_final = limpar_ruido_final(texto_final)

            st.session_state["texto_normalizado"] = texto_final

            # ✅ FORMATAÇÃO COM PARÁGRAFOS
            texto_ui = formatar_para_ui(texto_final)
            texto_ui = texto_ui.replace(". ", ".\n\n")

            st.text_area("Resultado:", texto_ui, height=400)

# ---------------------------------------------------------
# TAB 4 (CORRIGIDO)
# ---------------------------------------------------------
with tab4:

    col1, col2 = st.columns(2)

    # ✅ ANTES
    with col1:
        st.markdown("### 🔴 Antes")

        texto_antes = st.session_state.get("texto_original", "")

        if texto_antes:
            texto_antes = formatar_para_ui(texto_antes).replace(". ", ".\n\n")

            st.text_area(
                "",
                texto_antes,
                height=400,
                key="antes"
            )
        else:
            st.info("Sem texto original")

    # ✅ DEPOIS
    with col2:
        st.markdown("### 🟢 Depois")

        texto_depois = st.session_state.get("texto_normalizado", "")

        if texto_depois:
            texto_depois = formatar_para_ui(texto_depois).replace(". ", ".\n\n")

            st.text_area(
                "",
                texto_depois,
                height=400,
                key="depois"
            )
        else:
            st.info("Ainda não normalizaste o texto")

# ---------------------------------------------------------
# RELATÓRIO + PDF
# ---------------------------------------------------------
if st.session_state["texto_normalizado"]:

    st.subheader("📄 Gerar Relatório")

    texto_original = st.session_state["texto_original"]
    texto_limpo = st.session_state["texto_limpo"]
    texto_normalizado = st.session_state["texto_normalizado"]

    # ✅ FORMATAR TEXTO (igual à UI)
    texto_ui = formatar_para_ui(texto_normalizado)
    texto_ui = re.sub(r'\.\s*', '.\n\n', texto_ui)

    texto_original_html = texto_original.replace("\n", "<br>")
    texto_limpo_html = texto_limpo.replace("\n", "<br>")
    texto_normalizado_html = texto_ui.replace("\n", "<br>")

    # ✅ AVALIAÇÃO AUTOMÁTICA
    qualidade = "Boa"
    observacao = "O texto foi normalizado com sucesso e apresenta boa legibilidade."

    if len(texto_normalizado) < len(texto_limpo) * 0.7:
        qualidade = "Baixa"
        observacao = "Possível perda de conteúdo durante a normalização."

    elif "Erro" in texto_normalizado:
        qualidade = "Limitada"
        observacao = "Alguns blocos não foram processados corretamente."

    html = f"""
<!DOCTYPE html>
<html lang="pt">
<head>
<meta charset="UTF-8">
<title>Relatório</title>
</head>

<body style="font-family: Arial; margin: 40px;">

<h1 style="text-align:center;">Relatório de Normalização</h1>

<h2>Parâmetros</h2>
<p><b>Idioma:</b> {st.session_state.get("idioma")}</p>
<p><b>Chunks:</b> {len(st.session_state.get("chunks", []))}</p>

<h2>Texto Original</h2>
<div style="line-height: 1.6; max-width: 800px;">
{texto_original_html}
</div>

<h2>Texto Limpo</h2>
<div style="line-height: 1.6; max-width: 800px;">
{texto_limpo_html}
</div>

<h2>Texto Normalizado</h2>
<div style="line-height: 1.6; max-width: 800px;">
{texto_normalizado_html}
</div>

<hr>

<h2>Avaliação da Normalização</h2>
<p><b>Qualidade:</b> {qualidade}</p>
<p><b>Observação:</b> {observacao}</p>

</body>
</html>
"""

    # ✅ FUNÇÃO PDF
    def gerar_pdf_html(html):
        buffer = BytesIO()
        pisa.CreatePDF(src=html, dest=buffer)
        buffer.seek(0)
        return buffer

    pdf_buffer = gerar_pdf_html(html)

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            label="📄 PDF",
            data=pdf_buffer,
            file_name="relatorio.pdf",
            mime="application/pdf"
        )

    with col2:
        st.download_button(
            label="🌐 HTML",
            data=html,
            file_name="relatorio.html",
            mime="text/html"
        )
