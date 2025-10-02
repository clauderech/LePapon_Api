import requests
import os
import paramiko

class EnviarRelatorioPedido:
    """Responsável por enviar relatório (PDF) de pedidos via WhatsApp e fazer upload no droplet."""
    def __init__(self, token: str, phone_number_id: str):
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"

    # --- Upload / Limpeza no Droplet ---
    def upload_pdf_droplet(self, host: str, usuario: str, caminho_local: str, caminho_remoto: str, caminho_chave: str) -> bool:
        """Envia um PDF local para o droplet via SFTP (chave SSH)."""
        if not os.path.isfile(caminho_local):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_local}")
        key = paramiko.RSAKey.from_private_key_file(caminho_chave)
        transport = paramiko.Transport((host, 22))
        try:
            transport.connect(username=usuario, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            if sftp is None:
                raise Exception("Falha ao criar cliente SFTP.")
            sftp.put(caminho_local, caminho_remoto)
            sftp.close()
        finally:
            transport.close()
        return True

    def delete_all_pdfs_from_folder(self, host: str, usuario: str, pasta_remota: str, caminho_chave: str) -> int:
        """Remove todos PDFs de uma pasta remota para liberar espaço."""
        try:
            key = paramiko.RSAKey.from_private_key_file(caminho_chave)
            transport = paramiko.Transport((host, 22))
            transport.connect(username=usuario, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            if sftp is None:
                transport.close()
                raise ConnectionError("Falha ao criar cliente SFTP.")
            arquivos = sftp.listdir(pasta_remota)
            removidos = 0
            for arq in arquivos:
                if arq.lower().endswith('.pdf'):
                    try:
                        sftp.remove(f"{pasta_remota}/{arq}")
                        removidos += 1
                    except Exception as e:
                        print(f"Erro ao remover {arq}: {e}")
            sftp.close()
            transport.close()
            return removidos
        except Exception as e:
            print(f"Erro ao limpar PDFs: {e}")
            return 0

    # --- Envio WhatsApp ---
    def enviar_pdf(self, numero_cliente: str, pdf_url: str, nome_arquivo: str | None = None):
        """Envia o PDF (link público) via WhatsApp Business API."""
        headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        data = {
            "messaging_product": "whatsapp",
            "to": numero_cliente,
            "type": "document",
            "document": {"link": pdf_url, "filename": nome_arquivo or os.path.basename(pdf_url)}
        }
        resp = requests.post(self.api_url, headers=headers, json=data)
        return resp.json()

