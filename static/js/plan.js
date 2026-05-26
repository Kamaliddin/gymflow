(() => {
  const COLS = [
    "day_number",
    "exercise_name",
    "set_number",
    "rep_goal",
    "weight",
    "time_per_set",
    "checkbox",
  ];
  const COL_LABELS = {
    day_number: "Day",
    exercise_name: "Exercise",
    set_number: "Set",
    rep_goal: "Rep goal",
    weight: "Weight",
    time_per_set: "Time/set",
    checkbox: "Done",
  };

  const app = document.getElementById("plan-app");
  if (!app) return;

  const container = document.getElementById("tables-container");
  const memberId = app.dataset.memberId;
  const dayFilter = app.dataset.day || "";
  const role = app.dataset.role || "";
  const isTrainer = role === "trainer" || role === "admin";

  let planData = null;
  let activePerm = { tableId: null, column: null };

  const permPanel = document.getElementById("perm-panel");
  const permBackdrop = document.getElementById("perm-backdrop");
  const permToggle = document.getElementById("perm-toggle-input");
  const permColLabel = document.getElementById("perm-col-label");

  async function api(path, opts = {}) {
    const res = await fetch(path, {
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
      ...opts,
    });
    if (res.status === 401) {
      window.location.href = "/login";
      throw new Error("Unauthorized");
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || "Request failed");
    }
    return res.json();
  }

  function qs() {
    const p = new URLSearchParams();
    if (memberId) p.set("member_id", memberId);
    if (dayFilter) p.set("day", dayFilter);
    return `/api/plan?${p}`;
  }

  async function loadPlan() {
    if (!memberId) {
      container.innerHTML = '<p class="plan-empty">Log in to view your workout plan.</p>';
      return;
    }
    planData = await api(qs());
    renderTables();
  }

  function tablesForView() {
    const tables = planData.tables || [];
    if (!dayFilter) return tables.slice(0, 3);
    return tables.slice(0, 3);
  }

  function renderTables() {
    container.innerHTML = "";
    const tables = tablesForView();
    if (!tables.length) {
      container.innerHTML = '<p class="plan-empty">No workout tables yet. Add one to get started.</p>';
      return;
    }
    tables.forEach((t) => container.appendChild(buildTableEl(t)));
  }

  function buildTableEl(table) {
    const tpl = document.getElementById("table-template");
    const node = tpl.content.cloneNode(true).querySelector(".workout-table");
    node.dataset.tableId = table.id;

    const nameInput = node.querySelector(".wt-name");
    nameInput.value = table.name;
    nameInput.disabled = !canEditTable(table);

    const days = table.repeat_days || [];
    node.querySelector(".wt-repeat-days").textContent = days.length
      ? `Days: ${days.join(", ")}`
      : "All days";
    node.querySelector(".wt-time").textContent = `Default: ${table.default_time || "08:00"}`;

    applyColumnDimming(node, table.column_permissions);
    renderRows(node, table);
    bindTableEvents(node, table);

    return node;
  }

  function canEditTable(table) {
    return table.can_edit_all || !table.is_trainer_view;
  }

  function memberCanEdit(table, col) {
    if (isTrainer) return true;
    return table.column_permissions?.[col] !== false;
  }

  function applyColumnDimming(node, perms) {
    node.querySelectorAll("thead th").forEach((th) => {
      const col = th.dataset.col;
      if (perms && perms[col] === false) th.classList.add("col-dimmed");
      else th.classList.remove("col-dimmed");
    });
  }

  function groupRows(rows) {
    const groups = [];
    let current = null;
    rows.forEach((r) => {
      const key = `${r.day_number}-${r.exercise_name}`;
      if (!current || current.key !== key) {
        current = { key, rows: [r] };
        groups.push(current);
      } else {
        current.rows.push(r);
      }
    });
    return groups;
  }

  function renderRows(node, table) {
    const tbody = node.querySelector("tbody");
    tbody.innerHTML = "";
    const groups = groupRows(table.rows || []);
    let rowIdx = 0;

    groups.forEach((g) => {
      g.rows.forEach((row, idx) => {
        const tr = document.createElement("tr");
        tr.dataset.rowId = row.id;
        tr.style.animationDelay = `${Math.min(rowIdx * 24, 240)}ms`;
        rowIdx += 1;

        if (idx === 0) {
          tr.appendChild(
            cellDay(row, table, g.rows.length)
          );
          tr.appendChild(
            cellExercise(row, table, g.rows.length)
          );
        }

        tr.appendChild(cellSet(row, table));
        tr.appendChild(cellText(row, table, "rep_goal"));
        tr.appendChild(cellWeight(row, table));
        tr.appendChild(cellText(row, table, "time_per_set"));
        tr.appendChild(cellCheckbox(row, table));
        tbody.appendChild(tr);
      });
    });

    updateFooter(node, table.rows || []);
  }

  function cellDay(row, table, rowspan) {
    const td = document.createElement("td");
    if (rowspan > 1) td.rowSpan = rowspan;
    const locked = !memberCanEdit(table, "day_number");
    td.className = locked ? "locked" : "";
    const inp = document.createElement("input");
    inp.type = "number";
    inp.min = 1;
    inp.max = 7;
    inp.value = row.day_number;
    inp.disabled = locked;
    inp.addEventListener("change", () => patchRow(row.id, { day_number: +inp.value }, table));
    td.appendChild(inp);
    return td;
  }

  function cellExercise(row, table, rowspan) {
    const td = document.createElement("td");
    td.className = "exercise-cell" + (!memberCanEdit(table, "exercise_name") ? " locked" : "");
    if (rowspan > 1) td.rowSpan = rowspan;

    const inp = document.createElement("input");
    inp.type = "text";
    inp.value = row.exercise_name || "";
    inp.placeholder = "Search or type…";
    inp.disabled = !memberCanEdit(table, "exercise_name");

    const list = document.createElement("ul");
    list.className = "exercise-dropdown hidden";

    let debounce;
    inp.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(async () => {
        const q = inp.value.trim();
        if (q.length < 1) {
          list.classList.add("hidden");
          return;
        }
        const items = await api(`/api/exercises?q=${encodeURIComponent(q)}`);
        list.innerHTML = "";
        items.forEach((ex) => {
          const li = document.createElement("li");
          li.textContent = ex.name;
          li.addEventListener("mousedown", (e) => {
            e.preventDefault();
            inp.value = ex.name;
            list.classList.add("hidden");
            patchRow(row.id, { exercise_name: ex.name, exercise_id: ex.id }, table);
          });
          list.appendChild(li);
        });
        const manual = document.createElement("li");
        manual.textContent = `Use "${q}" (manual)`;
        manual.style.fontStyle = "italic";
        manual.addEventListener("mousedown", (e) => {
          e.preventDefault();
          list.classList.add("hidden");
          patchRow(row.id, { exercise_name: q, exercise_id: null }, table);
        });
        list.appendChild(manual);
        list.classList.remove("hidden");
      }, 200);
    });

    inp.addEventListener("blur", () => {
      setTimeout(() => list.classList.add("hidden"), 150);
      if (inp.value !== row.exercise_name) {
        patchRow(row.id, { exercise_name: inp.value }, table);
      }
    });

    td.appendChild(inp);
    td.appendChild(list);
    return td;
  }

  function cellSet(row, table) {
    const td = document.createElement("td");
    const locked = !memberCanEdit(table, "set_number");
    td.className = locked ? "locked" : "";
    const inp = document.createElement("input");
    inp.type = "number";
    inp.min = 1;
    inp.value = row.set_number;
    inp.disabled = locked;
    inp.addEventListener("change", () => patchRow(row.id, { set_number: +inp.value }, table));
    td.appendChild(inp);
    return td;
  }

  function cellText(row, table, field) {
    const td = document.createElement("td");
    const locked = !memberCanEdit(table, field);
    td.className = locked ? "locked" : "";
    const inp = document.createElement("input");
    inp.type = "text";
    inp.value = row[field] || "";
    inp.disabled = locked;
    inp.addEventListener("change", () => {
      const payload = {};
      payload[field] = inp.value;
      patchRow(row.id, payload, table);
    });
    td.appendChild(inp);
    return td;
  }

  function cellWeight(row, table) {
    const td = document.createElement("td");
    const locked = !memberCanEdit(table, "weight");
    td.className = locked ? "locked" : "";
    const inp = document.createElement("input");
    inp.type = "number";
    inp.min = 0;
    inp.step = 0.5;
    inp.value = row.weight ?? 0;
    inp.disabled = locked;
    inp.addEventListener("change", () => patchRow(row.id, { weight: parseFloat(inp.value) || 0 }, table));
    td.appendChild(inp);
    return td;
  }

  function cellCheckbox(row, table) {
    const td = document.createElement("td");
    const colLocked = !memberCanEdit(table, "checkbox");
    const rowLocked = row.checkbox_locked && !isTrainer;
    td.className = colLocked || rowLocked ? "locked" : "";

    const wrap = document.createElement("label");
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = row.is_checked;
    cb.disabled = colLocked || (row.checkbox_locked && !isTrainer);
    cb.addEventListener("change", () => {
      cb.classList.remove("check-pop");
      void cb.offsetWidth;
      cb.classList.add("check-pop");
      const payload = { is_checked: cb.checked };
      if (isTrainer) payload.checkbox_locked = false;
      patchRow(row.id, payload, table);
    });

    if (isTrainer) {
      cb.addEventListener("contextmenu", (e) => {
        e.preventDefault();
        patchRow(row.id, { checkbox_locked: !row.checkbox_locked }, table);
      });
    }

    wrap.appendChild(cb);
    td.appendChild(wrap);
    return td;
  }

  function updateFooter(node, rows) {
    const sets = rows.length;
    const reps = rows.filter((r) => r.rep_goal).map((r) => parseFloat(r.rep_goal) || 0);
    const weights = rows.map((r) => parseFloat(r.weight) || 0);
    const checked = rows.filter((r) => r.is_checked).length;

    node.querySelector(".ft-sets").textContent = sets;
    node.querySelector(".ft-reps").textContent = reps.length
      ? (reps.reduce((a, b) => a + b, 0) / reps.length).toFixed(1)
      : "—";
    node.querySelector(".ft-weight").textContent = weights.length
      ? (weights.reduce((a, b) => a + b, 0) / weights.length).toFixed(1)
      : "0";
    node.querySelector(".ft-checks").textContent = `${checked}/${sets}`;
  }

  async function patchRow(rowId, data, table) {
    await api(`/api/rows/${rowId}`, { method: "PATCH", body: JSON.stringify(data) });
    await loadPlan();
  }

  function bindTableEvents(node, table) {
    const tableId = table.id;

    node.querySelector(".wt-name").addEventListener("change", async (e) => {
      await api(`/api/tables/${tableId}`, {
        method: "PATCH",
        body: JSON.stringify({ name: e.target.value }),
      });
    });

    const menuBtn = node.querySelector(".wt-menu-btn");
    const menu = node.querySelector(".wt-menu");
    menuBtn.addEventListener("click", () => menu.classList.toggle("hidden"));

    menu.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", async () => {
        menu.classList.add("hidden");
        const action = btn.dataset.action;
        if (action === "delete") {
          if (confirm("Delete this workout table?")) {
            await api(`/api/tables/${tableId}`, { method: "DELETE" });
            await loadPlan();
          }
        } else if (action === "change-time") {
          const t = prompt("Default time (HH:MM):", table.default_time || "08:00");
          if (t) {
            await api(`/api/tables/${tableId}`, {
              method: "PATCH",
              body: JSON.stringify({ default_time: t }),
            });
            await loadPlan();
          }
        } else if (action === "change-days") {
          const d = prompt(
            "Repeat on days (comma-separated 1-7, empty = all):",
            (table.repeat_days || []).join(",")
          );
          const days = d
            ? d.split(",").map((x) => parseInt(x.trim(), 10)).filter((n) => n >= 1 && n <= 7)
            : [];
          await api(`/api/tables/${tableId}`, {
            method: "PATCH",
            body: JSON.stringify({ repeat_days: days }),
          });
          await loadPlan();
        }
      });
    });

    node.querySelector(".btn-add-row").addEventListener("click", async () => {
      const last = (table.rows || []).slice(-1)[0];
      await api(`/api/tables/${tableId}/rows`, {
        method: "POST",
        body: JSON.stringify({
          table_id: tableId,
          day_number: last?.day_number || 1,
          exercise_name: last?.exercise_name || "",
          set_number: (last?.set_number || 0) + 1,
          weight: 0,
        }),
      });
      await loadPlan();
    });

    node.querySelectorAll("thead th").forEach((th) => {
      const col = th.dataset.col;
      const openPerm = (e) => {
        if (!isTrainer) return;
        e.preventDefault();
        activePerm = { tableId, column: col };
        permColLabel.textContent = COL_LABELS[col] || col;
        const allowed = table.column_permissions?.[col] !== false;
        permToggle.checked = allowed;
        permPanel.classList.remove("hidden");
        permBackdrop.classList.remove("hidden");
        permPanel.setAttribute("aria-hidden", "false");
      };
      th.addEventListener("contextmenu", openPerm);
      let pressTimer;
      th.addEventListener("touchstart", (e) => {
        pressTimer = setTimeout(() => openPerm(e), 500);
      });
      th.addEventListener("touchend", () => clearTimeout(pressTimer));
    });
  }

  permToggle.addEventListener("change", async () => {
    if (!activePerm.tableId) return;
    await api(`/api/tables/${activePerm.tableId}/permissions`, {
      method: "PATCH",
      body: JSON.stringify({
        column_name: activePerm.column,
        member_can_edit: permToggle.checked,
      }),
    });
    await loadPlan();
  });

  document.getElementById("perm-close").addEventListener("click", closePerm);
  permBackdrop.addEventListener("click", closePerm);

  function closePerm() {
    permPanel.classList.add("hidden");
    permBackdrop.classList.add("hidden");
    activePerm = { tableId: null, column: null };
  }

  document.getElementById("btn-add-table")?.addEventListener("click", async () => {
    const dayTables = (planData?.tables || []).length;
    if (dayFilter && dayTables >= 3) {
      alert("Maximum 3 tables per day.");
      return;
    }
    const name = prompt("Table name:", "Workout");
    const days = dayFilter ? [parseInt(dayFilter, 10)] : [];
    await api("/api/tables", {
      method: "POST",
      body: JSON.stringify({
        member_id: memberId ? parseInt(memberId, 10) : null,
        name: name || "Workout",
        repeat_days: days,
      }),
    });
    await loadPlan();
  });

  document.getElementById("day-filter")?.addEventListener("change", (e) => {
    const url = new URL(window.location.href);
    if (e.target.value) url.searchParams.set("day", e.target.value);
    else url.searchParams.delete("day");
    window.location.href = url.toString();
  });

  document.addEventListener("click", (e) => {
    if (!e.target.closest(".wt-menu-wrap")) {
      document.querySelectorAll(".wt-menu").forEach((m) => m.classList.add("hidden"));
    }
  });

  loadPlan().catch(console.error);
})();
