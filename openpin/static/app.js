const I18N = {
  pt: {
    subtitle: "Seu gravador, seus áudios — 100% local, offline e sem nuvem",
    btn_reset: "Trocar aparelho",
    step1_title: "Encontrar seu Plaud no Bluetooth",
    step1_hint: "Acorde o gravador (aperte o botão rapidamente) e desligue o Bluetooth do celular por um instante para ele aparecer livre aqui.",
    badge_pending: "Pendente",
    badge_ready: "Pronto",
    badge_selected: "Selecionado",
    btn_scan: "Procurar no Bluetooth",
    btn_scanning: "Procurando...",
    chk_scan_all: "Mostrar todos os dispositivos Bluetooth próximos",
    btn_select_dev: "Usar este",
    step2_title: "Configurar a chave do seu aparelho (só 1 vez)",
    step2_hint: "Cada gravador tem uma chave fixa criada quando você vinculou ele ao app do celular. Depois de salvá-la aqui uma vez, ela vale para sempre.",
    key_saved_prefix: "Chave configurada neste computador (impressão SHA-256:",
    btn_verify_key: "Testar conexão Bluetooth",
    tab_log: "Extrair do log do celular (Fácil)",
    tab_paste: "Colar chave manualmente",
    log_step_1: "No Android, abra <b>Opções do Desenvolvedor</b> e ative <b>Log de snoop HCI Bluetooth</b>.",
    log_step_2: "Abra o app oficial com o gravador ligado por 5 segundos até ele conectar, depois feche o app.",
    log_step_3: "Em <b>Opções do Desenvolvedor → Relatório de bugs</b>, gere o arquivo <code>.zip</code> e envie para o PC.",
    log_step_4: "Arraste o <code>.zip</code> (ou <code>btsnoop_hci.log</code> / <code>.pklg</code>) abaixo — tudo é lido na memória RAM e descartado na hora!",
    drop_log_title: "Clique ou arraste aqui o arquivo .zip / btsnoop_hci.log",
    drop_log_sub: "Nenhum dado do celular fica salvo no disco — apenas os 16/32 caracteres da chave do gravador.",
    btn_save_token: "Salvar e verificar",
    step3_title: "Sincronizar e Ouvir Gravações (100% Offline)",
    btn_open_folder: "Abrir pasta de áudios",
    stat_battery: "Bateria",
    stat_storage: "Espaço livre",
    stat_clock: "Relógio interno",
    stat_wifi: "Hotspot Wi-Fi",
    wifi_setup_title: "Configurar Wi-Fi rápido do NotePin (só na 1ª vez)",
    wifi_setup_desc: "Escolha ou digite o nome do Wi-Fi do gravador e o <b>Número de Série</b> (que é a senha de fábrica do Wi-Fi do aparelho, impressa na caixa ou em 'Sobre o dispositivo' no app):",
    btn_save_wifi: "Salvar Wi-Fi",
    btn_sync_wifi: "Baixar novas por Wi-Fi Rápido",
    btn_list_wifi: "Ver lista no gravador (Wi-Fi)",
    btn_list_ble: "Modo só Bluetooth",
    btn_cfg_wifi: "Configurar Wi-Fi manual",
    firewall_tip: "Dica no Windows: na 1ª sincronização por Wi-Fi, se aparecer a janela do Firewall do Windows, marque <b>Redes privadas e públicas</b> e clique em <b>Permitir</b>. Seu Wi-Fi de casa volta sozinho logo em seguida!",
    dev_recs_title: "Gravações encontradas no aparelho",
    btn_delete_pin: "Apagar do gravador as já salvas marcadas",
    th_id: "ID / Data",
    th_duration: "Duração",
    th_status: "Status",
    th_file: "Arquivo / Início",
    th_listen: "Ouvir",
    local_recs_title: "Meus Áudios Salvos neste Computador (.wav limpos)",
    local_recs_empty: "Nenhuma gravação baixada ainda.",
    converter_summary: "Tem um arquivo .asr / .opus / .wav avulso (ex.: copiado via cabo USB)? Converter e limpar aqui",
    converter_drop: "Clique ou solte um arquivo .asr ou .wav para gerar um .wav limpo (sem serial embutido)",
    footer: "OpenPin roda 100% em 127.0.0.1 no seu computador. Nenhum áudio, chave ou identificador sai da sua máquina.",
    status_saved: "Salva no PC",
    status_on_pin: "Só no gravador",
    btn_download_one: "Baixar",
    btn_save_wav: "Salvar .wav",
    clock_ok: "Sincronizado",
    wifi_ok: "Configurado",
    wifi_auto: "Automático",
    phase_starting: "Iniciando sessão...",
    phase_ble_hotspot: "Autenticando no Bluetooth e ligando o Wi-Fi do gravador...",
    phase_joining_wifi: "Conectando o Wi-Fi do PC no gravador...",
    phase_waiting_device: "Aguardando o gravador enviar a lista de áudios...",
    phase_connecting_ble: "Conectando e lendo gravações via Bluetooth...",
    phase_listed: "Lista recebida!",
    phase_downloading: "Baixando e convertendo para WAV...",
    phase_restoring_wifi: "Reconectando seu PC de volta ao Wi-Fi de casa...",
    phase_done: "Sincronização concluída com sucesso!",
    confirm_reset: "Deseja limpar as configurações salvas neste computador para configurar outro aparelho?",
    confirm_delete_pin: "Apagar do gravador as gravações marcadas? (As cópias .wav no seu computador serão mantidas)."
  },
  en: {
    subtitle: "Your recorder, your audio — 100% local, offline, no cloud required",
    btn_reset: "Switch device",
    step1_title: "Find your Plaud over Bluetooth",
    step1_hint: "Wake your recorder (press its button briefly) and turn off your phone's Bluetooth for a moment so it can appear here.",
    badge_pending: "Pending",
    badge_ready: "Ready",
    badge_selected: "Selected",
    btn_scan: "Scan Bluetooth",
    btn_scanning: "Scanning...",
    chk_scan_all: "Show all nearby Bluetooth devices",
    btn_select_dev: "Select",
    step2_title: "Set up your device key (one time only)",
    step2_hint: "Each recorder has a permanent token created when paired with your phone app. Save it once here and it works forever.",
    key_saved_prefix: "Key configured on this computer (SHA-256 fingerprint:",
    btn_verify_key: "Test Bluetooth connection",
    tab_log: "Extract from phone log (Easy)",
    tab_paste: "Paste key manually",
    log_step_1: "On Android, open <b>Developer Options</b> and enable <b>Bluetooth HCI snoop log</b>.",
    log_step_2: "Open the official app with your recorder awake for 5 seconds until connected, then close the app.",
    log_step_3: "In <b>Developer Options → Bug report</b>, generate the <code>.zip</code> file and copy it to your PC.",
    log_step_4: "Drop the <code>.zip</code> (or <code>btsnoop_hci.log</code> / <code>.pklg</code>) below — parsed in RAM only and never written to disk!",
    drop_log_title: "Click or drag & drop your .zip / btsnoop_hci.log here",
    drop_log_sub: "Nothing from your phone log is written to disk — only the 16/32-character recorder key is kept.",
    btn_save_token: "Save & verify",
    step3_title: "Sync & Listen to Recordings (100% Offline)",
    btn_open_folder: "Open audio folder",
    stat_battery: "Battery",
    stat_storage: "Free space",
    stat_clock: "Device clock",
    stat_wifi: "Wi-Fi Hotspot",
    wifi_setup_title: "Set up NotePin Fast Wi-Fi (first time only)",
    wifi_setup_desc: "Pick or type your recorder's Wi-Fi name and its <b>Serial Number</b> (which is the factory Wi-Fi password printed on the box or under 'Device Info' in the app):",
    btn_save_wifi: "Save Wi-Fi",
    btn_sync_wifi: "Download new via Fast Wi-Fi",
    btn_list_wifi: "List on device (Wi-Fi)",
    btn_list_ble: "Bluetooth-only mode",
    btn_cfg_wifi: "Configure Wi-Fi manually",
    firewall_tip: "Windows tip: on your first Wi-Fi sync, if Windows Firewall pops up, check <b>Private and Public networks</b> and click <b>Allow</b>. Your home Wi-Fi reconnects automatically right after!",
    dev_recs_title: "Recordings currently on recorder",
    btn_delete_pin: "Delete checked (already saved) from recorder",
    th_id: "ID / Date",
    th_duration: "Duration",
    th_status: "Status",
    th_file: "File / Started",
    th_listen: "Listen",
    local_recs_title: "My Saved Audio on this Computer (clean .wav)",
    local_recs_empty: "No recordings downloaded yet.",
    converter_summary: "Have a standalone .asr / .opus / .wav file (e.g. copied over USB)? Convert & sanitize here",
    converter_drop: "Click or drop a .asr or .wav file to produce a clean .wav (zero embedded serial metadata)",
    footer: "OpenPin runs 100% locally on 127.0.0.1. Zero audio, keys, or identifiers ever leave your machine.",
    status_saved: "Saved on PC",
    status_on_pin: "On recorder only",
    btn_download_one: "Download",
    btn_save_wav: "Save .wav",
    clock_ok: "Synced",
    wifi_ok: "Configured",
    wifi_auto: "Auto",
    phase_starting: "Starting session...",
    phase_ble_hotspot: "Authenticating over Bluetooth & enabling recorder Wi-Fi...",
    phase_joining_wifi: "Connecting PC Wi-Fi to recorder...",
    phase_waiting_device: "Waiting for recorder to send recording list...",
    phase_connecting_ble: "Connecting and listing over Bluetooth...",
    phase_listed: "Recording list received!",
    phase_downloading: "Downloading and converting to clean WAV...",
    phase_restoring_wifi: "Restoring your PC's home Wi-Fi connection...",
    phase_done: "Sync completed!",
    confirm_reset: "Clear saved device settings on this computer to set up another recorder?",
    confirm_delete_pin: "Delete the checked recordings from the recorder? (Your local .wav copies on this PC will remain safe)."
  }
};

let currentLang = (navigator.language || "pt").toLowerCase().startsWith("pt") ? "pt" : "en";
let appState = null;
let pollTimer = null;
let lastSyncMode = "wifi";

function t(key) {
  return (I18N[currentLang] && I18N[currentLang][key]) || I18N.en[key] || key;
}

function setLang(lang) {
  currentLang = lang;
  document.getElementById("lang-pt").classList.toggle("active", lang === "pt");
  document.getElementById("lang-en").classList.toggle("active", lang === "en");
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = el.getAttribute("data-i18n");
    el.innerHTML = t(key);
  });
  if (appState) renderState(appState);
}

// Everything shown via innerHTML that comes from a device, the radio or the disk goes through esc().
function esc(value) {
  return String(value ?? "").replace(/[&<>"'`]/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;", "`": "&#96;",
  })[c]);
}

function showMsg(text, kind = "ok") {
  const box = document.getElementById("global-msg");
  box.className = `alert ${kind}`;
  box.textContent = text;
  box.hidden = false;
  if (kind === "ok") {
    setTimeout(() => { box.hidden = true; }, 6500);
  }
}

function fmtDuration(sec) {
  const s = Math.max(0, Math.round(sec || 0));
  const m = Math.floor(s / 60);
  const r = s % 60;
  return m > 0 ? `${m}m ${String(r).padStart(2, "0")}s` : `${r}s`;
}

function fmtBytes(b) {
  if (!b && b !== 0) return "—";
  if (b >= 1024 ** 3) return (b / 1024 ** 3).toFixed(1) + " GB";
  if (b >= 1024 ** 2) return (b / 1024 ** 2).toFixed(1) + " MB";
  return Math.round(b / 1024) + " kB";
}

function fmtRecTimestamp(idStr) {
  if (/^\d+$/.test(idStr)) {
    const n = Number(idStr);
    if (n > 1577836800 && n < 4102444800) {
      return new Date(n * 1000).toLocaleString();
    }
  }
  return idStr;
}

async function api(path, opts = {}) {
  const res = await fetch(path, opts);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(data.detail || `HTTP ${res.status}`);
  }
  return data;
}

async function refreshState() {
  try {
    const data = await api("/api/state");
    appState = data;
    renderState(data);
    if (data.job && data.job.running && !pollTimer) {
      startPolling();
    }
  } catch (e) {
    console.error(e);
  }
}

function renderState(data) {
  const cfg = data.config || {};
  const dev = cfg.device;

  // Step 1
  const s1Done = Boolean(dev && dev.address);
  document.getElementById("step1-num").classList.toggle("done", s1Done);
  const b1 = document.getElementById("step1-badge");
  b1.textContent = s1Done ? t("badge_ready") : t("badge_pending");
  b1.className = "badge " + (s1Done ? "ok" : "");

  const savedBox = document.getElementById("saved-device-box");
  if (s1Done) {
    savedBox.hidden = false;
    document.getElementById("saved-dev-name").textContent = dev.name || "Plaud";
    document.getElementById("saved-dev-model").textContent = dev.model || "BLE";
    document.getElementById("saved-dev-mac").textContent = dev.address_masked || dev.address;
  } else {
    savedBox.hidden = true;
  }

  // Step 2
  const s2Done = Boolean(cfg.has_token);
  document.getElementById("step2-num").classList.toggle("done", s2Done);
  const b2 = document.getElementById("step2-badge");
  b2.textContent = s2Done ? t("badge_ready") : t("badge_pending");
  b2.className = "badge " + (s2Done ? "ok" : "");

  const keyBanner = document.getElementById("key-saved-banner");
  if (s2Done) {
    keyBanner.hidden = false;
    document.getElementById("key-fp").textContent = cfg.token_fingerprint;
  } else {
    keyBanner.hidden = true;
  }

  // Telemetry stats
  const st = cfg.last_status || {};
  document.getElementById("stat-battery").textContent =
    st.battery !== undefined ? `${st.battery}%${st.charging ? " ⚡" : ""}` : "—";
  document.getElementById("stat-storage").textContent =
    st.free_bytes !== undefined ? `${fmtBytes(st.free_bytes)} / ${fmtBytes(st.total_bytes)}` : "—";
  document.getElementById("stat-clock").textContent = st.clock_synced ? t("clock_ok") : "—";
  document.getElementById("stat-wifi").textContent = cfg.wifi_configured ? cfg.wifi_ssid : t("wifi_auto");

  // Job progress
  renderJob(data.job || {});

  // Local recordings
  renderLocalRecordings(data.local_recordings || []);
}

function renderJob(job) {
  const pbox = document.getElementById("sync-progress-box");
  const btns = ["btn-wifi-sync", "btn-wifi-list", "btn-ble-list"];
  btns.forEach((id) => { document.getElementById(id).disabled = Boolean(job.running); });

  if (job.phase === "wifi_needed" && job.wifi_needed) {
    const wbox = document.getElementById("wifi-setup-box");
    wbox.hidden = false;
    const candDiv = document.getElementById("wifi-candidates");
    candDiv.innerHTML = "";
    (job.wifi_needed.candidates || []).forEach((ssid) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "chip-btn";
      btn.textContent = ssid;
      btn.onclick = () => { document.getElementById("wifi-ssid-input").value = ssid; };
      candDiv.appendChild(btn);
    });
  }

  if (job.error) {
    showMsg(job.error, "error");
  }

  if (job.running) {
    pbox.hidden = false;
    const phaseKey = `phase_${job.phase}`;
    document.getElementById("sync-phase-label").textContent = t(phaseKey) !== phaseKey ? t(phaseKey) : job.phase;
    const fill = document.getElementById("sync-bar-fill");
    if (job.phase === "downloading" && job.total > 0) {
      const pct = Math.min(100, Math.round((job.received / job.total) * 100));
      fill.style.width = `${pct}%`;
      document.getElementById("sync-bytes-label").textContent =
        `${fmtBytes(job.received)} / ${fmtBytes(job.total)} (${pct}%)`;
    } else {
      fill.style.width = "35%";
      document.getElementById("sync-bytes-label").textContent = "";
    }
  } else {
    pbox.hidden = true;
  }

  // Device recordings table
  const recs = job.device_recordings || [];
  const devSec = document.getElementById("device-recs-section");
  const devBody = document.getElementById("device-recs-body");
  if (recs.length > 0) {
    devSec.hidden = false;
    devBody.innerHTML = "";
    recs.forEach((r) => {
      const tr = document.createElement("tr");
      const chkDisabled = !r.already_saved ? "disabled" : "";
      tr.innerHTML = `
        <td><input type="checkbox" class="pin-del-chk" value="${esc(r.id)}" ${chkDisabled}></td>
        <td><strong>${esc(fmtRecTimestamp(r.id))}</strong><div style="font-size:0.76rem;color:var(--muted)">ID ${esc(r.id)}</div></td>
        <td>${esc(fmtDuration(r.duration_seconds))} (${esc(fmtBytes(r.size_bytes))})</td>
        <td><span class="badge ${r.already_saved ? 'ok' : 'warn'}">${r.already_saved ? t('status_saved') : t('status_on_pin')}</span></td>
        <td style="text-align:right">
          ${r.already_saved ? "" : `<button type="button" class="secondary small btn-dl-one">${t('btn_download_one')}</button>`}
        </td>
      `;
      const dlBtn = tr.querySelector(".btn-dl-one");
      if (dlBtn) dlBtn.addEventListener("click", () => downloadSingle(String(r.id)));
      devBody.appendChild(tr);
    });
  } else {
    devSec.hidden = true;
  }
}

function renderLocalRecordings(list) {
  const empty = document.getElementById("local-recs-empty");
  const table = document.getElementById("local-recs-table");
  const body = document.getElementById("local-recs-body");
  if (!list.length) {
    empty.hidden = false;
    table.hidden = true;
    return;
  }
  empty.hidden = true;
  table.hidden = false;
  body.innerHTML = "";
  list.forEach((r) => {
    const tr = document.createElement("tr");
    const sub = r.started_at ? new Date(r.started_at).toLocaleString() : r.saved_at;
    tr.innerHTML = `
      <td><strong>${esc(r.filename)}</strong><div style="font-size:0.76rem;color:var(--muted)">${esc(sub)}</div></td>
      <td>${esc(fmtDuration(r.duration_seconds))}</td>
      <td><audio controls preload="none" src="/api/recordings/${encodeURIComponent(r.id)}/wav"></audio></td>
      <td style="text-align:right">
        <a class="btn secondary small" href="/api/recordings/${encodeURIComponent(r.id)}/wav?download=true">${t('btn_save_wav')}</a>
      </td>
    `;
    body.appendChild(tr);
  });
}

async function scanBluetooth() {
  const btn = document.getElementById("btn-scan");
  const all = document.getElementById("chk-scan-all").checked;
  btn.disabled = true;
  btn.textContent = t("btn_scanning");
  const listEl = document.getElementById("scan-results");
  listEl.innerHTML = "";
  try {
    const data = await api(`/api/scan?include_all=${all}`, { method: "POST" });
    if (!data.devices.length) {
      showMsg(
        currentLang === "pt"
          ? "Nenhum Plaud encontrado. Aperte o botão do gravador para acordá-lo e desligue o Bluetooth do celular."
          : "No Plaud device found. Press your recorder's button to wake it and turn off your phone's Bluetooth.",
        "warn"
      );
    }
    data.devices.forEach((d) => {
      const div = document.createElement("div");
      div.className = "device-item";
      div.innerHTML = `
        <div>
          <strong>${esc(d.name)}</strong>
          <div style="font-size:0.8rem;color:var(--muted)">${esc(d.model)} · <code>${esc(d.address_masked)}</code> · RSSI ${esc(d.rssi ?? "?")} dBm</div>
        </div>
      `;
      const sbtn = document.createElement("button");
      sbtn.type = "button";
      sbtn.className = "small";
      sbtn.textContent = t("btn_select_dev");
      sbtn.onclick = () => selectDevice(d);
      div.appendChild(sbtn);
      listEl.appendChild(div);
    });
  } catch (e) {
    showMsg(e.message, "error");
  } finally {
    btn.disabled = false;
    btn.textContent = t("btn_scan");
  }
}

async function selectDevice(d) {
  try {
    await api("/api/device/select", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(d)
    });
    document.getElementById("scan-results").innerHTML = "";
    await refreshState();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

function switchKeyTab(which) {
  document.getElementById("tab-log").hidden = which !== "log";
  document.getElementById("tab-paste").hidden = which !== "paste";
  document.getElementById("tab-log-btn").classList.toggle("active", which === "log");
  document.getElementById("tab-paste-btn").classList.toggle("active", which === "paste");
}

async function uploadLogFile(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await api("/api/token/extract-log", { method: "POST", body: fd });
    showMsg(
      currentLang === "pt"
        ? `Chave extraída com sucesso! Impressão: ${res.token_fingerprint}`
        : `Key extracted! Fingerprint: ${res.token_fingerprint}`,
      "ok"
    );
    await refreshState();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

async function savePastedToken() {
  const val = document.getElementById("token-input").value.trim();
  try {
    await api("/api/token/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token: val, verify_now: true })
    });
    document.getElementById("token-input").value = "";
    showMsg(currentLang === "pt" ? "Chave verificada com o gravador!" : "Key verified with your recorder!", "ok");
    await refreshState();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

async function verifyKey() {
  try {
    await api("/api/token/verify", { method: "POST" });
    showMsg(
      currentLang === "pt"
        ? "Conexão Bluetooth autenticada e relógio do gravador sincronizado!"
        : "Bluetooth authenticated and recorder clock synced!",
      "ok"
    );
    await refreshState();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

function toggleWifiSetup() {
  const box = document.getElementById("wifi-setup-box");
  box.hidden = !box.hidden;
}

async function saveWifiCreds() {
  const ssid = document.getElementById("wifi-ssid-input").value.trim();
  const password = document.getElementById("wifi-pass-input").value.trim();
  try {
    await api("/api/wifi/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ssid, password })
    });
    document.getElementById("wifi-pass-input").value = "";
    document.getElementById("wifi-setup-box").hidden = true;
    showMsg(currentLang === "pt" ? "Credenciais do Wi-Fi do gravador salvas!" : "Recorder Wi-Fi credentials saved!", "ok");
    await refreshState();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

function startPolling() {
  if (pollTimer) clearInterval(pollTimer);
  pollTimer = setInterval(async () => {
    try {
      const data = await api("/api/sync/progress");
      appState = { ...appState, ...data };
      renderState(appState);
      if (!data.job.running) {
        clearInterval(pollTimer);
        pollTimer = null;
        if (data.job.phase === "done") {
          showMsg(t("phase_done"), "ok");
        }
      }
    } catch (_e) {
      // Localhost stays reachable while Wi-Fi switches; ignore transient hiccups
    }
  }, 900);
}

async function startWifiSync(action, ids = []) {
  lastSyncMode = "wifi";
  try {
    await api("/api/sync/wifi", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, ids })
    });
    startPolling();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

async function startBleSync(downloadIds = []) {
  lastSyncMode = "ble";
  try {
    await api("/api/sync/ble", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ download_ids: downloadIds })
    });
    startPolling();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

function downloadSingle(recId) {
  if (lastSyncMode === "ble") {
    startBleSync([recId]);
  } else {
    startWifiSync("selected", [recId]);
  }
}

function deleteSelectedFromPin() {
  const checked = Array.from(document.querySelectorAll(".pin-del-chk:checked")).map((c) => c.value);
  if (!checked.length) return;
  if (!confirm(t("confirm_delete_pin"))) return;
  startWifiSync("delete", checked);
}

async function convertStandaloneFile(file) {
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  try {
    const res = await api("/api/convert-file", { method: "POST", body: fd });
    showMsg(`WAV: ${res.filename}`, "ok");
    await refreshState();
  } catch (e) {
    showMsg(e.message, "error");
  }
}

async function openFolder() {
  try {
    await api("/api/open-folder", { method: "POST" });
  } catch (e) {
    showMsg(e.message, "error");
  }
}

async function resetConfig() {
  if (!confirm(t("confirm_reset"))) return;
  await api("/api/reset", { method: "POST" });
  await refreshState();
}

// Drag & drop wiring
["log-dropzone"].forEach((id) => {
  const dz = document.getElementById(id);
  dz.addEventListener("dragover", (e) => { e.preventDefault(); dz.classList.add("dragover"); });
  dz.addEventListener("dragleave", () => dz.classList.remove("dragover"));
  dz.addEventListener("drop", (e) => {
    e.preventDefault();
    dz.classList.remove("dragover");
    if (e.dataTransfer.files.length) uploadLogFile(e.dataTransfer.files[0]);
  });
});

setLang(currentLang);
refreshState();
