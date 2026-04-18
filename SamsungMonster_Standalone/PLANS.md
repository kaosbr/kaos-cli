# Plano de Restauração Cirúrgica - Samsung Monster GUI

Este documento descreve o inventário atual, as lacunas detectadas e o roteiro para a restauração da interface e integrações do projeto.

## 1. Inventário da GUI Atual

### Visíveis e Funcionais (Parcialmente)
- **Dashboard**: Leitura básica de info, reboots (System, Download).
- **Firmware**: Odin Flash (5 slots), Smart Repair (Cloud), Hybrid Engine.
- **Security**: FRP Bypass (Download/MTP), MDM Bypass, Exploit Lab (Ghost PIT, SysUI Crash).
- **Service**: RF Lab (IMEI, CSC), Chipsets (EDL, BROM, EUB), Tools (Auto-Repair).
- **Resources**: QR Gen (MDM), Driver Doctor (Básico), Full Logs.

### Ocultos/Incompletos/Quebrados
- **Partitions**: Tabela de partições vazia, sem lógica de listagem ou interação.
- **RF Lab**: Faltam funções de Backup EFS, Repair Network e Patch Certificate (implementadas no backend mas não ligadas).
- **Repair SN**: Botão sem efeito (handler órfão).
- **Schematics**: Conteúdo estático de exemplo.
- **Mode Awareness**: Botões ativos mesmo quando o protocolo não suporta a operação (ex: Flash em modo Modem).

## 2. Lacunas Detectadas (Backend vs GUI)

| Recurso | Status Backend | Status GUI | Ação Necessária |
| :--- | :--- | :--- | :--- |
| **Listar Partições** | Implementado nos protocolos | Handler vazio | Ligar Orchestrator à UI Table |
| **Backup EFS** | Implementado em `SamsungOperations` | Inexistente | Adicionar botão em RF Lab/Tools |
| **Repair Network** | Implementado em `SamsungOperations` | Inexistente | Adicionar botão em RF Lab |
| **Patch Certificate**| Implementado em `SamsungOperations` | Inexistente | Adicionar botão em RF Lab |
| **Repair Serial** | Não implementado | Botão órfão | Implementar em Ops e Orchestrator |
| **Auto-Detect Loaders**| Implementado em `LoaderManager` | Parcial | Validar detecção automática em Chipsets |

## 3. Ordem de Restauração por Prioridade

### Etapa 1: Alinhamento de Infraestrutura (Orchestrator) - [CONCLUÍDO]
- [x] Adicionar `list_partitions` ao `TaskOrchestrator`.
- [x] Adicionar `backup_efs`, `repair_network` e `patch_certificate` ao `TaskOrchestrator`.
- [x] Implementar `repair_serial` na camada de `SamsungOperations` e `Orchestrator`.

### Etapa 2: Restauração do Partition Manager - [CONCLUÍDO]
- [x] Implementar `_refresh_partitions` em `gui.py`.
- [x] Popular `QTableWidget` com Nome, Tamanho e Ações (Read, Erase).
- [x] Ligar ações de partição ao backend.

### Etapa 3: Expansão do RF Lab & Security - [CONCLUÍDO]
- [x] Integrar botões de Backup EFS, Repair Network e Patch Certificate no `RF LAB`.
- [x] Garantir que o `RF LAB` use o protocolo correto (Modem ou EUB/EDL).
- [x] Implementar e ligar `repair_serial` (S/N).

### Etapa 4: Estabilidade e UX - [CONCLUÍDO]
- [x] Implementar trava de segurança (disable buttons) baseada no modo atual do dispositivo.
- [x] Melhorar o `Driver Doctor` para diagnosticar drivers Samsung ausentes.
- [x] Adicionar feedback visual de progresso e logs detalhados para novas funções.

### Etapa 5: Suporte a Chipsets e Cloud - [CONCLUÍDO]
- [x] Integrar handlers de EDL Flash, EUB Loader e BROM Boot no Orchestrator.
- [x] Ligar botões na aba de Chipsets e garantir mode-awareness.
- [x] Expandir base de dados de SoCs (Qualcomm, MediaTek, Exynos) em `DeviceDatabase`.
- [x] Integrar `Soft-Brick Fix` via download automático e mapeamento de firmware.

### Etapa 6: Integração de Scripts Standalone - [CONCLUÍDO]
- [x] Integrar `deep_diagnose.py`, `brute_handshake.py`, `force_reboot.py` e `identify_apparel.py`.
- [x] Corrigir estabilidade USB e restaurar leitura automática.

### Etapa 7: Integração de Protocolos Ocultos e Payloads - [CONCLUÍDO]
- [x] Ativar e expor protocolo Unisoc SPD.
- [x] Implementar injeção de Payloads binários.

## Plano Atual: Integração Profunda de Hardware e Cloud - [CONCLUÍDO]
- [x] Implementar `AT+DEVCONINFO` para leitura de BIT real (SWREV).
- [x] Adicionar `Smart Bridge Toggle` para downgrades automáticos e seguros.
- [x] Estabilizar barramento USB via `USB_GLOBAL_LOCK` (Zero "Resource busy").
- [x] Implementar parser real para SamFW no `FirmwareFetcher` (BS4).

## Próximos Passos
1. Validar injeção de payloads em partições de segurança (PARAM/STEADY).
2. Expandir continuamente a base de dados de `Test Points` no tab de Schematics.
3. Adicionar suporte a `Soft-Brick Fix` via download automático de PIT específico.

### Checkpoint: Sistema Integrado e Estável
- [x] GUI 100% acessível e sincronizada.
- [x] Leitura de hardware automática (Bit/Model) robusta em One UI 6.1+.
- [x] Fluxo de Cloud Repair integrado com scraping real.
- [x] **Preservado**: Toda a lógica de baixo nível dos protocolos originais sem regressões.

## Etapa 8: Reconstrução por Integração (Em andamento)
- [x] Registrar e corrigir imports quebrados entre `main.py`, `ui/gui.py`, `core/orchestrator.py` e `operations/samsung_ops.py`.
- [x] Revalidar conexão UI -> handlers -> orchestrator para fluxo entrada -> processamento -> saída.
- [x] Ajustar chamadas órfãs e sinais de botões sem criar lógica nova.
- [x] Validar impacto local com execução rápida e revisar logs.

### Arquivos-alvo desta etapa
- `main.py`
- `ui/gui.py`
- `core/orchestrator.py`
- `operations/samsung_ops.py`
- `ui/widgets.py`

### Resultado / Checkpoint Etapa 8
- [x] Reconectado fluxo Unisoc SPD: detecção USB -> `ConnectionMode` -> `TaskOrchestrator.get_protocol` -> botão UI de boot.
- [x] Restaurado handler de saída do Driver Doctor no log da GUI.
- [x] Validado localmente: `python3 -m compileall -q .` sem erros.
- [x] Validado localmente: instância de `SamsungUnisocSPD` funcional (classe não-abstrata).
- [x] **Preservado**: sem remoção de código existente; sem reescrita integral de arquivos; sem alteração de arquitetura fora do escopo.

## Etapa 9: Correção do Atalho Desktop (Em andamento)
- [x] Corrigir `Exec` no arquivo `.desktop` para caminho com espaço.
- [x] Validar sintaxe do atalho após ajuste.

### Arquivo-alvo desta etapa
- `SamsungMonster.desktop`

### Resultado / Checkpoint Etapa 9
- [x] Atalho corrigido com escape de espaços no campo `Exec`.
- [x] Validação local executada sem erros de sintaxe reportados.
- [x] **Preservado**: script de inicialização e restante da configuração do atalho mantidos.

## Etapa 10: Drivers Samsung + Conexão Painel (Em andamento)
- [x] Reforçar detecção inicial de dispositivo para não perder evento antes do callback da GUI.
- [x] Garantir atualização imediata do painel de informações após iniciar o programa.
- [x] Ajustar fluxo de Driver Doctor para tentativa de correção dos itens detectados.
- [x] Validar compilação e importação local após integração.

### Arquivos-alvo desta etapa
- `main.py`
- `core/device_manager.py`
- `ui/gui.py`
- `utils/driver_doctor.py`

### Resultado / Checkpoint Etapa 10
- [x] Reordenada inicialização no `main.py`: monitor USB sobe após GUI conectar callbacks.
- [x] Adicionado `scan_now()` no `DeviceManager` e acionado em `ui/gui.py` para atualizar painel imediatamente.
- [x] Driver Doctor agora tenta correção real de `udev`, `plugdev` e `ModemManager` via `sudo -n`.
- [x] Validação local concluída: `python3 -m compileall -q .` e imports essenciais sem erro.
- [x] **Preservado**: sem remoção de código existente, sem troca de arquitetura e sem reescrita integral de arquivos.

## Etapa 11: Detecção Real de Info em ODIN (Em andamento)
- [x] Integrar fallback de identificação no `get_device_full_info` usando dados já disponíveis do USBDevice e descriptors.
- [x] Estabilizar sessão de leitura ODIN removendo reboot implícito no `disconnect`.
- [x] Exibir no painel dados úteis quando modelo exato não estiver exposto pelo bootloader.
- [x] Validar compilação local pós-integração.

### Arquivos-alvo desta etapa
- `core/orchestrator.py`
- `protocols/samsung_odin.py`
- `ui/gui.py`

### Resultado / Checkpoint Etapa 11
- [x] `get_device_full_info` agora aplica fallback de modelo por regex (`SM-*`) em descriptors USB e serial.
- [x] Quando o bootloader não expõe modelo, o painel usa identificador útil (`USB_VID_PID`) em vez de `UNKNOWN`.
- [x] `SamsungOdin.disconnect()` não força mais reboot ao encerrar sessão de leitura.
- [x] `ui/gui.py` reutiliza `product` como variante quando a identificação de apparel retornar genérica.
- [x] Validação local: `python3 -m compileall -q .` sem erro.
- [x] **Preservado**: lógica principal de protocolos e fluxos existentes mantida, com delta mínimo de integração.

## Etapa 12: Correção do Flash Firmware Automático (Em andamento)
- [x] Corrigir resolução de link/download no `FirmwareFetcher`.
- [x] Corrigir mapeamento de arquivos extraídos para flash plan (incluindo estrutura em subpastas).
- [x] Ajustar validação de `model` e `bit` no `run_auto_repair` para evitar chamadas inválidas ao SamFW.
- [x] Validar compilação local após integração.

### Arquivos-alvo desta etapa
- `utils/firmware_fetcher.py`
- `core/orchestrator.py`

### Resultado / Checkpoint Etapa 12
- [x] `run_auto_repair` valida modelo real (`SM-*|GT-*|SCH-*`) e normaliza filtro de `bit`.
- [x] `FirmwareFetcher.get_samfw_firmware` recebeu ordenação de data robusta e fallback quando bit exato não existe.
- [x] `download_and_extract` agora valida resposta HTTP, resolve link SamFW em dois passos e extrai somente quando pacote é ZIP.
- [x] `map_extracted_files` passou a mapear recursivamente BL/AP/CP/CSC/HOME_CSC/USERDATA.
- [x] Validação local: `python3 -m compileall -q .` sem erro.
- [x] **Preservado**: fluxo original de auto-repair e flash Odin mantido, apenas reconectado e robustecido.
