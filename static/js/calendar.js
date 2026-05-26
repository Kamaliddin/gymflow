document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".session-actions form").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!confirm("Book this class?")) {
        e.preventDefault();
      }
    });
  });
});
