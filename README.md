# kaos-cli (Assistente IA Local e de Terminal)

O `kaos-cli` é uma ferramenta de linha de comando leve e interativa desenhada para atuar como o seu assistente de inteligência artificial diretamente no terminal. Ele foi construído para funcionar integrado com o **Ollama** (para rodar LLMs localmente de forma privada e gratuita) ou com a API do **Gemini**, e é capaz de analisar projetos inteiros, fazer code review e auxiliar em tarefas de engenharia sem dependências pesadas.

## O que ele faz e seus benefícios

- **Zero dependências extras**: Feito em Python purista. Não exige `pip install` nem pacotes externos.
- **Leitura Inteligente de Prompts**: Você não precisa colocar sua pergunta entre aspas. Exemplo: `kaos-cli analise este projeto e aponte falhas` funciona diretamente.
- **Análise Automática de Projeto**: Ao pedir revisões ou análises estando em um diretório (ex: `kaos-cli revise este codigo`), ele mapeia arquivos importantes, respeita seu `.gitignore`, e cria um contexto de código automático para enviar ao modelo.
- **Modo Chat Interativo**: Execute apenas `kaos-cli` para abrir um terminal com chat interativo contínuo, útil para sessões prolongadas de debug.
- **Memória Persistente**: Salva conversas em sessões nomeadas usando SQLite nativo para que você possa continuar projetos do mesmo ponto mais tarde.
- **Tolerância a falhas (Fallback)**: Se você configurar o uso do modelo `qwen2.5-coder:latest` mas tiver apenas o `qwen2.5-coder` instalado, ele detecta e ajusta automaticamente.
- **Pipeline e Stdin**: Permite encadear comandos Linux via pipe (ex: `cat log.txt | kaos-cli o que deu erro aqui?`).

## Instalação

A instalação adiciona os scripts ao seu ambiente local (na pasta `~/.local/bin`), permitindo que você rode o CLI de qualquer lugar.

```bash
chmod +x install.sh uninstall.sh kaos-cli
./install.sh
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

## Guia de Uso

### 1. Chat Interativo Contínuo
Basta rodar sem parâmetros. Ótimo para manter um diálogo longo sobre um problema.
```bash
kaos-cli
```
Dentro do chat interativo, você pode usar os seguintes comandos:
- `/help`: Mostra a lista de comandos disponíveis.
- `/clear`: Limpa a tela e o histórico da sessão atual.
- `/model [nome]`: Troca o modelo que está sendo usado.
- `/models`: Lista os modelos disponíveis.
- `/session [nome]`: Cria ou alterna para uma sessão específica, isolando contextos.
- `/doctor`: Mostra o status da conexão e provedor.
- `/exit`: Sai do modo chat.

### 2. Comandos Diretos (One-shots)
Faça uma pergunta diretamente no terminal sem usar aspas.
```bash
kaos-cli como centralizar uma div no CSS?
```

### 3. Contexto de Projeto Automático e Explícito
O CLI sabe ler arquivos. Você pode anexar arquivos ou diretórios para o modelo analisar.

**Anexando um único arquivo:**
```bash
kaos-cli --read main.py explique este codigo e sugira testes
```

**Anexando um diretório inteiro:**
O CLI vai mapear a árvore e ler arquivos relevantes (ignorando `.git`, `node_modules` e obedecendo o `.gitignore`).
```bash
kaos-cli --project . procure por vulnerabilidades neste projeto
```

**Auto-contexto:**
Se a sua frase contiver palavras como "analise" ou "revise", ele assume `--project .` automaticamente.
```bash
kaos-cli revise este projeto
```

### 4. Integração com o fluxo do Linux (Pipes / Stdin)
Você pode injetar o resultado de outros comandos no CLI para ele interpretar, por exemplo para analisar logs de erro:
```bash
{
  echo "Analise o projeto e crie um plano de refatoracao"
  echo "Arquivos alterados recentemente:"
  git diff --name-only HEAD~1
} | kaos-cli
```
Outro exemplo, lendo um arquivo direto pro stdin:
```bash
cat relatorio.txt | kaos-cli resuma os pontos principais
```

### 5. Lendo prompt de um arquivo
Se o seu prompt for muito grande para ser digitado, use um arquivo `.txt`.
```bash
kaos-cli --file prompt_complexo.txt
```

### 6. Utilitários
Listar os modelos do Ollama/Gemini que você tem acesso:
```bash
kaos-cli --models
```

Diagnosticar a configuração atual do seu ambiente (Provedor, Modelo, Servidor Local):
```bash
kaos-cli --doctor
```

## Configurações

O comportamento do CLI pode ser customizado via variáveis de ambiente ou criando um arquivo chamado `config.env` no diretório em que está trabalhando ou em `~/.config/kaos-cli/config.env`.

Exemplo de arquivo `config.env`:
```env
# Define se usa o Ollama local ou a API do Gemini
KAOS_PROVIDER=ollama
# O nome do modelo que será usado por padrão (ex: qwen2.5-coder, llama3)
KAOS_MODEL=qwen2.5-coder:latest
# URL onde o Ollama está rodando (padrão é localhost:11434)
OLLAMA_HOST=http://127.0.0.1:11434
# Instruções base (System Prompt) dadas ao modelo
KAOS_SYSTEM_PROMPT="Você é um assistente sênior especialista em cybersegurança e engenharia de software."
# Opcional: Se for usar gemini, coloque sua chave aqui
GOOGLE_API_KEY="AIza..."
```

## Como Desinstalar

Para remover a ferramenta do seu sistema:
```bash
./uninstall.sh
```

## Rodando os Testes
Se você deseja contribuir ou checar a sanidade das modificações, pode rodar o conjunto de testes incluso:
```bash
python3 tests/run_tests.py
```
