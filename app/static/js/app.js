document.addEventListener("htmx:configRequest", (event) => {
  const token = document.querySelector("meta[name='csrf-token']")?.content;
  if (token) {
    event.detail.headers["X-CSRFToken"] = token;
  }
});

/* === Menu Drawer Toggle === */
(function () {
  const menuBtn = document.getElementById("menu-toggle");
  const drawer = document.getElementById("menu-drawer");
  if (!menuBtn || !drawer) return;

  menuBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    drawer.hidden = !drawer.hidden;
  });

  document.addEventListener("click", (e) => {
    if (!drawer.hidden && !drawer.contains(e.target) && e.target !== menuBtn) {
      drawer.hidden = true;
    }
  });
})();

document.addEventListener("click", (event) => {
  const item = event.target.closest(".search-item[data-paciente-id]");
  if (!item) return;

  const pacienteId = item.dataset.pacienteId;
  const pacienteLabel = item.dataset.pacienteLabel;

  const input = document.querySelector("input[name='paciente_query']");
  const hidden = document.querySelector("#paciente_id");
  const results = document.querySelector("#paciente-results");

  if (input) input.value = pacienteLabel || "";
  if (hidden) hidden.value = pacienteId || "";
  if (results) results.innerHTML = "";
});

function normalizeTimeChoices(rawChoices) {
  const values = [];
  (rawChoices || []).forEach((item) => {
    let value = "";
    if (Array.isArray(item)) {
      value = String(item[0] ?? "");
    } else if (item instanceof HTMLOptionElement) {
      value = String(item.value || "");
    } else {
      value = String(item || "");
    }

    if (!/^\d{2}:\d{2}$/.test(value)) return;
    values.push(value);
  });

  const uniqueValues = Array.from(new Set(values)).sort();
  const minutesByHour = new Map();
  uniqueValues.forEach((value) => {
    const [hour, minute] = value.split(":");
    if (!minutesByHour.has(hour)) {
      minutesByHour.set(hour, []);
    }
    minutesByHour.get(hour).push(minute);
  });

  minutesByHour.forEach((minutes) => minutes.sort());
  const hours = Array.from(minutesByHour.keys()).sort();

  return {
    values: uniqueValues,
    hours,
    minutesByHour,
  };
}

function buildTimeSplitPicker(rawChoices, selectedValue, onValueChange) {
  const normalized = normalizeTimeChoices(rawChoices);
  if (!normalized.hours.length) return null;

  const wrapper = document.createElement("div");
  wrapper.className = "time-split-picker-ui";

  const hourSelect = document.createElement("select");
  hourSelect.className = "input time-part-select time-hour";
  normalized.hours.forEach((hour) => {
    const option = document.createElement("option");
    option.value = hour;
    option.textContent = hour;
    hourSelect.appendChild(option);
  });

  const separator = document.createElement("span");
  separator.className = "time-separator";
  separator.textContent = ":";

  const minuteSelect = document.createElement("select");
  minuteSelect.className = "input time-part-select time-minute";

  wrapper.appendChild(hourSelect);
  wrapper.appendChild(separator);
  wrapper.appendChild(minuteSelect);

  const knownValues = new Set(normalized.values);
  const fallbackValue = normalized.values[0];
  const initialValue = knownValues.has(String(selectedValue))
    ? String(selectedValue)
    : fallbackValue;
  const [initialHour, initialMinute] = initialValue.split(":");

  function refreshMinuteOptions(preferredMinute) {
    const minuteOptions = normalized.minutesByHour.get(hourSelect.value) || [];
    minuteSelect.innerHTML = "";
    minuteOptions.forEach((minute) => {
      const option = document.createElement("option");
      option.value = minute;
      option.textContent = minute;
      minuteSelect.appendChild(option);
    });

    if (preferredMinute && minuteOptions.includes(preferredMinute)) {
      minuteSelect.value = preferredMinute;
    } else if (minuteOptions.length > 0) {
      minuteSelect.value = minuteOptions[0];
    }
  }

  function currentValue() {
    return `${hourSelect.value}:${minuteSelect.value}`;
  }

  hourSelect.value = initialHour;
  refreshMinuteOptions(initialMinute);

  hourSelect.addEventListener("change", () => {
    refreshMinuteOptions(null);
    onValueChange(currentValue());
  });
  minuteSelect.addEventListener("change", () => {
    onValueChange(currentValue());
  });

  return {
    wrapper,
    getValue: currentValue,
  };
}

(() => {
  const placeholders = document.querySelectorAll(".time-split-picker[data-source-field-id]");
  if (!placeholders.length) return;

  placeholders.forEach((placeholder) => {
    const fieldId = placeholder.getAttribute("data-source-field-id");
    if (!fieldId) return;

    const sourceField = document.getElementById(fieldId);
    if (!(sourceField instanceof HTMLSelectElement)) return;

    const picker = buildTimeSplitPicker(
      Array.from(sourceField.options),
      sourceField.value,
      (nextValue) => {
        sourceField.value = nextValue;
        sourceField.dispatchEvent(new Event("change", { bubbles: true }));
      }
    );
    if (!picker) return;

    sourceField.value = picker.getValue();
    placeholder.innerHTML = "";
    placeholder.appendChild(picker.wrapper);

    const fieldWrapper = sourceField.closest(".time-field");
    if (fieldWrapper) {
      fieldWrapper.classList.add("is-enhanced");
    }
  });
})();

(() => {
  const filtersForm = document.querySelector("#agenda-filters");
  const loadingIndicator = document.querySelector("#agenda-loading");
  const dateInput = document.querySelector("#agenda-fecha-input");
  const consultorioInput = document.querySelector("#agenda-consultorio-id");
  const consultorioPills = document.querySelector(".consultorio-pills");
  const dayNav = document.querySelector("#agenda-day-nav");
  const dayLabel = document.querySelector("#agenda-day-label");
  if (!filtersForm || !loadingIndicator || !dateInput || !dayNav) return;

  const WEEKDAYS_ES = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"];

  function parseIsoDate(value) {
    if (!value || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return null;
    const [year, month, day] = value.split("-").map(Number);
    const parsed = new Date(year, month - 1, day);
    if (Number.isNaN(parsed.getTime())) return null;
    return parsed;
  }

  function formatIsoDate(dateValue) {
    const year = dateValue.getFullYear();
    const month = String(dateValue.getMonth() + 1).padStart(2, "0");
    const day = String(dateValue.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
  }

  function formatAgendaLabel(dateValue) {
    const weekday = WEEKDAYS_ES[(dateValue.getDay() + 6) % 7];
    const day = dateValue.getDate();
    return `${weekday} ${day}`;
  }

  function isToday(dateValue) {
    const today = new Date();
    return (
      dateValue.getFullYear() === today.getFullYear() &&
      dateValue.getMonth() === today.getMonth() &&
      dateValue.getDate() === today.getDate()
    );
  }

  function updateDayHeaderUi() {
    const current = parseIsoDate(dateInput.value);
    if (!current) return;
    if (dayLabel) {
      dayLabel.textContent = formatAgendaLabel(current);
    }

    const todayChip = document.querySelector("#agenda-go-today");
    if (!todayChip) return;
    todayChip.hidden = isToday(current);
  }

  function submitDateChange(nextDate) {
    dateInput.value = formatIsoDate(nextDate);
    updateDayHeaderUi();
    dateInput.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function moveDay(offset) {
    const current = parseIsoDate(dateInput.value);
    if (!current) return;
    current.setDate(current.getDate() + offset);
    submitDateChange(current);
  }

  function isAgendaFilterEvent(event) {
    const source = event?.detail?.elt;
    if (!source) return false;
    if (source === filtersForm) return true;
    return source instanceof Element && Boolean(source.closest("#agenda-filters"));
  }

  function showLoading() {
    loadingIndicator.hidden = false;
  }

  function hideLoading() {
    loadingIndicator.hidden = true;
  }

  function syncFiltersToUrl() {
    const url = new URL(window.location.href);
    url.pathname = "/";

    const params = new URLSearchParams();
    const formData = new FormData(filtersForm);
    for (const [key, value] of formData.entries()) {
      if (typeof value !== "string") continue;
      if (!value.trim()) continue;
      params.set(key, value);
    }

    url.search = params.toString();
    window.history.replaceState({}, "", `${url.pathname}${url.search ? `?${url.search}` : ""}`);
  }

  function setActiveConsultorioPill(value) {
    if (!consultorioPills) return;
    consultorioPills.querySelectorAll(".pill").forEach((pill) => {
      const nextValue = String(pill.getAttribute("data-consultorio-pill") || "");
      pill.classList.toggle("is-active", nextValue === String(value || ""));
    });
  }

  dayNav.querySelectorAll("[data-day-offset]").forEach((link) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      const offset = Number(link.getAttribute("data-day-offset") || "0");
      if (!offset) return;
      moveDay(offset);
    });
  });

  const todayChip = document.querySelector("#agenda-go-today");
  if (todayChip) {
    todayChip.addEventListener("click", (event) => {
      event.preventDefault();
      const today = new Date();
      submitDateChange(today);
    });
  }

  if (consultorioInput && consultorioPills) {
    setActiveConsultorioPill(consultorioInput.value || "");

    consultorioPills.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof Element)) return;

      const pill = target.closest(".pill[data-consultorio-pill]");
      if (!pill) return;

      const nextValue = String(pill.getAttribute("data-consultorio-pill") || "");
      consultorioInput.value = nextValue;
      setActiveConsultorioPill(nextValue);
      consultorioInput.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  let touchStartX = null;
  let touchStartY = null;
  let touchStartTs = null;

  dayNav.addEventListener(
    "touchstart",
    (event) => {
      if (event.touches.length !== 1) return;
      const target = event.target;
      if (target instanceof Element && target.closest("a, button, input, select, label")) return;

      touchStartX = event.touches[0].clientX;
      touchStartY = event.touches[0].clientY;
      touchStartTs = Date.now();
    },
    { passive: true }
  );

  dayNav.addEventListener(
    "touchend",
    (event) => {
      if (touchStartX === null || touchStartY === null || touchStartTs === null) return;
      if (!event.changedTouches || event.changedTouches.length === 0) return;

      const dx = event.changedTouches[0].clientX - touchStartX;
      const dy = event.changedTouches[0].clientY - touchStartY;
      const dt = Date.now() - touchStartTs;

      touchStartX = null;
      touchStartY = null;
      touchStartTs = null;

      if (Math.abs(dx) < 60) return;
      if (Math.abs(dy) > 30) return;
      if (dt > 500) return;

      if (dx > 0) {
        moveDay(-1);
      } else {
        moveDay(1);
      }
    },
    { passive: true }
  );

  dateInput.addEventListener("change", updateDayHeaderUi);
  updateDayHeaderUi();

  document.body.addEventListener("htmx:beforeRequest", (event) => {
    if (!isAgendaFilterEvent(event)) return;
    showLoading();
  });

  document.body.addEventListener("htmx:afterRequest", (event) => {
    if (!isAgendaFilterEvent(event)) return;
    hideLoading();
    if (event.detail?.successful) {
      syncFiltersToUrl();
    }
  });

  ["htmx:responseError", "htmx:sendError", "htmx:timeout"].forEach((eventName) => {
    document.body.addEventListener(eventName, (event) => {
      if (!isAgendaFilterEvent(event)) return;
      hideLoading();
    });
  });
})();

(() => {
  const hiddenPatternsInput = document.querySelector("#recurrencia_patrones");
  if (!hiddenPatternsInput) return;

  const repeatCheckbox = document.querySelector("#repetir");
  const recurrencePanel = document.querySelector("#recurrencia-panel");
  const listContainer = document.querySelector("#recurrencia-patrones-list");
  const addButton = document.querySelector("#add-recurrencia-patron");
  const consultoriosScript = document.querySelector("#recurrencia-consultorios");
  const horasInicioScript = document.querySelector("#recurrencia-horas-inicio");
  const horasFinScript = document.querySelector("#recurrencia-horas-fin");

  if (
    !repeatCheckbox ||
    !recurrencePanel ||
    !listContainer ||
    !addButton ||
    !consultoriosScript ||
    !horasInicioScript ||
    !horasFinScript
  ) {
    return;
  }

  let consultorios = [];
  let horasInicio = [];
  let horasFin = [];
  try {
    consultorios = JSON.parse(consultoriosScript.textContent || "[]");
    horasInicio = JSON.parse(horasInicioScript.textContent || "[]");
    horasFin = JSON.parse(horasFinScript.textContent || "[]");
  } catch (_error) {
    consultorios = [];
    horasInicio = [];
    horasFin = [];
  }

  const weekdays = [
    [0, "Lunes"],
    [1, "Martes"],
    [2, "Miercoles"],
    [3, "Jueves"],
    [4, "Viernes"],
    [5, "Sabado"],
    [6, "Domingo"],
  ];

  function buildSelect(options, selectedValue) {
    const select = document.createElement("select");
    select.className = "input";
    options.forEach(([value, label]) => {
      const option = document.createElement("option");
      option.value = String(value);
      option.textContent = label;
      if (String(value) === String(selectedValue)) {
        option.selected = true;
      }
      select.appendChild(option);
    });
    return select;
  }

  function buildRecurrenceTimeField(options, selectedValue, role) {
    const wrapper = document.createElement("div");
    wrapper.className = "recurrence-time-field";

    const hidden = document.createElement("input");
    hidden.type = "hidden";
    hidden.dataset.role = role;

    const picker = buildTimeSplitPicker(options, selectedValue, (nextValue) => {
      hidden.value = nextValue;
    });

    if (!picker) {
      hidden.value = selectedValue || "";
      wrapper.appendChild(hidden);
      return wrapper;
    }

    hidden.value = picker.getValue();
    wrapper.appendChild(picker.wrapper);
    wrapper.appendChild(hidden);
    return wrapper;
  }

  function addPatternRow(initialData) {
    const row = document.createElement("div");
    row.className = "recurrence-row";

    const weekdaySelect = buildSelect(weekdays, initialData?.weekday ?? 0);
    weekdaySelect.dataset.role = "weekday";

    const startField = buildRecurrenceTimeField(
      horasInicio,
      initialData?.hora_inicio || "09:00",
      "hora_inicio"
    );

    const endField = buildRecurrenceTimeField(
      horasFin,
      initialData?.hora_fin || "09:30",
      "hora_fin"
    );

    const consultorioSelect = buildSelect(consultorios, initialData?.consultorio_id || consultorios[0]?.[0]);
    consultorioSelect.dataset.role = "consultorio_id";

    const removeButton = document.createElement("button");
    removeButton.type = "button";
    removeButton.className = "btn btn-ghost";
    removeButton.textContent = "Quitar";
    removeButton.dataset.action = "remove-pattern";

    row.appendChild(weekdaySelect);
    row.appendChild(startField);
    row.appendChild(endField);
    row.appendChild(consultorioSelect);
    row.appendChild(removeButton);

    listContainer.appendChild(row);
    serializePatterns();
  }

  function serializePatterns() {
    const rows = Array.from(listContainer.querySelectorAll(".recurrence-row"));
    const patterns = rows.map((row) => ({
      weekday: Number(row.querySelector('[data-role="weekday"]').value),
      hora_inicio: row.querySelector('[data-role="hora_inicio"]').value,
      hora_fin: row.querySelector('[data-role="hora_fin"]').value,
      consultorio_id: Number(row.querySelector('[data-role="consultorio_id"]').value),
    }));
    hiddenPatternsInput.value = JSON.stringify(patterns);
  }

  function getWeekdayFromDateInput() {
    const dateInput = document.querySelector("#fecha");
    if (!dateInput || !dateInput.value) return 0;
    const date = new Date(`${dateInput.value}T00:00:00`);
    if (Number.isNaN(date.getTime())) return 0;
    return (date.getDay() + 6) % 7;
  }

  function addFallbackPatternFromBaseFields() {
    const startInput = document.querySelector("#hora_inicio");
    const endInput = document.querySelector("#hora_fin");
    const consultorioSelect = document.querySelector("#consultorio_id");

    addPatternRow({
      weekday: getWeekdayFromDateInput(),
      hora_inicio: startInput?.value || "09:00",
      hora_fin: endInput?.value || "09:30",
      consultorio_id: consultorioSelect?.value || consultorios[0]?.[0],
    });
  }

  function toggleRecurrencePanel() {
    recurrencePanel.hidden = !repeatCheckbox.checked;
    if (repeatCheckbox.checked && listContainer.children.length === 0) {
      addFallbackPatternFromBaseFields();
    }
    serializePatterns();
  }

  addButton.addEventListener("click", () => {
    addPatternRow();
  });

  listContainer.addEventListener("click", (event) => {
    const target = event.target;
    if (!(target instanceof HTMLElement)) return;
    if (target.dataset.action !== "remove-pattern") return;

    const row = target.closest(".recurrence-row");
    if (!row) return;
    row.remove();
    serializePatterns();
  });

  listContainer.addEventListener("change", serializePatterns);
  listContainer.addEventListener("input", serializePatterns);
  repeatCheckbox.addEventListener("change", toggleRecurrencePanel);

  try {
    const current = JSON.parse(hiddenPatternsInput.value || "[]");
    if (Array.isArray(current) && current.length > 0) {
      current.forEach((item) => addPatternRow(item));
    }
  } catch (_error) {
    // ignore invalid payload; fallback below
  }

  toggleRecurrencePanel();
})();
