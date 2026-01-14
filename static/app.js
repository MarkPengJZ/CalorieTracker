const userId = "demo";

const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const searchResults = document.getElementById("searchResults");
const searchMeta = document.getElementById("searchMeta");
const favorites = document.getElementById("favorites");
const recents = document.getElementById("recents");
const macroForm = document.getElementById("macroForm");
const customMacros = document.getElementById("customMacros");
const templateForm = document.getElementById("templateForm");
const templates = document.getElementById("templates");

async function fetchJson(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error("Request failed");
  }
  return response.json();
}

function renderList(element, items, actions = []) {
  element.innerHTML = "";
  if (!items.length) {
    element.innerHTML = "<li class=\"empty\">No items yet.</li>";
    return;
  }
  items.forEach((item) => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div>
        <strong>${item.name}</strong>
        <span>${item.calories} kcal · P${item.protein} C${item.carbs} F${item.fat}</span>
        <span class="badge">${item.source ?? "catalog"}</span>
      </div>
    `;
    const buttons = document.createElement("div");
    buttons.className = "actions";
    actions.forEach((action) => {
      const button = document.createElement("button");
      button.textContent = action.label;
      button.addEventListener("click", () => action.handler(item));
      buttons.appendChild(button);
    });
    li.appendChild(buttons);
    element.appendChild(li);
  });
}

async function runSearch() {
  const query = searchInput.value.trim();
  if (!query) {
    searchResults.innerHTML = "";
    searchMeta.textContent = "";
    return;
  }
  const data = await fetchJson(`/api/search?q=${encodeURIComponent(query)}&user_id=${userId}`);
  searchMeta.textContent = data.cached
    ? `Showing cached results for "${query}".`
    : `Ranked results for "${query}".`;
  renderList(searchResults, data.results, [
    { label: "Add", handler: (item) => logItem(item.id) },
    { label: "Favorite", handler: (item) => addFavorite(item.id) },
  ]);
}

async function logItem(itemId) {
  await fetchJson("/api/log", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId, user_id: userId }),
  });
  await refreshRecents();
}

async function addFavorite(itemId) {
  await fetchJson(`/api/favorites?user_id=${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ item_id: itemId }),
  });
  await refreshFavorites();
}

async function refreshFavorites() {
  const data = await fetchJson(`/api/favorites?user_id=${userId}`);
  renderList(favorites, data.favorites);
}

async function refreshRecents() {
  const data = await fetchJson(`/api/recents?user_id=${userId}`);
  renderList(recents, data.recents);
}

async function refreshCustomMacros() {
  const data = await fetchJson(`/api/custom_macros?user_id=${userId}`);
  renderList(customMacros, data.custom_macros, [
    { label: "Add", handler: (item) => logItem(item.id) },
  ]);
}

async function refreshTemplates() {
  const data = await fetchJson(`/api/meal_templates?user_id=${userId}`);
  templates.innerHTML = "";
  if (!data.templates.length) {
    templates.innerHTML = "<p class=\"empty\">No templates yet.</p>";
    return;
  }
  data.templates.forEach((template) => {
    const card = document.createElement("div");
    card.className = "template";
    card.innerHTML = `
      <h3>${template.name}</h3>
      <p>${template.items.length} items · ${template.totals.calories} kcal</p>
      <ul>${template.items
        .map((item) => `<li>${item.name} (${item.calories} kcal)</li>`)
        .join("")}</ul>
    `;
    templates.appendChild(card);
  });
}

searchButton.addEventListener("click", runSearch);
searchInput.addEventListener("keyup", (event) => {
  if (event.key === "Enter") {
    runSearch();
  }
});

macroForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(macroForm);
  const payload = Object.fromEntries(formData.entries());
  await fetchJson(`/api/custom_macros?user_id=${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  macroForm.reset();
  await refreshCustomMacros();
});

templateForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const recentsData = await fetchJson(`/api/recents?user_id=${userId}`);
  if (!recentsData.recents.length) {
    alert("Add recent items before creating a template.");
    return;
  }
  const formData = new FormData(templateForm);
  const name = formData.get("name");
  const payload = {
    name,
    items: recentsData.recents.map((item) => item.id),
  };
  await fetchJson(`/api/meal_templates?user_id=${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  templateForm.reset();
  await refreshTemplates();
});

async function init() {
  await refreshFavorites();
  await refreshRecents();
  await refreshCustomMacros();
  await refreshTemplates();
}

init();
