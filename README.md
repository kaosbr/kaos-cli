# kaos-cli (Ollama local, pronto para Kali)

CLI local para conversar com o Ollama, analisar projetos e trabalhar sem depender de API paga.

## O que ele faz melhor

- entende prompt sem aspas em casos normais: `kaos-cli analise este projeto`
- entra em chat interativo quando voce executa `kaos-cli` sem argumentos
- le prompt de arquivo ou `stdin`, evitando o erro `argument list too long` do zsh
- detecta quando voce quer analisar o projeto atual e anexa contexto automaticamente
- resolve modelo automaticamente se o configurado nao existir
- persiste sessoes opcionais para continuar uma conversa tecnica
- nao precisa de `pip install`; usa so Python padrao

## Instalar

```bash
chmod +x install.sh uninstall.sh kaos-cli
./install.sh
export PATH="$HOME/.local/bin:$PATH"
hash -r
```

## Uso rapido

### Chat interativo

```bash
kaos-cli
```

### Pergunta simples sem aspas

```bash
kaos-cli analise este projeto e aponte falhas
```

### Analisar a pasta atual com contexto automatico

```bash
kaos-cli revise este projeto com foco em seguranca
```

### Anexar projeto explicitamente

```bash
kaos-cli --project . encontre bugs, riscos e melhorias
```

### Anexar arquivo explicitamente

```bash
kaos-cli --read main.py explique este codigo e corrija falhas
```

### Prompt grande por pipe

```bash
{
  echo "Analise este projeto e devolva um plano de correcao"
  echo
  find . -maxdepth 3 -type f | sort
} | kaos-cli
```

### Prompt a partir de arquivo

```bash
kaos-cli --file prompt.txt
```

### Listar modelos instalados

```bash
kaos-cli --models
```

### Diagnosticar ambiente

```bash
kaos-cli --doctor
```

## Comandos do modo interativo

- `/help`
- `/clear`
- `/model [nome]`
- `/models`
- `/think off|low|medium|high`
- `/context on|off`
- `/project [caminho]`
- `/read <arquivo>`
- `/session <nome>`
- `/doctor`
- `/exit`

## Validacao local incluida no pacote

Dentro da pasta `tests/` ha um mock compatível com a API do Ollama e um script de teste. Isso permite validar:

- instalacao em `~/.local/bin`
- leitura de prompt sem aspas
- leitura por `stdin`
- autodeteccao e fallback de modelo
- anexo automatico de contexto de projeto

Rode assim:

```bash
python3 tests/run_tests.py
```

## Remover

```bash
./uninstall.sh
```
