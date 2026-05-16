const today = "2026-05-15";

let inventory = [
  {
    id: "INV-000001",
    genre: "MTG",
    cardName: "Lightning Bolt",
    rarity: "C",
    setName: "4EDBB",
    language: "jp",
    collectorNumber: "",
    note: "通常",
    condition: "MP",
    quantity: 1,
    buyPrice: 1000,
    salePrice: 2100,
    status: "販売中",
    registeredAt: "2026-03-01",
    lastCheckedAt: "2026-03-01",
    updatedAt: "2026-03-01",
    memo: ""
  },
  {
    id: "INV-000002",
    genre: "ポケカ",
    cardName: "リザードンex",
    rarity: "SAR",
    setName: "SV4a",
    language: "jp",
    collectorNumber: "349/190",
    note: "テラスタル",
    condition: "A-",
    quantity: 1,
    buyPrice: 12500,
    salePrice: 17800,
    status: "販売中",
    registeredAt: "2026-01-22",
    lastCheckedAt: "2026-01-25",
    updatedAt: "2026-02-01",
    memo: "ショーケース"
  },
  {
    id: "INV-000003",
    genre: "遊戯王",
    cardName: "青眼の白龍",
    rarity: "UR",
    setName: "LB-01",
    language: "jp",
    collectorNumber: "",
    note: "初期",
    condition: "B",
    quantity: 1,
    buyPrice: 40000,
    salePrice: 69800,
    status: "取置中",
    registeredAt: "2026-04-04",
    lastCheckedAt: "2026-04-20",
    updatedAt: "2026-04-20",
    memo: "取置期限確認"
  },
  {
    id: "INV-000004",
    genre: "デュエマ",
    cardName: "ボルシャック・ドギラゴン",
    rarity: "LEG",
    setName: "DMR-19",
    language: "jp",
    collectorNumber: "L2/L2",
    note: "",
    condition: "A",
    quantity: 3,
    buyPrice: 900,
    salePrice: 1480,
    status: "販売中",
    registeredAt: "2026-05-02",
    lastCheckedAt: "2026-05-02",
    updatedAt: "2026-05-02",
    memo: ""
  },
  {
    id: "INV-000005",
    genre: "MTG",
    cardName: "Counterspell",
    rarity: "U",
    setName: "DMR",
    language: "en",
    collectorNumber: "",
    note: "Foil",
    condition: "SP",
    quantity: 2,
    buyPrice: 300,
    salePrice: 780,
    status: "売却済み",
    registeredAt: "2026-02-11",
    lastCheckedAt: "2026-03-12",
    updatedAt: "2026-04-01",
    memo: ""
  },
  {
    id: "INV-000006",
    genre: "ワンピースカード",
    cardName: "ナミ",
    rarity: "SP",
    setName: "OP01",
    language: "jp",
    collectorNumber: "016",
    note: "パラレル",
    condition: "A",
    quantity: 1,
    buyPrice: 18000,
    salePrice: 24800,
    status: "販売中",
    registeredAt: "2025-12-14",
    lastCheckedAt: "2026-01-03",
    updatedAt: "2026-01-03",
    memo: "価格見直し対象"
  },
  {
    id: "INV-000007",
    genre: "MTG",
    cardName: "Lightning Bolt",
    rarity: "C",
    setName: "４ＥＤＢＢ",
    language: "en",
    collectorNumber: "０５５／０７１",
    note: "Ｆｏｉｌ",
    condition: "SP",
    quantity: 1,
    buyPrice: 1200,
    salePrice: 2600,
    status: "販売中",
    registeredAt: "2026-05-15",
    lastCheckedAt: "2026-05-15",
    updatedAt: "2026-05-15",
    memo: "複製後に別バージョンとして調整する想定"
  }
];

const dummyGenres = ["MTG", "ポケカ", "遊戯王", "デュエマ", "ワンピースカード"];
const dummyNames = ["サンプルカード", "店頭確認カード", "価格調整候補", "ショーケース候補", "ストレージ追加分"];
const dummyRarities = ["C", "U", "R", "SR", "SAR", "SEC"];
const dummyConditions = ["A", "A-", "B", "SP", "MP"];
const dummyNotes = ["通常", "Foil", "プロモ", "パラレル", "拡張アート", ""];

function createDummyInventory() {
  return Array.from({ length: 72 }, (_, index) => {
    const number = index + 8;
    const genre = dummyGenres[index % dummyGenres.length];
    const month = String((index % 5) + 1).padStart(2, "0");
    const day = String((index % 27) + 1).padStart(2, "0");
    return {
      id: "INV-" + String(number).padStart(6, "0"),
      genre,
      cardName: `${dummyNames[index % dummyNames.length]} ${String(index + 1).padStart(2, "0")}`,
      rarity: dummyRarities[index % dummyRarities.length],
      setName: `${genre.slice(0, 2).toUpperCase()}-${String((index % 12) + 1).padStart(2, "0")}`,
      language: index % 4 === 0 ? "en" : "jp",
      collectorNumber: `${String((index % 150) + 1).padStart(3, "0")}/${String(180 + (index % 30)).padStart(3, "0")}`,
      note: dummyNotes[index % dummyNotes.length],
      condition: dummyConditions[index % dummyConditions.length],
      quantity: (index % 4) + 1,
      buyPrice: 50 + (index % 20) * 120,
      salePrice: 180 + (index % 30) * 220,
      status: index % 17 === 0 ? "取置中" : "販売中",
      registeredAt: `2026-${month}-${day}`,
      lastCheckedAt: `2026-${month}-${day}`,
      updatedAt: `2026-${month}-${day}`,
      memo: index % 9 === 0 ? "ダミーデータ" : ""
    };
  });
}

inventory = inventory.concat(createDummyInventory());

const linkSettings = [
  {
    enabled: true,
    genre: "MTG",
    siteName: "晴れる屋",
    urlTemplate: "https://www.hareruyamtg.com/ja/products/search?product={query}",
    queryTemplate: "{card_name} {set} {collector_number}"
  },
  {
    enabled: true,
    genre: "ポケカ",
    siteName: "カードラッシュ ポケモン",
    urlTemplate: "https://www.cardrush-pokemon.jp/product-list?keyword={query}",
    queryTemplate: "{card_name} {set} {collector_number}"
  },
  {
    enabled: true,
    genre: "その他",
    siteName: "Google検索",
    urlTemplate: "https://www.google.com/search?q={query}",
    queryTemplate: "{genre} {card_name} {set} {collector_number}"
  }
];

const displayColumns = [
  "ジャンル",
  "カード名",
  "補足",
  "枚数",
  "販売価格",
  "最終確認日",
  "在庫ステータス",
  "価格検索リンク"
];

let selectedIds = new Set();
let editingId = null;
let detailEditingId = null;
let filteredInventory = [];
let currentPage = 1;
const pageSize = 50;

const form = document.querySelector("#filterForm");
const body = document.querySelector("#inventoryBody");
const toast = document.querySelector("#toast");
const filterPanel = document.querySelector("#filterPanel");
const toggleFiltersButton = document.querySelector("#toggleFiltersButton");
const filterSummary = document.querySelector("#filterSummary");

function daysBetween(dateText) {
  const base = new Date(today);
  const target = new Date(dateText);
  return Math.floor((base - target) / 86400000);
}

function yen(value) {
  return Number(value).toLocaleString("ja-JP") + "円";
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.add("show");
  window.setTimeout(() => toast.classList.remove("show"), 2200);
}

function nextId() {
  const max = inventory.reduce((current, item) => {
    const number = Number(item.id.replace("INV-", ""));
    return Math.max(current, number);
  }, 0);
  return "INV-" + String(max + 1).padStart(6, "0");
}

function getFormFilters() {
  return Object.fromEntries(new FormData(form).entries());
}

function normalizeSearchText(value) {
  return String(value ?? "").normalize("NFKC").toLowerCase();
}

function matchesTextFilter(value, query) {
  if (!query) return true;
  return normalizeSearchText(value).includes(normalizeSearchText(query));
}

function applyFilters() {
  const filters = getFormFilters();
  filteredInventory = inventory.filter((item) => {
    if (filters.genre && item.genre !== filters.genre) return false;
    if (filters.status && item.status !== filters.status) return false;
    if (!matchesTextFilter(item.cardName, filters.cardName)) return false;
    if (!matchesTextFilter(item.setName, filters.setName)) return false;
    if (!matchesTextFilter(item.collectorNumber, filters.collectorNumber)) return false;
    if (!matchesTextFilter(item.note, filters.note)) return false;
    if (filters.reviewDays && daysBetween(item.lastCheckedAt) < Number(filters.reviewDays)) return false;
    return true;
  });

  const key = filters.sortKey || "lastCheckedAt";
  const direction = filters.sortDir === "desc" ? -1 : 1;
  filteredInventory.sort((a, b) => {
    const left = a[key];
    const right = b[key];
    if (left === right) return 0;
    return left > right ? direction : -direction;
  });
}

function updateFilterSummary() {
  const filters = getFormFilters();
  const active = [];
  if (filters.genre) active.push(`ジャンル: ${filters.genre}`);
  if (filters.cardName) active.push(`カード名: ${filters.cardName}`);
  if (filters.setName) active.push(`セット: ${filters.setName}`);
  if (filters.collectorNumber) active.push(`番号: ${filters.collectorNumber}`);
  if (filters.status) active.push(`ステータス: ${filters.status}`);
  if (filters.note) active.push(`補足: ${filters.note}`);
  if (filters.reviewDays) active.push(`${filters.reviewDays}日以上未確認`);
  filterSummary.textContent = active.length ? active.join(" / ") : "全件表示";
}

function buildQuery(item, setting) {
  const variables = {
    genre: item.genre,
    card_name: item.cardName,
    set: item.setName,
    language: item.language,
    collector_number: item.collectorNumber,
    condition: item.condition,
    note: item.note
  };
  return setting.queryTemplate.replace(/\{([^}]+)\}/g, (_, key) => variables[key] || "").trim();
}

function priceLink(item) {
  const setting = linkSettings.find((entry) => entry.enabled && entry.genre === item.genre)
    || linkSettings.find((entry) => entry.enabled && entry.genre === "その他");
  const query = encodeURIComponent(buildQuery(item, setting));
  return setting.urlTemplate.replace("{query}", query);
}

function statusClass(status) {
  if (status === "売却済み") return "sold";
  if (status === "取置中") return "hold";
  if (status === "削除済み") return "deleted";
  return "";
}

function fieldInput(item, key, type = "text") {
  return `<input data-key="${key}" type="${type}" value="${String(item[key] ?? "").replaceAll('"', "&quot;")}">`;
}

function moneyInput(item, key) {
  return `<input data-key="${key}" inputmode="numeric" pattern="[0-9]*" value="${String(item[key] ?? "").replaceAll('"', "&quot;")}">`;
}

function detailField(item, label, key, type = "text", readonly = false) {
  const readonlyAttribute = readonly ? "readonly" : "";
  const readonlyClass = readonly ? " readonly-field" : "";
  return `
    <label class="${readonlyClass}">
      ${label}
      <input name="${key}" type="${type}" value="${String(item[key] ?? "").replaceAll('"', "&quot;")}" ${readonlyAttribute}>
    </label>
  `;
}

function renderEditRow(item) {
  return `
    <tr data-id="${item.id}">
      <td></td>
      <td>${fieldInput(item, "genre")}</td>
      <td>${fieldInput(item, "cardName")}</td>
      <td>${fieldInput(item, "note")}</td>
      <td>${fieldInput(item, "quantity", "number")}</td>
      <td>${moneyInput(item, "salePrice")}</td>
      <td>${fieldInput(item, "lastCheckedAt", "date")}</td>
      <td>
        <select data-key="status">
          ${["販売中", "売却済み", "取置中", "販売停止", "削除済み"].map((status) => `<option ${status === item.status ? "selected" : ""}>${status}</option>`).join("")}
        </select>
      </td>
      <td><a class="price-link" href="${priceLink(item)}" target="_blank" rel="noreferrer">価格確認</a></td>
      <td class="row-actions">
        <button class="primary" data-action="save">保存</button>
        <button class="secondary" data-action="cancel">キャンセル</button>
      </td>
    </tr>
  `;
}

function renderViewRow(item) {
  const checked = selectedIds.has(item.id) ? "checked" : "";
  return `
    <tr data-id="${item.id}">
      <td><input type="checkbox" data-action="select" ${checked} aria-label="${item.cardName}を選択"></td>
      <td>${item.genre}</td>
      <td><strong>${item.cardName}</strong><br><span class="muted">${item.setName || "-"} / ${item.rarity || "-"} / ${item.condition || "-"} / ${item.language || "-"}</span></td>
      <td>${item.note || "-"}</td>
      <td>${item.quantity}</td>
      <td>${yen(item.salePrice)}</td>
      <td>${item.lastCheckedAt}<br><span class="muted">${daysBetween(item.lastCheckedAt)}日前</span></td>
      <td><span class="status ${statusClass(item.status)}">${item.status}</span></td>
      <td><a class="price-link" href="${priceLink(item)}" target="_blank" rel="noreferrer">価格確認</a></td>
      <td class="row-actions">
        <button class="secondary" data-action="edit">編集</button>
        <button class="secondary" data-action="duplicate">複製</button>
        <button class="secondary" data-action="detail">詳細編集</button>
      </td>
    </tr>
  `;
}

function renderDetailEditor() {
  const overlay = document.querySelector("#detailOverlay");
  const item = inventory.find((entry) => entry.id === detailEditingId);
  if (!item) {
    overlay.hidden = true;
    return;
  }

  overlay.hidden = false;
  document.querySelector("#detailMeta").textContent = `${item.id} / 登録日 ${item.registeredAt} / 更新日 ${item.updatedAt}`;
  document.querySelector("#detailFields").innerHTML = [
    detailField(item, "在庫ID", "id", "text", true),
    detailField(item, "ジャンル", "genre"),
    detailField(item, "カード名", "cardName"),
    detailField(item, "レア", "rarity"),
    detailField(item, "セット", "setName"),
    detailField(item, "言語", "language"),
    detailField(item, "コレクター番号", "collectorNumber"),
    detailField(item, "補足", "note"),
    detailField(item, "カード状態", "condition"),
    detailField(item, "枚数", "quantity", "number"),
    detailField(item, "買取価格", "buyPrice"),
    detailField(item, "販売価格", "salePrice"),
    `<label>在庫ステータス<select name="status">${["販売中", "売却済み", "取置中", "販売停止", "削除済み"].map((status) => `<option ${status === item.status ? "selected" : ""}>${status}</option>`).join("")}</select></label>`,
    detailField(item, "登録日", "registeredAt", "date", true),
    detailField(item, "最終確認日", "lastCheckedAt", "date"),
    detailField(item, "更新日", "updatedAt", "date", true),
    `<label class="wide">メモ<textarea name="memo" rows="3">${item.memo || ""}</textarea></label>`
  ].join("");
}

function closeDetailEditor() {
  detailEditingId = null;
  renderDetailEditor();
}

function saveDetailEditor(event) {
  event.preventDefault();
  const item = inventory.find((entry) => entry.id === detailEditingId);
  if (!item) return;
  const data = Object.fromEntries(new FormData(event.currentTarget).entries());
  [
    "genre",
    "cardName",
    "rarity",
    "setName",
    "language",
    "collectorNumber",
    "note",
    "condition",
    "status",
    "lastCheckedAt",
    "memo"
  ].forEach((key) => {
    item[key] = data[key] ?? "";
  });
  item.quantity = Number(data.quantity || 0);
  item.buyPrice = Number(data.buyPrice || 0);
  item.salePrice = Number(data.salePrice || 0);
  item.updatedAt = today;
  closeDetailEditor();
  showToast("詳細編集を保存しました");
  renderInventory();
}

function renderInventory() {
  applyFilters();
  const totalPages = Math.max(1, Math.ceil(filteredInventory.length / pageSize));
  if (currentPage > totalPages) currentPage = totalPages;
  const startIndex = (currentPage - 1) * pageSize;
  const pageItems = filteredInventory.slice(startIndex, startIndex + pageSize);
  body.innerHTML = pageItems.map((item) => editingId === item.id ? renderEditRow(item) : renderViewRow(item)).join("");
  document.querySelector("#metricOnSale").textContent = inventory.filter((item) => item.status === "販売中").length;
  document.querySelector("#metricStale").textContent = inventory.filter((item) => item.status === "販売中" && daysBetween(item.lastCheckedAt) >= 90).length;
  document.querySelector("#metricVisible").textContent = filteredInventory.length;
  document.querySelector("#metricSelected").textContent = selectedIds.size;
  document.querySelector("#selectAll").checked = pageItems.length > 0 && pageItems.every((item) => selectedIds.has(item.id));
  document.querySelector("#pageInfo").textContent = `${currentPage} / ${totalPages}ページ（${filteredInventory.length}件中 ${pageItems.length ? startIndex + 1 : 0}-${startIndex + pageItems.length}件を表示）`;
  document.querySelector("#prevPageButton").disabled = currentPage <= 1;
  document.querySelector("#nextPageButton").disabled = currentPage >= totalPages;
  updateFilterSummary();
}

function saveEdit(row) {
  const item = inventory.find((entry) => entry.id === row.dataset.id);
  row.querySelectorAll("[data-key]").forEach((input) => {
    const key = input.dataset.key;
    item[key] = ["quantity", "buyPrice", "salePrice"].includes(key) ? Number(input.value || 0) : input.value;
  });
  item.updatedAt = today;
  editingId = null;
  showToast("編集内容を保存しました");
  renderInventory();
}

function duplicateItem(item) {
  if (!confirmDiscardEdit(item.id)) return;
  const clone = {
    ...item,
    id: nextId(),
    registeredAt: today,
    lastCheckedAt: today,
    updatedAt: today
  };
  inventory.unshift(clone);
  selectedIds.delete(item.id);
  editingId = clone.id;
  currentPage = 1;
  showToast(`${item.cardName}を複製しました`);
  renderInventory();
}

function confirmDiscardEdit(nextId) {
  if (!editingId || editingId === nextId) return true;
  return confirm("未保存の編集内容があります。破棄して別の商品を編集しますか？");
}

function updateSelected(action) {
  if (!selectedIds.size) {
    showToast("商品が選択されていません");
    return;
  }
  if (!confirm(`${selectedIds.size}件に一括操作を実行します。よろしいですか？`)) return;
  inventory.forEach((item) => {
    if (selectedIds.has(item.id)) {
      action(item);
      item.updatedAt = today;
    }
  });
  showToast("一括操作を実行しました");
  renderInventory();
}

function renderSettings() {
  document.querySelector("#linkSettingsBody").innerHTML = linkSettings.map((setting) => `
    <tr>
      <td><input type="checkbox" ${setting.enabled ? "checked" : ""}></td>
      <td>${setting.genre}</td>
      <td>${setting.siteName}</td>
      <td>${setting.urlTemplate}</td>
    </tr>
  `).join("");

  document.querySelector("#columnSettings").innerHTML = displayColumns.map((column) => `
    <label><input type="checkbox" checked> ${column}</label>
  `).join("");
}

function addItem(event) {
  event.preventDefault();
  const data = Object.fromEntries(new FormData(event.currentTarget).entries());
  if (!data.genre || !data.cardName || !data.quantity || !data.salePrice) {
    showToast("必須項目を入力してください");
    return;
  }
  inventory.unshift({
    id: nextId(),
    genre: data.genre,
    cardName: data.cardName,
    rarity: data.rarity,
    setName: data.setName,
    language: data.language || "jp",
    collectorNumber: data.collectorNumber,
    note: data.note,
    condition: data.condition,
    quantity: Number(data.quantity),
    buyPrice: Number(data.buyPrice || 0),
    salePrice: Number(data.salePrice),
    status: data.status || "販売中",
    registeredAt: today,
    lastCheckedAt: data.lastCheckedAt || today,
    updatedAt: today,
    memo: data.memo
  });
  event.currentTarget.reset();
  showToast("ダミー在庫を追加しました");
  switchView("inventory");
  renderInventory();
}

function switchView(viewName) {
  document.querySelectorAll(".view").forEach((view) => view.classList.remove("active"));
  document.querySelector(`#view-${viewName}`).classList.add("active");
  document.querySelectorAll("[data-view]").forEach((button) => button.classList.toggle("active", button.dataset.view === viewName));
}

function validateCsv() {
  const lines = document.querySelector("#csvPreview").value.trim().split(/\r?\n/);
  const errors = [];
  lines.slice(1).forEach((line, index) => {
    const columns = line.split(",");
    if (columns.length < 17) errors.push(`${index + 2}行目: CSV列不足`);
    if (!columns[1] || !columns[2]) errors.push(`${index + 2}行目: 必須項目不足`);
    if (Number.isNaN(Number(columns[9]))) errors.push(`${index + 2}行目: 枚数の数値不正`);
    if (Number.isNaN(Number(columns[11]))) errors.push(`${index + 2}行目: 販売価格の数値不正`);
  });
  document.querySelector("#csvErrors").innerHTML = errors.length
    ? errors.map((error) => `<li>${error}</li>`).join("")
    : "<li>エラーは見つかりませんでした。取り込み可能です。</li>";
}

function exportCsv() {
  applyFilters();
  const header = "在庫ID,ジャンル,カード名,レア,セット,言語,コレクター番号,補足,カード状態,枚数,買取価格,販売価格,在庫ステータス,登録日,最終確認日,更新日,メモ";
  const rows = filteredInventory.map((item) => [
    item.id,
    item.genre,
    item.cardName,
    item.rarity,
    item.setName,
    item.language,
    item.collectorNumber,
    item.note,
    item.condition,
    item.quantity,
    item.buyPrice,
    item.salePrice,
    item.status,
    item.registeredAt,
    item.lastCheckedAt,
    item.updatedAt,
    item.memo
  ].join(","));
  console.log([header, ...rows].join("\n"));
  showToast("CSV内容をブラウザのコンソールに出力しました");
}

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => switchView(button.dataset.view));
});

toggleFiltersButton.addEventListener("click", () => {
  const willOpen = filterPanel.hidden;
  filterPanel.hidden = !willOpen;
  toggleFiltersButton.setAttribute("aria-expanded", String(willOpen));
  toggleFiltersButton.textContent = willOpen ? "絞り込みを閉じる" : "絞り込みを開く";
});

form.addEventListener("submit", (event) => {
  event.preventDefault();
  currentPage = 1;
  renderInventory();
});

document.querySelector("#clearFiltersButton").addEventListener("click", () => {
  form.reset();
  form.status.value = "販売中";
  currentPage = 1;
  renderInventory();
});

document.querySelector("#prevPageButton").addEventListener("click", () => {
  currentPage = Math.max(1, currentPage - 1);
  renderInventory();
});

document.querySelector("#nextPageButton").addEventListener("click", () => {
  const totalPages = Math.max(1, Math.ceil(filteredInventory.length / pageSize));
  currentPage = Math.min(totalPages, currentPage + 1);
  renderInventory();
});

body.addEventListener("click", (event) => {
  const action = event.target.dataset.action;
  if (!action) return;
  const row = event.target.closest("tr");
  const item = inventory.find((entry) => entry.id === row.dataset.id);

  if (action === "edit") {
    if (!confirmDiscardEdit(item.id)) return;
    editingId = item.id;
    renderInventory();
  }
  if (action === "detail") {
    if (!confirmDiscardEdit(item.id)) return;
    editingId = null;
    detailEditingId = item.id;
    renderDetailEditor();
  }
  if (action === "duplicate") {
    duplicateItem(item);
  }
  if (action === "cancel") {
    editingId = null;
    renderInventory();
  }
  if (action === "save") {
    saveEdit(row);
  }
});

body.addEventListener("change", (event) => {
  if (event.target.dataset.action !== "select") return;
  const id = event.target.closest("tr").dataset.id;
  if (event.target.checked) {
    selectedIds.add(id);
  } else {
    selectedIds.delete(id);
  }
  renderInventory();
});

document.querySelector("#selectAll").addEventListener("change", (event) => {
  const startIndex = (currentPage - 1) * pageSize;
  const pageItems = filteredInventory.slice(startIndex, startIndex + pageSize);
  pageItems.forEach((item) => {
    if (event.target.checked) {
      selectedIds.add(item.id);
    } else {
      selectedIds.delete(item.id);
    }
  });
  renderInventory();
});

document.querySelector("#markCheckedButton").addEventListener("click", () => {
  updateSelected((item) => {
    item.lastCheckedAt = today;
  });
});

document.querySelector("#soldSelectedButton").addEventListener("click", () => {
  updateSelected((item) => {
    item.status = "売却済み";
  });
});

document.querySelector("#deleteSelectedButton").addEventListener("click", () => {
  updateSelected((item) => {
    item.status = "削除済み";
  });
});

document.querySelector("#addForm").addEventListener("submit", addItem);
document.querySelector("#detailForm").addEventListener("submit", saveDetailEditor);
document.querySelector("#cancelDetailButton").addEventListener("click", closeDetailEditor);
document.querySelector("#closeDetailButton").addEventListener("click", closeDetailEditor);
document.querySelector("#validateCsvButton").addEventListener("click", validateCsv);
document.querySelector("#importCsvButton").addEventListener("click", () => showToast("サンプルのため実ファイル取込は行いません"));
document.querySelector("#exportCsvButton").addEventListener("click", exportCsv);

renderSettings();
renderDetailEditor();
renderInventory();
