const euro = (value) => "€" + Math.round(value).toLocaleString("en-US");

function fillSelect(select, values, selected) {
  select.innerHTML = "";
  for (const value of values) {
    const opt = document.createElement("option");
    opt.value = value;
    opt.textContent = value;
    if (value === selected) opt.selected = true;
    select.appendChild(opt);
  }
}

async function loadOptions() {
  const res = await fetch("/api/options");
  const options = await res.json();

  const modelSelect = document.getElementById("f-model");
  const sizeSelect = document.getElementById("f-size");

  fillSelect(modelSelect, options.models);
  fillSelect(sizeSelect, options.model_sizes[modelSelect.value]);
  fillSelect(document.getElementById("f-color"), options.colors);
  fillSelect(document.getElementById("f-leather"), options.leathers);
  fillSelect(document.getElementById("f-hardware"), options.hardware);
  fillSelect(document.getElementById("f-condition"), options.conditions, "Excellent");

  modelSelect.addEventListener("change", () => {
    fillSelect(sizeSelect, options.model_sizes[modelSelect.value]);
  });
}

function setupHeroZoom() {
  const heroBag = document.getElementById("hero-bag");
  const hero = document.getElementById("hero");

  function update() {
    const heroHeight = hero.offsetHeight;
    const progress = Math.min(Math.max(window.scrollY / heroHeight, 0), 1);
    const scale = 1 + progress * 1.6;
    const opacity = 1 - progress * 1.05;
    heroBag.style.transform = `scale(${scale})`;
    heroBag.style.opacity = Math.max(opacity, 0);
  }

  window.addEventListener("scroll", update, { passive: true });
  window.addEventListener("resize", update);
  update();
}

function setupDiscoverButton() {
  document.getElementById("discover-btn").addEventListener("click", () => {
    document.getElementById("content").scrollIntoView({ behavior: "smooth" });
  });
}

function renderComparables(tbody, comparables) {
  tbody.innerHTML = "";
  for (const comp of comparables) {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${comp.label}</td>
      <td>${comp.year}</td>
      <td>${comp.condition}</td>
      <td>${comp.price_formatted}</td>
      <td>${comp.similarity}/100</td>
    `;
    tbody.appendChild(tr);
  }
}

function renderResults(data) {
  document.getElementById("r-fair-value").textContent = data.fair_value_formatted;
  document.getElementById("r-asking-price").textContent = data.asking_price_formatted;
  document.getElementById("r-upside").textContent = data.upside_formatted;

  const recEl = document.getElementById("r-recommendation");
  const badge = document.getElementById("r-rec-badge");
  const text = document.getElementById("r-rec-text");

  recEl.classList.remove("buy", "negotiate", "pass");
  const recCopy = {
    BUY: ["BUY", "Attractive price relative to comparable sales."],
    NEGOTIATE: ["NEGOTIATE", "Fairly priced overall, but there may be room to negotiate."],
    PASS: ["PASS", "The asking price appears above comparable market value."],
  };
  const [label, copy] = recCopy[data.recommendation] ?? [data.recommendation, ""];
  recEl.classList.add(data.recommendation.toLowerCase());
  badge.textContent = label;
  text.textContent = copy;

  document.getElementById("r-investment-score").textContent = `${data.investment_score}/100`;
  document.getElementById("r-discount").textContent = `${data.discount}%`;
  document.getElementById("r-confidence").textContent = `${data.confidence}%`;

  const bars = [
    ["investment", data.investment_score],
    ["liquidity", data.liquidity_score],
    ["rarity", data.rarity_score],
  ];
  for (const [key, value] of bars) {
    document.getElementById(`r-${key}-bar`).style.width = `${value}%`;
    document.getElementById(`r-${key}-pct`).textContent = `${value}/100`;
  }

  renderComparables(document.querySelector("#r-comparables tbody"), data.comparables);

  document.getElementById("results-panel").hidden = false;
  document.getElementById("results-panel").scrollIntoView({ behavior: "smooth", block: "start" });
}

function setupForm() {
  const form = document.getElementById("bag-form");
  const errorEl = document.getElementById("form-error");
  const submitBtn = form.querySelector(".submit-btn");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorEl.hidden = true;
    submitBtn.disabled = true;
    submitBtn.textContent = "Calculating…";

    const formData = new FormData(form);
    const payload = {
      model: formData.get("model"),
      size: Number(formData.get("size")),
      color: formData.get("color"),
      leather: formData.get("leather"),
      hardware: formData.get("hardware"),
      year: Number(formData.get("year")),
      condition: formData.get("condition"),
      price: Number(formData.get("price")),
    };

    try {
      const res = await fetch("/api/valuate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const err = await res.json();
        errorEl.textContent = err.detail || "Something went wrong.";
        errorEl.hidden = false;
        document.getElementById("results-panel").hidden = true;
        return;
      }

      const data = await res.json();
      renderResults(data);
    } catch (e) {
      errorEl.textContent = "Could not reach the server.";
      errorEl.hidden = false;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Generate Estimate";
    }
  });
}

loadOptions();
setupHeroZoom();
setupDiscoverButton();
setupForm();
