import requests
import os
import paramiko

class EnviarContaCliente:
    def __init__(self, token, phone_number_id):
        self.token = token
        self.phone_number_id = phone_number_id
        self.api_url = f"https://graph.facebook.com/v19.0/{self.phone_number_id}/messages"

    def upload_pdf_droplet(self, host, usuario, caminho_local, caminho_remoto, caminho_chave):
        """
        Faz upload do PDF para o droplet via SFTP usando chave SSH.
        - host: IP ou domínio do droplet
        - usuario: usuário SSH
        - caminho_local: caminho do PDF local
        - caminho_remoto: caminho destino no droplet (ex: /var/www/html/arquivo.pdf)
        - caminho_chave: caminho da chave privada SSH
        """
        if not os.path.isfile(caminho_local):
            raise FileNotFoundError(f"Arquivo não encontrado: {caminho_local}")
        key = paramiko.RSAKey.from_private_key_file(caminho_chave)
        transport = paramiko.Transport((host, 22))
        try:
            transport.connect(username=usuario, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            if sftp is None:
                raise Exception("Falha ao criar o cliente SFTP. Verifique a conexão e as credenciais.")
            sftp.put(caminho_local, caminho_remoto)
            sftp.close()
        finally:
            transport.close()
        return True

    def enviar_pdf(self, numero_cliente, pdf_url, nome_arquivo=None):
        """
        Envia um PDF para o número do cliente via WhatsApp Business API.
        - numero_cliente: string, no formato internacional (ex: 5599999999999)
        - pdf_url: URL pública do PDF
        - nome_arquivo: nome do arquivo a ser exibido no WhatsApp (opcional)
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": numero_cliente,
            "type": "document",
            "document": {
                "link": pdf_url,
                "filename": nome_arquivo or os.path.basename(pdf_url)
            }
        }
        response = requests.post(self.api_url, headers=headers, json=data)
        return response.json()

    def delete_all_pdfs_from_folder(self, host, usuario, pasta_remota, caminho_chave):
        """
        Remove todos os arquivos PDF de uma pasta específica no droplet via SFTP.
        - host: IP ou domínio do droplet
        - usuario: usuário SSH
        - pasta_remota: caminho da pasta no droplet onde estão os PDFs
        - caminho_chave: caminho da chave privada SSH
        """
        try:
            key = paramiko.RSAKey.from_private_key_file(caminho_chave)
            transport = paramiko.Transport((host, 22))
            transport.connect(username=usuario, pkey=key)
            sftp = paramiko.SFTPClient.from_transport(transport)
            if sftp is None:
                transport.close()
                raise ConnectionError("Falha ao criar o cliente SFTP. Verifique as credenciais e a conexão.")
            
            # Lista todos os arquivos da pasta
            arquivos = sftp.listdir(pasta_remota)
            pdfs_removidos = 0
            
            for arquivo in arquivos:
                if arquivo.lower().endswith('.pdf'):
                    caminho_arquivo = f"{pasta_remota}/{arquivo}"
                    try:
                        sftp.remove(caminho_arquivo)
                        pdfs_removidos += 1
                        print(f"PDF removido: {arquivo}")
                    except Exception as e:
                        print(f"Erro ao remover {arquivo}: {e}")
            
            sftp.close()
            transport.close()
            return pdfs_removidos
        except Exception as e:
            print(f"Erro ao limpar pasta de PDFs: {e}")
            return 0