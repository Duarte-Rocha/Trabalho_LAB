import re

# ---------------------------------------------------------
# 1. Remover artefactos e símbolos estranhos
# ---------------------------------------------------------
def remover_artefactos(texto):
    # Remove bullets e símbolos comuns de OCR
    texto = re.sub(r"[■□�•●▪◦·]", " ", texto)

    # Remove tags HTML simples e preserva o texto interno
    texto = re.sub(r"<br\s*/?>", "\n", texto, flags=re.IGNORECASE)
    texto = re.sub(r"<[^>]+>", " ", texto)

    # Remove "Página X" ou "Página X/Y"
    texto = re.sub(r"Página\s+\d+(/\d+)?", "", texto, flags=re.IGNORECASE)

    # Remove linhas de separadores
    texto = re.sub(r"[-=]{3,}", "", texto)

    # Mantém acentos, remove caracteres inválidos
    texto = re.sub(r"[^\wÀ-ÿ.,;:!?()\n|/\- ]", " ", texto)

    return texto


def _linha_tabela(linha):
    if "|" in linha:
        return True

    partes = re.split(r"\s{2,}", linha.strip())
    if len(partes) >= 3 and any(re.search(r"\d", parte) for parte in partes):
        return True

    return False


# ---------------------------------------------------------
# 2. Normalizar espaços
# ---------------------------------------------------------
def normalizar_espacos(texto):
    texto = re.sub(r"[ ]{2,}", " ", texto)
    texto = re.sub(r"\t+", " ", texto)
    return texto.strip()


# ---------------------------------------------------------
# 3. Corrigir quebras de linha (sem destruir parágrafos)
# ---------------------------------------------------------
def corrigir_quebras(texto):
    texto = texto.replace("\r", "")
    # Máximo 2 quebras seguidas
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto


# ---------------------------------------------------------
# 4. Remover cabeçalhos e rodapés repetidos
# ---------------------------------------------------------
def remover_cabecalhos_rodapes(texto):
    linhas = texto.split("\n")
    filtradas = []

    padroes = [
        r"UNIVERSIDADE .*",
        r"Relatório Técnico .*",
        r"202\d/202\d",
        r"V\d\.\d \| \d{8}",
    ]

    for linha in linhas:
        if any(re.match(p, linha.strip(), re.IGNORECASE) for p in padroes):
            continue
        filtradas.append(linha)

    return "\n".join(filtradas)


# ---------------------------------------------------------
# 5. Remover linhas duplicadas
# ---------------------------------------------------------
def remover_linhas_duplicadas(texto):
    linhas = texto.split("\n")
    vistas = set()
    resultado = []

    for linha in linhas:
        key = linha.strip().lower()
        if key and key not in vistas:
            resultado.append(linha)
            vistas.add(key)

    return "\n".join(resultado)


# ---------------------------------------------------------
# 6. Preservar tabelas (não destrutivo)
# ---------------------------------------------------------
def preservar_tabelas(texto):
    # Mantém colunas alinhadas
    texto = re.sub(r"\s*\|\s*", " | ", texto)

    # Evita juntar linhas de tabela com texto normal
    texto = re.sub(r"(\|)", r" \1 ", texto)

    return texto


# ---------------------------------------------------------
# 7. Normalizar pontuação (seguro)
# ---------------------------------------------------------
def normalizar_pontuacao(texto):
    texto = re.sub(r"\s+([.,;:!?])", r"\1", texto)
    texto = re.sub(r"([.,;:!?])(?=[A-Za-zÀ-ÿ])", r"\1 ", texto)
    texto = re.sub(r"(\d)\s*\.\s*(\d)", r"\1.\2", texto)
    return texto


# ---------------------------------------------------------
# 8. Reconstruir parágrafos (sem colar tudo)
# ---------------------------------------------------------
def reconstruir_paragrafos(texto):
    linhas = texto.split("\n")
    paragrafos = []
    buffer = ""

    for linha in linhas:
        linha = linha.strip()

        # Linha vazia → fecha parágrafo
        if not linha:
            if buffer:
                paragrafos.append(buffer.strip())
                buffer = ""
            continue

        # Títulos (não juntar)
        if re.match(r"(CAP[IÍ]TULO|Sec[cç]ão|#)", linha, re.IGNORECASE):
            if buffer:
                paragrafos.append(buffer.strip())
                buffer = ""
            paragrafos.append(linha)
            continue

        # Linhas de tabela → não juntar
        if _linha_tabela(linha):
            if buffer:
                paragrafos.append(buffer.strip())
                buffer = ""
            paragrafos.append(linha)
            continue

        # Junta linhas normais
        if buffer:
            buffer += " " + linha
        else:
            buffer = linha

    if buffer:
        paragrafos.append(buffer.strip())

    return "\n\n".join(paragrafos)


# ---------------------------------------------------------
# 9. PIPELINE FINAL (ordem otimizada)
# ---------------------------------------------------------
def limpar_texto(texto):
    texto = remover_artefactos(texto)
    texto = corrigir_quebras(texto)
    texto = remover_cabecalhos_rodapes(texto)
    texto = remover_linhas_duplicadas(texto)
    texto = preservar_tabelas(texto)
    texto = reconstruir_paragrafos(texto)
    texto = normalizar_pontuacao(texto)
    texto = normalizar_espacos(texto)
    return texto
