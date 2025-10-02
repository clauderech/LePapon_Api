from google import genai
from google.genai import types
import pathlib
import os
from dotenv import load_dotenv
import json
import re
import argparse

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), './.env'))

google_api_key = os.getenv("GEMINI_API_KEY")
if google_api_key is None:
  print("Please set the GEMINI_API_KEY environment variable.")

client = genai.Client(api_key=google_api_key)

# Retrieve and encode the PDF byte
# Parse CLI args: allow user to provide PDF filename and output JSON filename
parser = argparse.ArgumentParser(description="Extrai dados de produtos de um PDF usando Gemini e salva JSON limpo")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--file", "-f", help="Caminho para o arquivo PDF de entrada")
group.add_argument("--dir", "-d", help="Caminho para diretório contendo PDFs a processar (recursivo)")
parser.add_argument("--output", "-o", default='response.json', help="Arquivo JSON de saída (modo arquivo único)")
parser.add_argument("--out-dir", help="Diretório de saída para múltiplos JSONs (modo diretório)")
parser.add_argument("--sleep", type=float, default=0.5, help="Segundos para dormir entre requests (ajuste para evitar limites)")
args = parser.parse_args()


def process_pdf_file(input_path: pathlib.Path, output_path: pathlib.Path, sleep: float = 0.5):
    """Processa um único PDF com Gemini e salva o JSON parseado em output_path."""
    if not input_path.exists():
        raise FileNotFoundError(f"PDF não encontrado: {input_path}")

    prompt = "Extraia os dados dos produtos do documento (seção 'DADOS DOS PRODUTOS /SERVIÇOS'). Retorne apenas JSON válido."

    response = client.models.generate_content(
      model="gemini-2.5-flash",
      config=types.GenerateContentConfig(
        system_instruction=(
          "Você é um assistente que extrai dados estruturados. "
          "EXIJA que a resposta contenha APENAS um JSON válido (sem texto adicional, sem backticks), "
          "no formato de uma lista de objetos. Cada objeto deve ter as chaves: "
          "'codigo' (string), 'descricao' (string MAXIMO 250), 'unidade' (string), 'qtd' (number), "
          "'qtd_trib' (number), 'preco_unitario_final' (number), 'data' (string YYYY-MM-DD). "
          "Se não houver produtos, retorne a lista vazia: []. "
          "Não inclua comentários, explicações ou marcações. Responda somente com o JSON."
        )
      ),
      contents=[
          types.Part.from_bytes(
            data=input_path.read_bytes(),
            mime_type='application/pdf',
          ),
          prompt])

    resp_text = response.text if response.text is not None else ""
    parsed = parse_gemini_json(resp_text)
    if not isinstance(parsed, list):
        if isinstance(parsed, dict):
            parsed = [parsed]
        else:
            raise ValueError("O JSON retornado não é uma lista nem um objeto JSON válido de produto.")

    # criar diretório pai se necessário
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({"produtos": parsed}, f, ensure_ascii=False, indent=2)

    # pequeno delay para não bombardear a API
    if sleep and sleep > 0:
        import time as _t
        _t.sleep(sleep)


# preparar modo de execução
if args.file:
    filepath = pathlib.Path(args.file)
    output_file = pathlib.Path(args.output)
else:
    dirpath = pathlib.Path(args.dir)
    out_dir = pathlib.Path(args.out_dir) if args.out_dir else None

# A chamada ao modelo é feita dentro de process_pdf_file por arquivo.


def parse_gemini_json(text):
    """Limpa fences como ```json``` e tenta converter em objeto Python.

    Retorna lista/dict em caso de sucesso. Lança ValueError em caso de falha.
    """
    # remover fences ```json``` e backticks
    cleaned = re.sub(r"```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "").strip()
    # desescapar sequências comuns
    cleaned = cleaned.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # tentativa fallback: extrair primeiro bloco JSON entre [] ou {}
        m = re.search(r"(\[.*\]|\{.*\})", cleaned, flags=re.DOTALL)
        if m:
            fragment = m.group(1)
            try:
                return json.loads(fragment)
            except json.JSONDecodeError as e:
                raise ValueError(f"Erro ao parsear fragmento JSON: {e}") from e
        raise ValueError("Não foi possível parsear o texto retornado como JSON.")

resp_text = ""
def _main_single():
  try:
    process_pdf_file(filepath, output_file, sleep=args.sleep)
    print(f"Parse bem-sucedido: arquivo salvo em {output_file}")
  except Exception as e:
    raw_path = f"{output_file}.raw.txt"
    # tentar salvar resposta bruta se houver
    try:
      with open(raw_path, "w", encoding="utf-8") as f:
        f.write("")
    except Exception:
      pass
    print("Falha ao processar:", e)
    print(f"Verifique {raw_path} para conteúdo bruto (se disponível)")


def _main_dir():
  if not dirpath.exists() or not dirpath.is_dir():
    raise NotADirectoryError(f"Diretório inválido: {dirpath}")

  pdfs = sorted([p for p in dirpath.rglob("*.pdf")])
  if not pdfs:
    print("Nenhum PDF encontrado no diretório.")
    return

  errors = []
  for p in pdfs:
    try:
      if out_dir:
        out_path = out_dir / (p.stem + ".json")
      else:
        out_path = p.with_suffix('.json')
      print(f"Processando {p} -> {out_path}")
      process_pdf_file(p, out_path, sleep=args.sleep)
    except Exception as e:
      print(f"Erro processando {p}: {e}")
      errors.append((p, str(e)))

  print(f"Processados: {len(pdfs) - len(errors)}; com falhas: {len(errors)}")
  if errors:
    for p, msg in errors:
      print(f" - {p}: {msg}")


if __name__ == "__main__":
  if args.file:
    _main_single()
  else:
    _main_dir()
