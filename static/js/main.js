document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("is-loaded");

  document.querySelectorAll(".alert").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });

  const profileBtn = document.getElementById("profile-menu-btn");
  const profileMenu = document.getElementById("profile-menu");
  if (profileBtn && profileMenu) {
    profileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      profileMenu.classList.toggle("hidden");
    });
    document.addEventListener("click", () => profileMenu.classList.add("hidden"));
  }
});
