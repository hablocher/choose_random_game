# 🎮 Choose Random Game & Live Stream Assistant

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-PyQt6-green?logo=qt)](https://riverbankcomputing.com/software/pyqt/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)](https://www.microsoft.com/windows)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Aplicativo inteligente para gerenciamento de backlog, sorteio ponderado de jogos e assistente completo para transmissões ao vivo no YouTube.**

Criado especialmente para streamers e gamers com bibliotecas gigantescas (Steam, GOG, Playnite, eXoDOS, emuladores e pastas locais) que nunca sabem o que jogar ou querem transformar a escolha do jogo em uma atração interativa ao vivo com o chat da live!

---

## ✨ Principais Funcionalidades

### 🖥️ Gaming Dashboard PyQt6
- **Interface Dark Gamer**: Layout responsivo moderno com paleta escura, cards iluminados e badges por plataforma.
- **Estatísticas em Tempo Real**: Total do acervo, sessões registradas, taxa de conclusão do backlog e jogos favoritados.
- **Minimização Inteligente**: Ao iniciar qualquer jogo, o dashboard minimiza automaticamente para a barra de tarefas para liberar a tela e recursos do PC.
- **Limpeza Inteligente de Banco**: Varre o disco procurando por jogos desinstalados e remove registros órfãos sem apagar nenhum arquivo pessoal.

### 🎲 Sorteador Geral Ponderado
- **Anti-Repetição / Priorização de Backlog**: O algoritmo favorece jogos que você nunca jogou ou jogou poucas vezes.
- **Filtros Rápidos de Categoria**: Filtre o sorteio por *Playnite*, *eXoDOS*, *Atalhos do Windows* ou *Instalações Locais*.

### 📅 Jogo do Dia (*Game of the Day - GOTD*)
- Sugere diariamente um jogo sorteado **estritamente entre os jogos instalados** no seu computador.

### 🏆 Hall da Fama e Sorteador GOTY (*Game of the Year*)
- Banco de dados histórico completo de vencedores do GOTY de **1983 a 2025** (The Game Awards, Golden Joystick, BAFTA, DICE, etc.).
- Identifica instantaneamente se o clássico premiado já está instalado no seu computador ou permite explorar seu histórico na web.

### 🔴 Suíte Especial para Streamers & YouTube Live
1. **🗳️ Modo Escolha do Chat (Sorteio Triplo para Enquete)**:
   - Sorteia 3 opções distintas de jogos instalados (Opção A, B e C) lado a lado.
   - Botão com 1 clique para copiar o texto pronto da enquete para colar no chat da live do YouTube.
   - Botão para lançar imediatamente a opção vencedora da votação.
2. **🎰 Animação Roleta de Suspense**:
   - Checkbox que ativa um giro acelerado em estilo *slot machine* que desacelera gradualmente antes de travar no jogo sorteado.
3. **🧠 Central de Inteligência do Jogo (*Game Intel Modal*)**:
   - Sinopse oficial resumida via API da Wikipedia em tempo real.
   - Acesso rápido a **GameFAQs**, **IGN Walkthroughs**, **HowLongToBeat**, **PCGamingWiki**, **YouTube Playthroughs** e **Speedrun.com**.
   - Leitor e localizador de manuais locais (`.pdf`, `.txt`, `.doc`) para jogos clássicos e eXoDOS.
4. **🎥 Modo Overlay para OBS Studio / Streamlabs**:
   - Janela compacta *frameless* (`WindowStaysOnTopHint`) projetada para ser capturada via *Window Capture* no OBS.
   - Alternância entre estilos: **Dark Gamer**, **Chroma Green (#00FF00)** e **Chroma Magenta (#FF00FF)**.
5. **📜 Histórico de Transmissões ao Vivo**:
   - Histórico em banco SQLite persistente (`LiveHistory`) com duração, data e anotações sobre cada live realizada.

---

## 🛠️ Pré-requisitos

- **Sistema Operacional**: Windows 10 ou Windows 11 (devido à execução de atalhos `.lnk` e integração com a Steam/Playnite).
- **Python**: Versão **3.10 ou superior** instalada e configurada no `PATH` do sistema.
- **Git** (opcional, para clonar o repositório).

---

## 🚀 Instalação Passo a Passo

### 1. Clonar ou Baixar o Repositório
Abra o PowerShell ou Terminal e clone o repositório:
```bash
git clone https://github.com/hablocher/choose_random_game.git
cd choose_random_game
```

### 2. Criar e Ativar um Ambiente Virtual (Recomendado)
Usando o `venv` padrão do Python:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*Ou usando Anaconda / Miniconda:*
```bash
conda create -n choose_random_game python=3.11 -y
conda activate choose_random_game
```

### 3. Instalar as Dependências
Instale todos os pacotes necessários listados no `requirements.txt`:
```bash
pip install -r requirements.txt
```

As dependências principais incluem:
- `PyQt6`: Interface gráfica moderna do Dashboard.
- `Pillow`: Manipulação e conversão de capas e ícones de jogos.
- `pywin32`: Leitura e resolução de atalhos `.lnk` nativos do Windows.
- `requests`: Consultas a APIs da Steam, GOG e Wikipedia.
- `jellyfish`: Algoritmo de distância Levenshtein para correspondência aproximada de títulos.

---

## ⚙️ Configuração do Arquivo `choose_random_game.ini`

O arquivo `choose_random_game.ini` controla todas as fontes de jogos, diretórios, bancos e preferências de streaming.

Para começar, copie o modelo de exemplo:
```powershell
copy sample-choose_random_game.ini choose_random_game.ini
```

Abra o arquivo `choose_random_game.ini` em seu editor de texto preferido e ajuste as seções:

### 1. Pastas de Jogos Locais `[FOLDERS]`
Indique os diretórios onde seus jogos estão instalados (um por linha):
```ini
[FOLDERS]
path1 = C:\Jogos
path2 = D:\Games
path3 = G:\Steam\steamapps\common
```

### 2. Atalhos do Windows `[SHORTCUTS]`
Indique pastas contendo atalhos `.lnk` e `.url` (como área de trabalho ou pastas personalizadas):
```ini
[SHORTCUTS]
path1 = C:\Users\SeuUsuario\Desktop\ShortcutGames
path2 = G:\AtalhosJogos
```

### 3. Integração com o Playnite `[PLAYNITE]`
Se você usa o **Playnite**, ative a leitura unificada de bibliotecas (Steam, Epic, GOG, Ubisoft, etc.):
```ini
[PLAYNITE]
enabled = true
# Caminho da pasta de instalação do Playnite
path = C:\Users\SeuUsuario\AppData\Local\Playnite
onlyInstalled = true
# Arquivo JSON exportado da biblioteca
exportJson = playnite_games.json
```
> 💡 **Dica Playnite**: Você pode usar o script incluído `export_playnite_library.ps1` para sincronizar automaticamente os metadados e capas da sua biblioteca do Playnite.

### 4. Integração com eXoDOS `[EXODOS]`
Se você possui a coleção clássica eXoDOS instalada:
```ini
[EXODOS]
path = G:\eXoDOS_Lite\eXo\eXoDOS
```

### 5. Steam & GOG `[STEAM]` / `[GOG]`
```ini
[STEAM]
enabled = true
steamPath = C:\Program Files (x86)\Steam

[GOG]
enabled = true
# Caminho opcional para o banco local do GOG Galaxy:
galaxyDbPath = C:\ProgramData\GOG.com\Galaxy\storage\galaxy-2.0.db
```

### 6. Configurações para Streamers `[STREAMER]`
```ini
[STREAMER]
# Ativar animação de roleta no sorteio
rouletteEnabled = true
rouletteDurationMs = 2600

# Cor padrão da janela OBS: 'dark', 'green' (Chroma Key) ou 'magenta'
overlayChromaKey = dark

# Canais do YouTube (opcional)
youtubeMainChannel = https://www.youtube.com/@SeuCanalPrincipal
youtubeLiveChannel = https://www.youtube.com/@SeuCanalDeLives
```

---

## 🎮 Como Executar

### Opção 1: Via Python
```bash
python choose_random_game.py
```

### Opção 2: Via Script de Inicialização Rápida no Windows
Dê um duplo clique no arquivo:
```cmd
choose_game.cmd
```

---

## 🎥 Como Usar no OBS Studio (Transmissões ao Vivo)

Para exibir o jogo sorteado ao vivo na sua transmissão sem mostrar a janela inteira do aplicativo:

1. No Dashboard, clique no botão **"🎥 Overlay OBS"** no topo da tela.
2. Uma janela compacta, sem bordas (*frameless*) e sempre no topo será aberta.
3. No **OBS Studio**:
   - Adicione uma nova fonte: **Captura de Janela** (*Window Capture*).
   - Selecione a janela `Choose Random Game - OBS Overlay`.
   - Método de captura: *Windows 10 (1903 e superior)* ou *Automático*.
4. **Filtro de Transparência (Chroma Key)**:
   - Se preferir fundo transparente, clique no botão **"🟩 Verde"** ou **"🟪 Magenta"** no topo da janelinha do overlay.
   - No OBS, clique com o botão direito na fonte de Captura de Janela > **Filtros** > Adicionar **Chroma Key**.
   - Escolha a cor correspondente (Verde ou Magenta).
   - O fundo desaparecerá instantaneamente, deixando apenas a capa e o título flutuando de forma elegante na tela da live!

---

## 📂 Estrutura do Projeto

```text
choose_random_game/
├── aesgard/                     # Módulos centrais do aplicativo
│   ├── config.py                # Gerenciador de configurações (.ini)
│   ├── covers.py                # Sistema de busca em cascata de capas (Playnite -> GOG -> Steam -> Wikipedia)
│   ├── dashboard.py             # Interface visual PyQt6 (5 Views integradas)
│   ├── database.py              # Camada de banco de dados SQLite (Games, Goty, Stats)
│   ├── game_intel.py            # Consulta a sinopses e guias externos
│   ├── gameutil.py              # Execução de jogos, detecção de atalhos e sorteio ponderado
│   ├── gog.py                   # Integração e capas via catálogo GOG
│   ├── goty.py                  # Hall da Fama e lógica do Jogo do Ano (1983-2025)
│   ├── intel_dialog.py          # Modal com detonados, manuais e dicas
│   ├── playnite.py              # Leitura de banco e metadados do Playnite
│   ├── steam.py                 # Integração com API da Steam Store
│   ├── streamer.py              # Gerenciador de histórico de lives e Overlay OBS
│   ├── ui.py                    # Formatação de títulos e badges de plataformas
│   └── winicon.py               # Extrator de ícones de executáveis e atalhos Windows
├── choose_random_game.ini       # Arquivo de configuração ativo do usuário
├── sample-choose_random_game.ini# Modelo de configuração comentado
├── choose_random_game.py        # Ponto de entrada principal da aplicação
├── choose_game.cmd              # Script batch para lançamento rápido no Windows
├── export_playnite_library.ps1  # Script PowerShell para integração com Playnite
├── requirements.txt             # Lista de dependências Python
└── README.md                    # Documentação completa
```

---

## ❓ Perguntas Frequentes (FAQ)

### 1. O jogo sorteado não abre ao clicar em "Jogar". O que fazer?
- Verifique se o jogo ainda está instalado no diretório indicado no arquivo `.ini`.
- Caso seja um atalho `.lnk`, verifique se o destino original do atalho ainda existe.
- Clique no botão **"🧹 Limpar Banco"** no Dashboard para sincronizar o banco com os jogos realmente instalados no momento.

### 2. A capa de um jogo está aparecendo em branco ou com ícone genérico. Como resolver?
- O aplicativo possui busca em cascata automática:
  1. Banco de capas local do Playnite;
  2. Catálogo online oficial do GOG;
  3. API pública da Steam Store;
  4. Wikipedia OpenSearch;
  5. Extração nativa do ícone do executável `.exe`.
- Certifique-se de que sua máquina está conectada à internet para permitir a busca de capas que não estão instaladas localmente.

### 3. Posso usar um banco de dados MySQL ou SQL Server em vez de SQLite?
- Sim! O arquivo `sample-choose_random_game.ini` possui exemplos comentados de configuração para servidores MySQL e SQL Server na seção `[DATABASE]`. Por padrão, o SQLite (`Games.db`) é usado localmente sem necessidade de configuração de servidor.

---

## 🤝 Contribuições

Contribuições são muito bem-vindas! Sinta-se à vontade para abrir uma *Issue* ou enviar um *Pull Request*:
1. Faça um Fork do projeto
2. Crie uma branch para sua funcionalidade (`git checkout -b feature/minha-melhoria`)
3. Faça o commit de suas alterações (`git commit -m "feat: minha melhoria"`)
4. Faça o push para a branch (`git push origin feature/minha-melhoria`)
5. Abra um Pull Request

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.

Desenvolvido com carinho para a comunidade gamer, criadores de conteúdo e streamers! 🎮
