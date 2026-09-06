const WA = "77473858155";
const CATEGORY_ORDER = [
  "Уход за лицом",
  "Уход за зубами",
  "Волосы",
  "Тело и гигиена",
  "Солнцезащита",
  "Макияж",
  "Здоровье",
  "Еда и напитки",
  "Дом и быт",
  "Наборы",
  "Корейский раздел",
  "Бизнес и прочее",
];

const CATALOG_URL = "https://heyzine.com/flip-book/3b7be4e8fe.html#page/";

const money = (n) =>
  n == null
    ? "—"
    : new Intl.NumberFormat("ru-RU").format(n) + " ₸";

const waLink = (title) => {
  const text = `Здравствуйте! Хочу заказать: ${title}`;
  return `https://wa.me/${WA}?text=${encodeURIComponent(text)}`;
};

const products = Array.isArray(window.PRODUCTS) ? window.PRODUCTS : [];

const state = {
  category: "all",
  query: "",
  sort: "popular",
};

const chipsEl = document.getElementById("chips");
const gridEl = document.getElementById("grid");
const metaEl = document.getElementById("result-meta");
const searchEl = document.getElementById("search");
const sortEl = document.getElementById("sort");
const modal = document.getElementById("modal");

function counts() {
  const map = new Map();
  for (const p of products) {
    map.set(p.categoryName, (map.get(p.categoryName) || 0) + 1);
  }
  return map;
}

function renderChips() {
  const c = counts();
  const cats = CATEGORY_ORDER.filter((name) => c.has(name));
  const items = ["all", ...cats];
  chipsEl.innerHTML = items
    .map((name) => {
      const label = name === "all" ? `Все · ${products.length}` : `${name} · ${c.get(name)}`;
      const pressed = state.category === name ? "true" : "false";
      return `<button class="chip" type="button" data-cat="${name}" aria-pressed="${pressed}">${label}</button>`;
    })
    .join("");
}

function filtered() {
  const q = state.query.trim().toLowerCase();
  let list = products.filter((p) => {
    const catOk = state.category === "all" || p.categoryName === state.category;
    const text = `${p.title} ${p.categoryName} ${p.promo || ""} ${p.description || ""} ${p.sku || ""} ${p.volume || ""}`.toLowerCase();
    return catOk && (!q || text.includes(q));
  });
  if (state.sort === "popular") list.sort((a, b) => (b.favorites || 0) - (a.favorites || 0));
  if (state.sort === "price-asc") list.sort((a, b) => (a.priceMember ?? 1e12) - (b.priceMember ?? 1e12));
  if (state.sort === "price-desc") list.sort((a, b) => (b.priceMember ?? -1) - (a.priceMember ?? -1));
  if (state.sort === "name") list.sort((a, b) => a.title.localeCompare(b.title, "ru"));
  return list;
}

function excerpt(text) {
  if (!text) return "";
  const clean = text.replace(/\s+/g, " ").trim();
  return clean.length > 120 ? clean.slice(0, 117) + "…" : clean;
}

function cardHTML(p) {
  const promo = p.promo
    ? `<span class="badge-promo">${p.promo}</span>`
    : p.section === "korea"
      ? `<span class="badge-promo">Корея</span>`
      : "";
  const excerptHtml = p.description
    ? `<p class="card-excerpt">${excerpt(p.description)}</p>`
    : "";
  const priceMember = p.priceMember == null ? "Цена в WhatsApp" : money(p.priceMember);
  const priceGuest = p.priceGuest == null ? "" : money(p.priceGuest);
  const fav = p.favorites ? `${p.favorites} в избранном` : (p.volume || "");
  return `
    <article class="card" data-id="${p.id}">
      <div class="card-media" data-open="${p.id}">
        ${promo}
        <img src="${p.image}" alt="${p.title.replace(/"/g, "&quot;")}" loading="lazy" onerror="this.style.opacity='.25'" />
      </div>
      <div class="card-body">
        <p class="card-cat">${p.categoryName}</p>
        <h3>${p.title}</h3>
        ${excerptHtml}
        <div class="price-row">
          <span class="price-member">${priceMember}</span>
          <span class="price-guest">${priceGuest}</span>
        </div>
        <div class="meta-row">
          <span>PV ${p.pv ? new Intl.NumberFormat("ru-RU").format(p.pv) : "—"}</span>
          <span>${fav}</span>
        </div>
        <a class="btn btn-primary" href="${waLink(p.title)}" target="_blank" rel="noopener">Заказать</a>
      </div>
    </article>
  `;
}

function renderGrid() {
  const list = filtered();
  metaEl.textContent = list.length
    ? `Показано ${list.length} из ${products.length}`
    : "Ничего не найдено — попробуйте другой запрос";
  gridEl.innerHTML = list.length
    ? list.map(cardHTML).join("")
    : `<p class="empty">Товары не найдены</p>`;
}

function openModal(id) {
  const p = products.find((x) => x.id === Number(id));
  if (!p) return;
  document.getElementById("modal-img").src = p.image2 || p.image;
  document.getElementById("modal-img").alt = p.title;
  document.getElementById("modal-cat").textContent = p.categoryName;
  document.getElementById("modal-title").textContent = p.title;
  const promoEl = document.getElementById("modal-promo");
  if (p.promo) {
    promoEl.hidden = false;
    promoEl.textContent = "Акция: " + p.promo;
  } else {
    promoEl.hidden = true;
  }
  const metaBits = [];
  if (p.sku) metaBits.push("Код " + p.sku);
  if (p.volume) metaBits.push(p.volume);
  document.getElementById("modal-meta").textContent = metaBits.join(" · ");
  document.getElementById("modal-prices").innerHTML = `
    <div class="price-row">
      <span class="price-member">${p.priceMember == null ? "Цена по запросу" : money(p.priceMember)}</span>
      <span class="price-guest">${p.priceGuest == null ? "" : money(p.priceGuest)}</span>
    </div>
    <div class="meta-row">
      <span>${p.section === "korea" ? "Корейский раздел · заказ через WhatsApp" : "Для участников / до регистрации"}</span>
      <span>PV ${p.pv ? new Intl.NumberFormat("ru-RU").format(p.pv) : "—"}</span>
    </div>
  `;
  const descEl = document.getElementById("modal-desc");
  if (p.description) {
    descEl.hidden = false;
    descEl.textContent = p.description;
  } else {
    descEl.hidden = true;
  }
  const usageEl = document.getElementById("modal-usage");
  if (p.usage) {
    usageEl.hidden = false;
    usageEl.textContent = p.usage;
  } else {
    usageEl.hidden = true;
  }
  const compEl = document.getElementById("modal-composition");
  if (p.composition) {
    compEl.hidden = false;
    compEl.textContent = "Состав: " + p.composition;
  } else {
    compEl.hidden = true;
  }
  const catEl = document.getElementById("modal-catalog");
  if (p.catalogPage) {
    catEl.hidden = false;
    catEl.href = CATALOG_URL + p.catalogPage;
    catEl.textContent = "Страница " + p.catalogPage + " в каталоге 2026";
  } else {
    catEl.hidden = true;
  }
  const wa = document.getElementById("modal-wa");
  wa.href = waLink(p.title);
  if (typeof modal.showModal === "function") modal.showModal();
}

function render() {
  renderChips();
  renderGrid();
}

chipsEl.addEventListener("click", (e) => {
  const btn = e.target.closest("[data-cat]");
  if (!btn) return;
  state.category = btn.dataset.cat;
  render();
});

gridEl.addEventListener("click", (e) => {
  const open = e.target.closest("[data-open]");
  if (!open) return;
  openModal(open.dataset.open);
});

searchEl.addEventListener("input", () => {
  state.query = searchEl.value;
  renderGrid();
});

sortEl.addEventListener("change", () => {
  state.sort = sortEl.value;
  renderGrid();
});

document.getElementById("modal-close").addEventListener("click", () => modal.close());
modal.addEventListener("click", (e) => {
  if (e.target === modal) modal.close();
});

document.getElementById("stat-count").textContent = String(products.length);
render();
