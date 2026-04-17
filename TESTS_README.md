# KAOS-CLI: Test Suite (Enterprise v4.0)

Este diretório contém a infraestrutura de testes automatizados para validação do `kaos-cli` em ambientes Kali Linux e outros sistemas POSIX.

## Arquitetura de Testes

A suíte de testes é composta por dois componentes principais:
1. **`mock_ollama.py`**: Um servidor HTTP minimalista que simula a API do Ollama (endpoints `/api/tags` e `/api/chat`). Ele permite testar a lógica da CLI sem consumir recursos de GPU ou depender de modelos baixados.
2. **`run_tests.py`**: O orquestrador que:
   - Valida a sintaxe de todos os scripts (`python` e `bash`).
   - Cria um ambiente isolado (`TEMP_HOME`) para não sujar o sistema do usuário.
   - Executa o processo de instalação real via `install.sh`.
   - Dispara comandos contra o Mock Server e valida os outputs via Regex/Assertions.

## Como Executar

Para rodar a suíte completa de testes, execute o comando abaixo na raiz do projeto:

```bash
python3 tests/run_tests.py
```

## O que é validado?

O script de teste cobre os seguintes cenários críticos:
- **Instalação**: Verificação se o binário é movido corretamente para `~/.local/bin` e se o wrapper é funcional.
- **Fallback de Modelo**: Se o modelo configurado não existe, a CLI deve detectar e sugerir/usar um disponível no Mock.
- **Contexto Automático**: Valida se a flag `--project` ou a detecção automática de diretório anexa o contexto do projeto corretamente no prompt enviado.
- **Buffer de STDIN**: Teste de envio de grandes volumes de dados (12KB+) via pipe para garantir que não há estouro de argumento no shell.
- **Diagnóstico**: Execução do comando `--doctor` para validar integridade do ambiente.

## Troubleshooting

### Erro de Porta Ocupada
O mock tenta subir na porta `19114`. Se houver conflito:
```bash
export MOCK_OLLAMA_PORT=20000
python3 tests/run_tests.py
```

### Logs de Erro
Se um teste falhar, o `run_tests.py` imprimirá o `STDOUT` e `STDERR` do comando específico que causou a falha, facilitando a depuração cirúrgica.

---
**KAOS-AGENT** | *Security & Automation*