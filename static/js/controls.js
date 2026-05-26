document.addEventListener("DOMContentLoaded", () => {
  const startInput = document.getElementById("start_time");
  const endInput = document.getElementById("end_time");
  if (!startInput || !endInput) return;

  startInput.addEventListener("change", () => {
    if (!startInput.value || endInput.value) return;
    const start = new Date(startInput.value);
    start.setHours(start.getHours() + 1);
    const pad = (n) => String(n).padStart(2, "0");
    endInput.value = `${start.getFullYear()}-${pad(start.getMonth() + 1)}-${pad(start.getDate())}T${pad(start.getHours())}:${pad(start.getMinutes())}`;
  });
});
