# 💀 MANUAL KAOS CLI (v8.1.2-stable)

O KAOS CLI é o seu assistente de engenharia terminal-nativo, otimizado para performance, segurança e inteligência local/nuvem.

---

## 🚀 1. INSTALAÇÃO RÁPIDA

Se você acabou de baixar, rode:
```bash
chmod +x install.sh kaos-cli
./install.sh
source ~/.bashrc  # Ou ~/.zshrc
```

---

## 🛠️ 2. COMANDOS BÁSICOS

### Pergunta Simples (Single Shot)
```bash
kaos-cli "Como extrair um arquivo .tar.gz no Linux?"
```

### Análise de Projeto (Contexto Automático)
O KAOS detecta palavras como "analise" ou "revise" e anexa automaticamente a estrutura da pasta atual (respeitando o `.gitignore`).
```bash
kaos-cli analise este projeto e encontre bugs
```

### Ler Arquivo Específico
```bash
kaos-cli --read src/db_manager.py "Como este código salva sessões?"
```

### Modo Especialista em Segurança (Scanner)
Para coletar contexto profundo para auditoria:
```bash
./kaos_scan.sh > contexto.txt
kaos-cli --file contexto.txt "Encontre falhas de segurança neste log"
```

---

## 💬 3. MODO CHAT INTERATIVO

Para entrar no modo de conversa contínua:
```bash
kaos-cli
```

### Comandos dentro do Chat:
- `/help`     : Lista todos os comandos.
- `/model`    : Troca o modelo de IA na hora (ex: `/model gemini-1.5-pro`).
- `/models`   : Lista modelos que você tem instalados/disponíveis.
- `/session`  : Muda de conversa (ex: `/session bug-fix`). Salva tudo no SQLite!
- `/clear`    : Limpa a tela e o histórico da sessão atual.
- `/doctor`   : Verifica se a conexão com o servidor está OK.
- `/exit`     : Sai do chat.

---

## 🔌 4. CONFIGURAÇÃO (`config.env`)

Edite o arquivo `~/.config/kaos-cli/config.env` para mudar o comportamento:

- `KAOS_PROVIDER`: `ollama` (Local/Grátis) ou `gemini` (Nuvem).
- `KAOS_MODEL`: O modelo padrão (ex: `gemini-1.5-flash` ou `qwen2.5-coder`).
- `GOOGLE_API_KEY`: Sua chave do Google AI Studio.
- `OLLAMA_HOST`: Endereço do seu servidor Ollama (Padrão: `http://127.0.0.1:11434`).

---

## ⚡ 5. TRICKS DE PERFORMANCE (Poder do Engenheiro)

### Usar com Pipes (Unix Way)
```bash
cat erro.log | kaos-cli "Explique este erro"
```

### Diagnóstico de Ambiente
```bash
kaos-cli --doctor
```

### Ver Modelos Disponíveis
```bash
kaos-cli --models
```

---

## 🔒 6. SEGURANÇA E PRIVACIDADE

1. **Local Primeiro**: Use `KAOS_PROVIDER=ollama` para garantir que seu código NUNCA saia da sua máquina.
2. **SQLite WAL**: Suas sessões são salvas localmente em `~/.local/share/kaos-cli/sessions.db`.
3. **Filtro de Contexto**: O KAOS ignora automaticamente pastas sensíveis como `.git` e chaves configuradas no seu `.gitignore`.

---
*KAOS CLI - Criado para quem domina o terminal.*
