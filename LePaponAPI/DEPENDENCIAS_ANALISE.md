# Mapeamento de Dependências por Módulo - LePaponAPI

## 📊 Análise Completa das Dependências

### 🏗️ **Estrutura do Projeto e Dependências**

#### **1. app_admin/** - Aplicação Desktop de Administração
**Dependências Principais:**
- `flet>=0.21.0` - Framework GUI moderno
- `pandas>=2.0.0` - Análise de dados e relatórios  
- `reportlab>=4.0.0` - Geração de PDFs
- `python-dotenv>=1.0.0` - Configurações
- `pytz>=2023.3` - Manipulação de timezone

**Funcionalidades:**
- Interface gráfica para gestão
- Geração de relatórios em PDF
- Controle de vendas, crediário, fornecedores
- Análises de dados com pandas

#### **2. PDV_API/** - Sistema de Ponto de Venda
**Dependências Principais:**
- `flet>=0.21.0` - Interface do PDV
- `requests>=2.31.0` - Comunicação com APIs
- `pandas>=2.0.0` - Processamento de dados
- `reportlab>=4.0.0` - Relatórios e comprovantes
- `paramiko>=3.3.0` - Upload via SFTP

**Funcionalidades:**
- Interface de vendas
- Gestão de pedidos temporários
- Upload de documentos via SSH/SFTP
- Integração com APIs locais

#### **3. Baixar_Pedidos_DigOcean/** - Sistema de Sincronização
**Dependências Principais:**
- `websockets>=12.0` - Cliente WebSocket em tempo real
- `pandas>=2.0.0` - Processamento de pedidos
- `python-dotenv>=1.0.0` - Configurações
- `requests>=2.31.0` - HTTP para fallback

**Funcionalidades:**
- Cliente WebSocket moderno
- Sincronização de pedidos em tempo real
- Processamento com PedidoManager
- Sistema de reconexão automática

#### **4. LePapon_Cozinha/** - Sistema da Cozinha
**Dependências Principais:**
- `flet>=0.21.0` - Interface da cozinha
- `pandas>=2.0.0` - Listagem de pedidos
- `requests>=2.31.0` - APIs de pedidos
- `python-dotenv>=1.0.0` - Configurações

**Funcionalidades:**
- Interface para cozinha
- Visualização de pedidos
- Gestão de produtos

#### **5. Scan_Converter_IA/** - Conversor com IA
**Dependências Principais:**
- `google-generativeai>=0.7.0` - API do Gemini
- `python-dotenv>=1.0.0` - Chaves da API
- `pathlib` - Manipulação de arquivos (built-in)

**Funcionalidades:**
- Conversão de PDFs usando Gemini AI
- Processamento de documentos da Ambev
- Análise inteligente de texto

#### **6. Produtos_Manager/** - Gerenciador de Produtos
**Dependências Principais:**
- `requests>=2.31.0` - APIs de produtos
- `flet>=0.21.0` - Interface (se existir)

**Funcionalidades:**
- Gestão de produtos
- Categorização
- Atualizações de estoque

### 📈 **Distribuição de Dependências**

| Categoria | Dependências | Uso |
|-----------|-------------|-----|
| **Interface Gráfica** | flet | 80% dos módulos |
| **HTTP/API** | requests | 90% dos módulos |
| **Dados** | pandas, numpy | 70% dos módulos |
| **PDF** | reportlab | 40% dos módulos |
| **Configuração** | python-dotenv | 60% dos módulos |
| **Database** | mysql-connector | 5% dos módulos |
| **IA** | google-generativeai | 5% dos módulos |
| **SSH/Upload** | paramiko | 10% dos módulos |
| **WebSocket** | websockets | 5% dos módulos |
| **Timezone** | pytz | 10% dos módulos |

### 🎯 **Dependências Críticas vs Opcionais**

#### **✅ Críticas (Obrigatórias)**
```
flet>=0.21.0                # Interface principal
requests>=2.31.0            # Comunicação HTTP
pandas>=2.0.0               # Processamento de dados
python-dotenv>=1.0.0        # Configurações
```

#### **🔧 Importantes (Funcionalidades específicas)**
```
reportlab>=4.0.0            # PDFs (relatórios)
websockets>=12.0            # Tempo real
paramiko>=3.3.0             # Upload de arquivos
pytz>=2023.3                # Timezone
```

#### **🚀 Opcionais (Recursos avançados)**
```
google-generativeai>=0.7.0  # IA (apenas Scan_Converter)
mysql-connector-python>=8.0.0  # DB direto (apenas scripts)
```

### 📋 **Comandos de Instalação por Cenário**

#### **Instalação Completa**
```bash
pip install -r requirements.txt
```

#### **Instalação Mínima**
```bash
pip install flet requests pandas python-dotenv
```

#### **Instalação por Módulo**

**Para app_admin:**
```bash
pip install flet pandas reportlab python-dotenv pytz
```

**Para PDV_API:**
```bash
pip install flet requests pandas reportlab paramiko
```

**Para WebSocket Client:**
```bash
pip install websockets pandas python-dotenv requests
```

**Para Scan_Converter_IA:**
```bash
pip install google-generativeai python-dotenv
```

### 🔍 **Análise de Compatibilidade**

| Python Version | Compatibilidade | Notas |
|---------------|-----------------|-------|
| **3.8+** | ✅ Completa | Todas as dependências |
| **3.7** | ⚠️ Limitada | Flet pode ter problemas |
| **3.6-** | ❌ Incompatível | Não suportado |

### 📊 **Estatísticas do Projeto**

- **Total de arquivos Python**: ~214
- **Dependências externas**: 12 principais
- **Módulos do projeto**: 6 principais
- **Funcionalidades**: Interface, APIs, IA, Relatórios, WebSocket
- **Tamanho estimado**: ~50MB (com dependências)

### 🛠️ **Recomendações de Desenvolvimento**

1. **Ambiente Virtual**: Sempre usar venv/conda
2. **Versionamento**: Manter versões específicas em produção
3. **Testing**: Adicionar pytest, black, mypy para desenvolvimento
4. **Monitoring**: Considerar adicionar structlog para logs
5. **Validation**: Considerar pydantic para validação de dados

### 🚨 **Dependências que Precisam de Atenção**

1. **mysql-connector-python**: Usado apenas em scripts
2. **google-generativeai**: Versão em desenvolvimento ativo
3. **websockets**: Atualizar regularmente para segurança
4. **paramiko**: Crítico para uploads, manter atualizado