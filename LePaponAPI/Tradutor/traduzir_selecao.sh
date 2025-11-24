# Instale as dependências no Ubuntu se ainda não as tiver
#sudo apt install xclip libnotify-bin

# Crie um script shell wrapper, por exemplo: /usr/local/bin/traduzir_selecao
#!/bin/bash

# 1. Captura o texto selecionado (copiado)
TEXTO_SELECIONADO=`xclip -o -selection clipboard`

if [ -z "$TEXTO_SELECIONADO" ]; then
    notify-send "Tradutor Gemini" "Nenhum texto copiado para tradução."
    exit 1
fi

# 2. Executa o script Python
# ATENÇÃO: Substitua /caminho/para/seu/script/tradutor_gemini.py pelo caminho real
TRADUCAO=$(/home/claus/Projetos/Python/LePapon_Api/.venv/bin/python LePaponAPI/Tradutor/translater_pt-br.py "$TEXTO_SELECIONADO")

echo "$TRADUCAO" > LePaponAPI/Tradutor/traducao_gemini.txt
# 3. Exibe o resultado como uma notificação pop-up
notify-send "Tradução Gemini (Feita por Você)" "$TRADUCAO"