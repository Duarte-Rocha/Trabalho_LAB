import requests

def enviar_para_slm(prompt, chunk):
    url = "https://reality.utad.net/slm"

    # Garantir valores
    prompt = prompt or ""
    chunk = chunk or ""

    payload = {
        "model": "llama-3-8b-instruct",
        "messages": [
            {
                "role": "system",
                "content": prompt   # ✅ instruções
            },
            {
                "role": "user",
                "content": chunk   # ✅ só texto
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120)

        if response.status_code != 200:
            return "Erro na API"

        resposta_json = response.json()

        if "choices" not in resposta_json:
            return "Erro na API"

        return resposta_json["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        return "Erro: timeout na API"

    except:
        return "Erro: falha na API"
