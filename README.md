# OpenPin — Local Offline Sync for Plaud NotePin & Plaud Note

**[Português](#português--guia-rápido-em-3-cliques) · [English](#english--3-click-quick-start)**

---

## Português — Guia Rápido em 3 Cliques

Seu gravador é seu: **use seus próprios áudios localmente no Windows (ou Linux), 100% offline, sem nuvem e sem complicação.**

O **OpenPin** abre um painel visual no seu navegador (`http://127.0.0.1:8765`) feito para qualquer pessoa usar sem precisar entender de programação.

### O que ele faz
- Funciona tanto com o **Plaud NotePin** (chip Realtek `0x005d`) quanto com o **Plaud Note** (chip Nordic `0x0059`).
- **Sincronização rápida pelo Wi-Fi do próprio gravador (~800 kB/s)** — lista todas as gravações, baixa, converte e reconecta seu PC de volta ao Wi-Fi de casa sozinho.
- **Modo só Bluetooth** — para computadores de mesa que têm Bluetooth, mas não têm placa Wi-Fi.
- **Áudios `.wav` limpos** — converte os pacotes Opus originais para `.wav` padrão (16 kHz mono), **sem metadados extras** (nenhum número de série ou identificador do aparelho no arquivo), pronto para ouvir no navegador ou transcrever localmente (Whisper etc.).
- **Privacidade total** — nada sai do seu computador; chaves e gravações ficam ignoradas no `.gitignore` para nunca vazarem por engano. O painel só atende o navegador deste próprio computador: outros sites e outros aparelhos da rede são recusados.

### Como usar no Windows (Passo a Passo Simples)

1. **Baixe ou extraia esta pasta** no seu computador (ex.: `D:\projetos\openpin`) e dê **dois cliques em `Start-Windows.bat`**.
   - Se você ainda não tiver o Python instalado, o próprio `Start-Windows.bat` oferece instalar automaticamente pelo Windows (`winget`).
   - Ele prepara tudo sozinho na primeira vez e abre o navegador em `http://127.0.0.1:8765`.
2. **Passo 1 na tela — Encontrar seu Plaud:**
   - Aperte rapidamente o botão do gravador para acordá-lo, desligue o Bluetooth do celular por um instante e clique em **Procurar no Bluetooth** → **Usar este**.
3. **Passo 2 na tela — Configurar sua chave (só precisa fazer 1 vez na vida):**
   - Cada gravador tem uma chave fixa criada quando foi pareado com seu celular.
   - No Android: ative *Opções do Desenvolvedor → Log de snoop HCI Bluetooth*, abra o app da Plaud por 5 segundos até conectar no gravador, gere o *Relatório de bugs (`.zip`)* e **arraste o `.zip` direto para a página do OpenPin**. O programa acha a chave na memória RAM na hora sem salvar nada do relatório no disco! *(Ou cole sua chave direto se já tiver).*
4. **Passo 3 na tela — Sincronizar e Ouvir:**
   - Clique em **Baixar novas por Wi-Fi Rápido** (se o Firewall do Windows perguntar na 1ª vez, marque *Redes privadas e públicas* e clique em *Permitir*).
   - **Se o painel pedir o nome e a senha do Wi-Fi do gravador:** alguns firmwares não informam isso pelo Bluetooth. O nome da rede aparece sozinho como sugestão na tela (é a rede nova que surge quando a sincronização começa). A senha costuma ser o **número de série** do gravador (veja nas informações do dispositivo no app da Plaud ou na embalagem). Você só digita isso uma vez.
   - Ouça direto na tela ou clique em **Abrir pasta de áudios**!
   - O OpenPin só apaga uma gravação do gravador se a cópia `.wav` local estiver completa.

### Como usar no Linux / Raspberry Pi

```bash
chmod +x start-linux.sh
./start-linux.sh
```

---

## English — 3-Click Quick Start

Your hardware belongs to you: **access, play, and back up your recordings locally on Windows or Linux — 100% offline, cloud-free, and subscription-free.**

**OpenPin** launches a clean local browser wizard (`http://127.0.0.1:8765`) designed for everyday users with zero command-line setup required.

### Highlights
- Supports both **Plaud NotePin** (Realtek `0x005d`) and **Plaud Note** (Nordic `0x0059`).
- **Fast Local Wi-Fi Sync (~800 kB/s):** Activates the recorder's temporary local Wi-Fi AP over BLE, downloads recordings over WebSocket, deletes temporary Wi-Fi profiles, and automatically reconnects your PC to your home Wi-Fi.
- **Bluetooth-Only Mode:** Works even on desktop PCs without a Wi-Fi adapter.
- **Clean `.wav` Output:** Decodes raw 80-byte Opus streams into standard 16 kHz mono PCM `.wav` files with no extra metadata (no device serial or identifier in the file).
- **Privacy by Design:** Binds strictly to `127.0.0.1` and only answers this computer's own browser tab (other websites and DNS-rebinding hosts are refused). Device tokens and serials are masked in the UI and excluded via `.gitignore`.

### Running on Windows

1. Extract this folder anywhere on your PC and **double-click `Start-Windows.bat`**.
   - On first run, it automatically sets up an isolated `.venv`, installs dependencies, and opens `http://127.0.0.1:8765`.
2. **Step 1 — Scan Bluetooth:** Wake your recorder, pause your phone's Bluetooth briefly, and click **Scan Bluetooth** → **Select**.
3. **Step 2 — One-Time Device Key:** Drag & drop an Android Bluetooth bugreport `.zip` / `btsnoop_hci.log` (parsed purely in RAM, never saved to disk) or paste an existing 16/32-character hex token.
4. **Step 3 — Sync & Play:** Click **Download new via Fast Wi-Fi** (allow Python through Windows Firewall on first run if prompted) or use **Bluetooth-only mode**.
   - **If the panel asks for the recorder's Wi-Fi name and password:** some firmware builds don't send them over Bluetooth. The network name is suggested on screen (it's the new network that appears when the sync starts). The password is usually the recorder's **serial number** (see device info in the Plaud app, or the box). You only enter it once.
   - OpenPin only deletes a recording from the device when a complete local `.wav` copy exists.

### Project Status / Estado do projeto

| Feature | Status |
| --- | --- |
| Plaud NotePin — Wi-Fi protocol (BLE wake-up, hotspot, list, download, delete) | Verified on real hardware |
| Plaud NotePin — this app end-to-end on Linux (NetworkManager) | **Experimental** — same protocol, app not yet run against hardware |
| Plaud NotePin — Wi-Fi sync on Windows (`netsh`) | **Experimental** — not yet tested on real hardware |
| Bluetooth-only download | **Experimental** |
| Plaud Note (Nordic) | **Experimental** — protocol believed identical, untested |
| Key extraction from an Android bugreport | **Experimental** — tested with synthetic captures only |

Bug reports with your platform and recorder model are very welcome (never attach recordings, bugreports or keys). / Relatos de bug são bem-vindos (nunca anexe gravações, bugreports ou chaves).

### Protocol Documentation & Disclaimer

See [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for wire-level interoperability notes.

*OpenPin is an independent open-source interoperability tool created so hardware owners can access their own personal audio files locally. Not affiliated with or endorsed by Plaud Inc. Avoid updating device firmware if you rely on local offline workflows, as vendor firmware updates may alter local protocols.*
