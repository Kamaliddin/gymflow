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
  const slideItems = [
    document.querySelector(".content-panel"),
    ...document.querySelectorAll(".page-header, .page-header h1, .page-header h2, .card"),
  ].filter(Boolean);
  const fadeItems = Array.from(document.querySelectorAll(".nav-link, .btn, .alert, .profile-wrap"));

  slideItems.forEach((el, index) => {
    el.classList.add("animate-slide-in");
    el.style.animationDelay = `${index * 80}ms`;
  });

  fadeItems.forEach((el, index) => {
    el.classList.add("animate-fade-in");
    el.style.animationDelay = `${Math.max(120, index * 50)}ms`;
  });
}

function initTypingText() {
  const textTargets = document.querySelectorAll(".page-header h1, .page-header h2, .content-panel h1, .content-panel h2, .login h1");
  textTargets.forEach((heading) => {
    const text = heading.textContent.trim();
    if (!text) return;

    const wrapper = document.createElement("span");
    wrapper.className = "typing-text text-unite typing-left";
    const charCount = text.length;
    const duration = Math.max(2.2, charCount * 0.08);
    wrapper.textContent = text;
    heading.textContent = "";
    heading.appendChild(wrapper);

    const animationName = window.getComputedStyle(heading).textAlign === "right" ? "typing-right" : "typing-left";
    if (animationName === "typing-right") {
      wrapper.classList.add("from-right");
    }

    wrapper.style.animation = `${animationName} ${duration}s steps(${charCount}, end) forwards, blink 0.8s step-end infinite alternate`;
    wrapper.style.animationDelay = "120ms";

    wrapper.addEventListener("animationend", (event) => {
      if (event.animationName === animationName) {
        wrapper.classList.add("typing-complete");
        wrapper.style.borderRightColor = "transparent";
      }
    });
  });
}

function initInteractionWaves() {
  const layer = document.createElement("div");
  layer.className = "interaction-layer";
  document.body.appendChild(layer);

  let lastMove = 0;

  document.addEventListener("mousemove", (event) => {
    const now = Date.now();
    if (now - lastMove < 150) return;
    lastMove = now;
    createWave(layer, event.clientX, event.clientY, 10, 0.10);
    if (Math.random() < 0.18) {
      createSmoke(layer, event.clientX, event.clientY, 12, 0.14);
    }
  });

  document.addEventListener("click", (event) => {
    createWave(layer, event.clientX, event.clientY, 20, 0.24);
    createSmoke(layer, event.clientX, event.clientY, 20, 0.16);
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) {
      const rect = target.getBoundingClientRect();
      createWave(layer, rect.left + rect.width / 2, rect.top + rect.height / 2, 14, 0.18);
      createSmoke(layer, rect.left + rect.width / 2, rect.top + rect.height / 2 + 8, 10, 0.11);
    }
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(target.tagName)) {
      const rect = target.getBoundingClientRect();
      createWave(layer, rect.left + rect.width / 2, rect.top + rect.height / 2, 10, 0.12);
      createSmoke(layer, rect.left + rect.width / 2, rect.top + rect.height / 2 + 8, 8, 0.09);
    }
  });
}

function createSmoke(layer, x, y, size, opacity) {
  const smoke = document.createElement("span");
  smoke.className = "smoke-particle";
  smoke.style.left = `${x}px`;
  smoke.style.top = `${y}px`;
  smoke.style.width = `${size + Math.random() * 12}px`;
  smoke.style.height = `${size + Math.random() * 12}px`;
  smoke.style.opacity = opacity;
  layer.appendChild(smoke);
  setTimeout(() => {
    smoke.remove();
  }, 2800);
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
