from langdetect import detect, LangDetectException
from difflib import SequenceMatcher
import re

# ---------------------------------------------------------
# 1. DETEÇÃO DE IDIOMA
# ---------------------------------------------------------
def detetar_idioma(texto):
    texto = texto.strip()

    if len(texto) < 20:
        return "desconhecido"

    try:
        return detect(texto)
    except LangDetectException:
        return "desconhecido"


# ---------------------------------------------------------
# 2. CHUNKING (VERSÃO MELHORADA)
# ---------------------------------------------------------
def chunk_text(texto, tamanho=1200, overlap=120):

    texto = texto.strip()
    chunks = []
    inicio = 0

    while inicio < len(texto):

        fim = inicio + tamanho

        if fim >= len(texto):
            chunks.append(texto[inicio:].strip())
            break

        corte = max(
            texto.rfind("\n\n", inicio, fim),
            texto.rfind("\n", inicio, fim),
            texto.rfind(". ", inicio, fim),
            texto.rfind(" ", inicio, fim)
        )

        if corte == -1:
            corte = fim

        if corte - inicio < tamanho * 0.4:
            corte = fim

        chunk = texto[inicio:corte].strip()

        if chunk:
            chunks.append(chunk)

        inicio = max(corte - overlap, 0)

    return chunks


# ---------------------------------------------------------
# 3. PROMPT
# ---------------------------------------------------------
def criar_prompt_relatorio():
    return """
TAREFA: NORMALIZAÇÃO LITERAL DE TEXTO
Corrige apenas espaços, quebras de linha e pontuação.
Não expliques. Não alteres palavras. Não adiciones texto.
Devolve apenas o texto.
""".strip()


# ---------------------------------------------------------
# 4. VALIDAÇÃO
# ---------------------------------------------------------
PADROES_PROIBIDOS = [
    "não posso", "como modelo", "desculpa",
    "posso ajudar", "assistente", "chatgpt",
    "openai", "ia"
]

def validar_resposta(chunk, resposta):

    if not resposta:
        return False

    resposta = resposta.strip()

    if len(resposta) < len(chunk) * 0.5:
        return False

    similaridade = SequenceMatcher(None, chunk, resposta).ratio()

    if similaridade < 0.90:
        return False

    for p in PADROES_PROIBIDOS:
        if p in resposta.lower():
            return False

    nums_r = [w for w in resposta.split() if w.isdigit()]
    nums_c = [w for w in chunk.split() if w.isdigit()]

    for n in nums_r:
        if n not in nums_c:
            return False

    novas = set(resposta.split()) - set(chunk.split())

    if len(novas) > 8:
        return False

    return True


# ---------------------------------------------------------
# 5. LIMPEZA FINAL
# ---------------------------------------------------------
def limpeza_final(texto):

    texto = re.sub(r'[ \t]+', ' ', texto)

    texto = texto.replace(" .", ".")
    texto = texto.replace(" ,", ",")
    texto = texto.replace(" :", ":")
    texto = texto.replace(" ;", ";")

    return texto.strip()


# ---------------------------------------------------------
# 6. REMOVER REPETIÇÕES
# ---------------------------------------------------------
def remover_repeticoes(texto):

    palavras = texto.split()
    resultado = []

    for i, p in enumerate(palavras):
        if i == 0 or p != palavras[i - 1]:
            resultado.append(p)

    return " ".join(resultado)


# ---------------------------------------------------------
# 7. REMOVER LINHAS DUPLICADAS
# ---------------------------------------------------------
def remover_linhas_duplicadas(texto):

    linhas = texto.split("\n")
    vistas = set()
    resultado = []

    for linha in linhas:
        l = linha.strip()

        if l and l not in vistas:
            vistas.add(l)
            resultado.append(linha)

    return "\n".join(resultado)


# ---------------------------------------------------------
# 8. REMOVER BLOCOS DUPLICADOS
# ---------------------------------------------------------
def remover_blocos_duplicados(texto):

    frases = texto.split(". ")

    vistas = set()
    resultado = []

    for f in frases:
        f_clean = f.strip().lower()

        if f_clean not in vistas:
            vistas.add(f_clean)
            resultado.append(f)

    return ". ".join(resultado)


# ---------------------------------------------------------
# 9. LIMPAR RUÍDO FINAL
# ---------------------------------------------------------
def limpar_ruido_final(texto):

    texto = re.sub(r'(\d+)\s+Curso\s+\|', r'\1 |', texto)
    texto = re.sub(r'Curso\s+\|\s+Nota', '', texto)
    texto = re.sub(r'(\d+)\s+(No entanto)', r'\1\n\n\2', texto)
    texto = re.sub(r'\n\s+', '\n', texto)

    return texto


# ---------------------------------------------------------
# 11. FORMATAR UI
# ---------------------------------------------------------
def formatar_para_ui(texto):

    texto = re.sub(r'\r\n|\r', '\n', texto)

    texto = re.sub(r'(CAPÍTULO \d+)', r'\n\n\1\n\n', texto)
    texto = re.sub(r'\.\s+', '.\n', texto)
    texto = re.sub(r'(\w)\s+\|\s+(\w)', r'\1 | \2', texto)

    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)

    return texto.strip()


# ---------------------------------------------------------
# 12. PIPELINE PRINCIPAL
# ---------------------------------------------------------
def preparar_para_normalizacao(texto_limpo, tamanho_chunk=1200):

    if not texto_limpo:
        return "desconhecido", [], []

    idioma = detetar_idioma(texto_limpo)
    chunks = chunk_text(texto_limpo, tamanho_chunk, overlap=120)

    prompt = criar_prompt_relatorio()
    prompts = [prompt for _ in chunks]

    return idioma, chunks, prompts
