(() => {
  const locale = navigator.language || "nl-NL";
  const numberFmt = new Intl.NumberFormat(locale, { minimumFractionDigits: 0, maximumFractionDigits: 1 });
  const dateFmtLong = new Intl.DateTimeFormat(locale, {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  const dateFmtShort = new Intl.DateTimeFormat(locale, {
    day: "numeric",
    month: "short",
  });

  const drinkOptions = window.DRINK_OPTIONS || [];
  const optionsById = Object.fromEntries(drinkOptions.map((d) => [d.id, d]));

  const dateInput = document.getElementById("log_date");
  const dateFormatted = document.getElementById("date-formatted");
  const dateWeekday = document.getElementById("date-weekday");
  const dateDisplay = document.getElementById("date-display");
  const drinkItemsInput = document.getElementById("drink_items");
  const unitsDisplay = document.getElementById("units-display");
  const basket = document.getElementById("drink-basket");
  const basketList = document.getElementById("basket-list");
  const unitsTotal = document.getElementById("units-total");
  const btnZero = document.getElementById("btn-zero");
  const btnSubmit = document.getElementById("btn-submit");
  const notesInput = document.getElementById("notes");
  const logStatus = document.getElementById("log-status");
  const logStatusIcon = document.getElementById("log-status-icon");
  const logStatusText = document.getElementById("log-status-text");

  const existingLogs = window.EXISTING_LOGS || {};

  let basketItems = {};
  let isZeroDay = false;
  /** @type {"unregistered" | "zero" | "drinks"} */
  let registrationState = "unregistered";
  let savedUnits = null;

  const selectedDate = window.LOG_SELECTED_DATE || window.LOG_TODAY;
  if (dateInput && selectedDate) {
    const today = parseDate(window.LOG_TODAY);
    const picked = parseDate(selectedDate);
    if (picked <= today) {
      dateInput.value = selectedDate;
    }
  }

  function parseDate(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    return new Date(y, m - 1, d);
  }

  function toIso(date) {
    const y = date.getFullYear();
    const m = String(date.getMonth() + 1).padStart(2, "0");
    const d = String(date.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }

  function updateDateDisplay() {
    const date = parseDate(dateInput.value);
    const todayIso = window.LOG_TODAY;
    const isToday = dateInput.value === todayIso;

    dateWeekday.textContent = isToday
      ? "Vandaag"
      : new Intl.DateTimeFormat(locale, { weekday: "long" }).format(date);
    dateFormatted.textContent = dateFmtLong.format(date);

    const nextBtn = document.getElementById("date-next");
    if (nextBtn) {
      nextBtn.disabled = isToday;
      nextBtn.classList.toggle("disabled", isToday);
    }
  }

  function formatUnits(value) {
    return numberFmt.format(value);
  }

  function calculateTotal() {
    let total = 0;
    for (const [id, count] of Object.entries(basketItems)) {
      total += (optionsById[id]?.units || 0) * count;
    }
    return Math.round(total * 10) / 10;
  }

  function syncHiddenFields() {
    const items = Object.entries(basketItems)
      .filter(([, count]) => count > 0)
      .map(([id, count]) => ({ id, count }));

    drinkItemsInput.value = JSON.stringify(items);

    const isUnset = registrationState === "unregistered";
    const total = isZeroDay ? 0 : calculateTotal();
    const displayTotal = isUnset ? "—" : formatUnits(total);

    unitsDisplay.textContent = displayTotal;

    unitsTotal.classList.toggle("units-total--unset", isUnset);
    unitsTotal.classList.toggle("units-total--zero", !isUnset && total === 0);
    unitsTotal.classList.toggle("units-total--active", !isUnset && total > 0);
    btnZero.classList.toggle("drink-tile-zero--active", registrationState === "zero");

    const hasItems = items.length > 0;
    basket.hidden = !hasItems;

    const hasSavedEntry = !!existingLogs[dateInput.value];
    btnSubmit.disabled = registrationState === "unregistered" && !hasSavedEntry;

    if (registrationState === "unregistered") {
      btnSubmit.textContent = "Kies drankjes of 'Geen alcohol'";
    } else if (registrationState === "zero") {
      btnSubmit.textContent = hasSavedEntry
        ? "Bijwerken — niet gedronken"
        : "Opslaan — niet gedronken";
    } else {
      btnSubmit.textContent = hasSavedEntry
        ? `Bijwerken — ${formatUnits(total)} standaardglazen`
        : `Opslaan — ${formatUnits(total)} standaardglazen`;
    }

    updateRegistrationStatus(total);
  }

  function updateRegistrationStatus(total) {
    if (!logStatus) return;

    logStatus.classList.remove("log-status--unregistered", "log-status--zero", "log-status--drinks");

    if (registrationState === "unregistered") {
      logStatus.classList.add("log-status--unregistered");
      logStatusIcon.textContent = "○";
      logStatusText.textContent = "Nog niet geregistreerd";
      return;
    }

    if (registrationState === "zero") {
      logStatus.classList.add("log-status--zero");
      logStatusIcon.textContent = "🌿";
      logStatusText.textContent = "Niet gedronken";
      return;
    }

    logStatus.classList.add("log-status--drinks");
    logStatusIcon.textContent = "🍺";
    const units = total > 0 ? total : (savedUnits ?? 0);
    logStatusText.textContent = `${formatUnits(units)} ${units === 1 ? "standaardglas" : "standaardglazen"} geregistreerd`;
  }

  function renderBasket() {
    basketList.innerHTML = "";

    for (const [id, count] of Object.entries(basketItems)) {
      if (count <= 0) continue;
      const drink = optionsById[id];
      if (!drink) continue;

      const li = document.createElement("li");
      li.className = "basket-item";
      li.innerHTML = `
        <span class="basket-item-icon" aria-hidden="true">${drink.icon}</span>
        <span class="basket-item-label">${drink.label}</span>
        <span class="basket-item-sub">${formatUnits(drink.units * count)} glas</span>
        <div class="basket-item-controls">
          <button type="button" class="basket-btn" data-action="dec" data-id="${id}" aria-label="Minder ${drink.label}">−</button>
          <span class="basket-count">${count}</span>
          <button type="button" class="basket-btn" data-action="inc" data-id="${id}" aria-label="Meer ${drink.label}">+</button>
        </div>
      `;
      basketList.appendChild(li);
    }

    syncHiddenFields();
  }

  function addDrink(id) {
    isZeroDay = false;
    registrationState = "drinks";
    basketItems[id] = (basketItems[id] || 0) + 1;
    renderBasket();

    const tile = document.querySelector(`.drink-tile[data-id="${id}"]`);
    if (tile) {
      tile.classList.add("drink-tile--pulse");
      setTimeout(() => tile.classList.remove("drink-tile--pulse"), 300);
    }
  }

  function adjustDrink(id, delta) {
    const next = (basketItems[id] || 0) + delta;
    if (next <= 0) {
      delete basketItems[id];
    } else {
      basketItems[id] = next;
    }
    if (Object.keys(basketItems).length === 0) {
      registrationState = "unregistered";
      isZeroDay = false;
    }
    renderBasket();
  }

  function clearBasket() {
    basketItems = {};
    isZeroDay = false;
    registrationState = "unregistered";
    renderBasket();
  }

  function setZeroDay() {
    if (registrationState === "zero") {
      isZeroDay = false;
      registrationState = "unregistered";
    } else {
      basketItems = {};
      isZeroDay = true;
      registrationState = "zero";
    }
    renderBasket();
  }

  function loadLogForDate(isoDate) {
    const entry = existingLogs[isoDate];

    basketItems = {};
    isZeroDay = false;
    registrationState = "unregistered";
    savedUnits = null;

    if (entry) {
      savedUnits = entry.units ?? null;
      if (entry.zero) {
        isZeroDay = true;
        registrationState = "zero";
      } else if (entry.items?.length) {
        registrationState = "drinks";
        for (const { id, count } of entry.items) {
          if (count > 0 && optionsById[id]) {
            basketItems[id] = count;
          }
        }
      } else if (entry.units > 0) {
        registrationState = "drinks";
      }
      if (notesInput) {
        notesInput.value = entry.notes || "";
      }
    } else if (notesInput) {
      notesInput.value = "";
    }

    renderBasket();
  }

  function onDateChange() {
    updateDateDisplay();
    loadLogForDate(dateInput.value);
  }

  function shiftDate(days) {
    const date = parseDate(dateInput.value);
    date.setDate(date.getDate() + days);
    const today = parseDate(window.LOG_TODAY);
    if (date > today) return;
    dateInput.value = toIso(date);
    onDateChange();
  }

  // Format unit labels on drink tiles
  document.querySelectorAll(".drink-units").forEach((el) => {
    const value = parseFloat(el.dataset.unitsValue);
    const label = value === 1 ? "glas" : "glas";
    el.textContent = `${formatUnits(value)} ${label}`;
  });

  document.querySelectorAll(".drink-tile[data-id]").forEach((tile) => {
    tile.addEventListener("click", () => addDrink(tile.dataset.id));
  });

  basketList.addEventListener("click", (e) => {
    const btn = e.target.closest(".basket-btn");
    if (!btn) return;
    const delta = btn.dataset.action === "inc" ? 1 : -1;
    adjustDrink(btn.dataset.id, delta);
  });

  document.getElementById("basket-clear")?.addEventListener("click", clearBasket);
  btnZero?.addEventListener("click", setZeroDay);

  document.getElementById("date-prev")?.addEventListener("click", () => shiftDate(-1));
  document.getElementById("date-next")?.addEventListener("click", () => shiftDate(1));
  document.getElementById("date-today")?.addEventListener("click", () => {
    dateInput.value = window.LOG_TODAY;
    onDateChange();
  });

  dateDisplay?.addEventListener("click", () => {
    if (dateInput.showPicker) {
      dateInput.showPicker();
    } else {
      dateInput.focus();
    }
  });

  dateInput?.addEventListener("change", () => {
    const today = parseDate(window.LOG_TODAY);
    const selected = parseDate(dateInput.value);
    if (selected > today) {
      dateInput.value = window.LOG_TODAY;
    }
    onDateChange();
  });

  onDateChange();
})();
