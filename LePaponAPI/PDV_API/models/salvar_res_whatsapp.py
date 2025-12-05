import requests
from typing import Optional, Dict, Any


class WhatsAppMessageSaver:
    """
    Classe para salvar mensagens do WhatsApp no servidor.
    """
    
    def __init__(self, api_url: str, api_key: str):
        """
        Inicializa o salvador de mensagens do WhatsApp.
        
        Args:
            api_url: URL da API para enviar mensagens
            api_key: Chave de autenticação da API
        """
        self.api_url = api_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "X-API-KEY": self.api_key
        }
    
    def save_message(
        self,
        session_id: str,
        text: str,
        whatsapp_message_id: str,
        media_type: str = "document",
        media_url: Optional[str] = None,
        local_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Salva uma mensagem do WhatsApp no servidor.
        
        Args:
            session_id: ID da sessão (número de telefone)
            text: Texto da mensagem
            whatsapp_message_id: WAMID recebido do WhatsApp
            media_type: Tipo de mídia (padrão: "document")
            media_url: URL da mídia no WhatsApp
            local_filename: Nome do arquivo local
            
        Returns:
            Resposta da API em formato JSON
            
        Raises:
            requests.exceptions.RequestException: Se houver erro na requisição
        """
        payload = {
            "session_id": session_id,
            "text": text,
            "whatsapp_message_id": whatsapp_message_id,
            "media_type": media_type
        }
        
        if media_url:
            payload["media_url"] = media_url
        
        if local_filename:
            payload["local_filename"] = local_filename
        
        response = requests.post(self.api_url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        return response.json()
    
    def save_pdf_message(
        self,
        session_id: str,
        whatsapp_message_id: str,
        pdf_title: str,
        media_url: str,
        local_filename: str
    ) -> Dict[str, Any]:
        """
        Salva uma mensagem de PDF do WhatsApp.
        
        Args:
            session_id: ID da sessão (número de telefone)
            whatsapp_message_id: WAMID recebido do WhatsApp
            pdf_title: Título do PDF
            media_url: URL do PDF no WhatsApp
            local_filename: Nome do arquivo PDF local
            
        Returns:
            Resposta da API em formato JSON
        """
        text = f"[PDF: {pdf_title}]"
        
        return self.save_message(
            session_id=session_id,
            text=text,
            whatsapp_message_id=whatsapp_message_id,
            media_type="document",
            media_url=media_url,
            local_filename=local_filename
        )


# Exemplo de uso
if __name__ == "__main__":
    # Configuração
    API_URL = "https://seu-servidor.com/direct-message"
    API_KEY = "sua-api-key"
    
    # Instanciar a classe
    saver = WhatsAppMessageSaver(api_url=API_URL, api_key=API_KEY)
    
    # Exemplo: Salvar mensagem de PDF após enviar via WhatsApp
    try:
        response = saver.save_pdf_message(
            session_id="5511999999999",
            whatsapp_message_id="wamid.HBgNNTU...",
            pdf_title="Conta Cliente - Janeiro/2025",
            media_url="https://cdn.whatsapp.com/...",
            local_filename="conta_cliente.pdf"
        )
        print("Mensagem salva com sucesso:", response)
    except requests.exceptions.RequestException as e:
        print(f"Erro ao salvar mensagem: {e}")