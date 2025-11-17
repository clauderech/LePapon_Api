import os
import sys
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../../.env'))

google_api_key = os.getenv("GEMINI_API_KEY")
if google_api_key is None:
  print("Please set the GEMINI_API_KEY environment variable.")

genai.configure(api_key=google_api_key)

# --- Configuração ---
# O modelo gemini-2.5-flash é rápido e excelente para tarefas de tradução.
MODELO = "gemini-2.5-flash"
IDIOMA_DESTINO = "Português" # Você pode mudar para o idioma que mais usa

def traduzir_texto(texto_para_traduzir):
    """
    Traduz um texto usando a API do Gemini.
    """
    try:
        # A chave de API é lida automaticamente da variável de ambiente GEMINI_API_KEY
        genai.configure(api_key=google_api_key)
    except Exception as e:
        return f"Erro ao inicializar o cliente Gemini. Certifique-se de que a variável GEMINI_API_KEY está definida. Erro: {e}"

    # Prompt para o Gemini, focado em alta qualidade e contexto
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
        print("Uso: python tradutor_gemini.py \"texto para traduzir\"")
        sys.exit(1)

    # O texto a ser traduzido é o primeiro argumento da linha de comando
    texto = sys.argv[1]
    
    traducao = traduzir_texto(texto)
    print(traducao)