document.addEventListener("DOMContentLoaded", () => {
  document.body.classList.add("is-loaded");

  animateBlocks();
  initTypingText();
  initInteractionWaves();
  autoDismissAlerts();
  initProfileMenu();
});

function autoDismissAlerts() {
  document.querySelectorAll(".alert").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity 0.4s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
}

function initProfileMenu() {
  const profileBtn = document.getElementById("profile-menu-btn");
  const profileMenu = document.getElementById("profile-menu");
  if (profileBtn && profileMenu) {
    profileBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      profileMenu.classList.toggle("hidden");
    });
    document.addEventListener("click", () => profileMenu.classList.add("hidden"));
  }
}

function animateBlocks() {
  const blocks = [
    document.querySelector(".content-panel"),
    ...document.querySelectorAll(".card, .page-header, .page-header h1, .page-header h2, .nav-link, .btn, .alert"),
  ].filter(Boolean);
  const animationClasses = ["animate-slide-in", "animate-rotate-in", "animate-fade-in"];
  blocks.forEach((el, index) => {
    const animation = animationClasses[index % animationClasses.length];
    el.classList.add(animation);
    el.style.animationDelay = `${Math.min(index * 55, 400)}ms`;
  });
}

function initTypingText() {
  const textTargets = document.querySelectorAll(".page-header h1, .page-header h2, .content-panel h1, .content-panel h2, .login h1");
  textTargets.forEach((heading) => {
    if (!heading.textContent.trim()) return;
    const wrapper = document.createElement("span");
    wrapper.className = "typing-text text-unite";
    wrapper.textContent = heading.textContent.trim();
    heading.textContent = "";
    heading.appendChild(wrapper);
    wrapper.style.animationDelay = "150ms";
  });
}

function initInteractionWaves() {
  const layer = document.createElement("div");
  layer.className = "interaction-layer";
  document.body.appendChild(layer);

  let lastMove = 0;

  document.addEventListener("mousemove", (event) => {
    const now = Date.now();
    if (now - lastMove < 120) return;
    lastMove = now;
    createWave(layer, event.clientX, event.clientY, 10, 0.12);
  });

  document.addEventListener("click", (event) => {
    createWave(layer, event.clientX, event.clientY, 20, 0.25);
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) {
      const rect = target.getBoundingClientRect();
      createWave(layer, rect.left + rect.width / 2, rect.top + rect.height / 2, 14, 0.18);
    }
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(target.tagName)) {
      const rect = target.getBoundingClientRect();
      createWave(layer, rect.left + rect.width / 2, rect.top + rect.height / 2, 10, 0.12);
    }
  });
}

function createWave(layer, x, y, size, opacity) {
  const wave = document.createElement("span");
  wave.className = "interaction-wave";
  wave.style.left = `${x}px`;
  wave.style.top = `${y}px`;
  wave.style.width = `${size * 2}px`;
  wave.style.height = `${size * 2}px`;
  wave.style.opacity = opacity;
  layer.appendChild(wave);
  setTimeout(() => {
    wave.remove();
  }, 950);
}
