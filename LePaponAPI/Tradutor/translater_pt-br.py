import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

google_api_key = os.getenv("GEMINI_API_KEY")
if google_api_key is None:
    print("Please set the GEMINI_API_KEY environment variable.")
    sys.exit(1)

genai.configure(api_key=google_api_key)

# --- Configuração ---
MODELO = "gemini-2.5-flash"
IDIOMA_DESTINO = "Português"

def traduzir_texto(texto_para_traduzir):
    """
    Traduz um texto usando a API do Gemini.
    """
    prompt = f"""
    Traduza o seguinte texto para {IDIOMA_DESTINO} de forma profissional e com alta precisão,
    mantendo o tom e as nuances do original. Não inclua comentários adicionais, apenas a tradução.

    TEXTO ORIGINAL:
    ---
    {texto_para_traduzir}
    ---
    """

    try:
        model = genai.GenerativeModel(MODELO)
        response = model.generate_content(prompt)
        if response and response.text:
            return response.text.strip()
        else:
            return "Erro: Resposta vazia ou inválida do modelo"
    except Exception as e:
        return f"Erro na tradução: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python translater_pt-br.py \"texto para traduzir\"")
        sys.exit(1)

    texto = sys.argv[1]
    
    traducao = traduzir_texto(texto)
    print(traducao)