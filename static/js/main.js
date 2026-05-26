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

  // initialize canvas smoke system (may be disabled on low-end devices)
  initCanvasSmoke();
  let lastMove = 0;

  document.addEventListener("mousemove", (event) => {
    const now = Date.now();
    if (now - lastMove < 80) return;
    lastMove = now;
    createWave(layer, event.clientX, event.clientY, 10, 0.10);
    if (window.canvasSmoke && window.canvasSmoke.enabled) {
      window.canvasSmoke.attract(event.clientX, event.clientY);
    }
  });

  document.addEventListener("click", (event) => {
    createWave(layer, event.clientX, event.clientY, 20, 0.24);
    if (window.canvasSmoke && window.canvasSmoke.enabled) {
      window.canvasSmoke.burst(event.clientX, event.clientY);
    }
  });

  document.addEventListener("keydown", (event) => {
    const target = event.target;
    if (target instanceof HTMLElement && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) {
      const rect = target.getBoundingClientRect();
      createWave(layer, rect.left + rect.width / 2, rect.top + rect.height / 2, 14, 0.18);
      if (window.canvasSmoke && window.canvasSmoke.enabled) {
        window.canvasSmoke.attract(rect.left + rect.width / 2, rect.top + rect.height / 2 + 8);
      }
    }
  });

  document.addEventListener("input", (event) => {
    const target = event.target;
    if (target instanceof HTMLElement && ["INPUT", "TEXTAREA"].includes(target.tagName)) {
      const rect = target.getBoundingClientRect();
      createWave(layer, rect.left + rect.width / 2, rect.top + rect.height / 2, 10, 0.12);
      if (window.canvasSmoke && window.canvasSmoke.enabled) {
        window.canvasSmoke.attract(rect.left + rect.width / 2, rect.top + rect.height / 2 + 8);
      }
    }
  });
}

function spawnAmbientSmoke(layer, count) {
  for (let i = 0; i < count; i++) {
    const x = Math.random() * window.innerWidth;
    const y = Math.random() * window.innerHeight;
    const size = 38 + Math.random() * 30;
    const smoke = document.createElement("span");
    smoke.className = "smoke-particle";
    smoke.style.left = `${x}px`;
    smoke.style.top = `${y}px`;
    smoke.style.width = `${size}px`;
    smoke.style.height = `${size * 0.7}px`;
    smoke.style.opacity = 0.22;
    // initial random rotation
    smoke.style.transform = `translate(-50%, -50%) rotate(${Math.random() * 360}deg) scale(${0.14 + Math.random() * 0.22})`;
    layer.appendChild(smoke);
    setTimeout(() => smoke.remove(), 5200);
  }
}

// Smoke particle manager: simulated particles with simple physics
const smokeManager = {
  particles: [],
  max: 80,
  layer: null,
};

function addParticle(el, x, y, w, h, opacity) {
  if (smokeManager.particles.length >= smokeManager.max) {
    // reuse oldest
    const p = smokeManager.particles.shift();
    p.el.remove();
  }
  const vx = (Math.random() - 0.5) * 0.4;
  const vy = (Math.random() - 0.5) * 0.6 - 0.1; // slight upward bias
  const rot = Math.random() * 360;
  const rotSpeed = (Math.random() - 0.5) * 0.6;
  const life = 6 + Math.random() * 4;
  const p = { el, x, y, vx, vy, rot, rotSpeed, life, age: 0, baseOpacity: opacity || 0.28 };
  smokeManager.particles.push(p);
}

function createSmoke(layer, x, y, size, opacity) {
  if (!smokeManager.layer) smokeManager.layer = layer;
  const smoke = document.createElement("span");
  smoke.className = "smoke-particle";
  smoke.style.left = `${x}px`;
  smoke.style.top = `${y}px`;
  const w = Math.max(10, size + Math.random() * 28);
  const h = Math.max(8, size * (0.6 + Math.random() * 0.6));
  smoke.style.width = `${w}px`;
  smoke.style.height = `${h}px`;
  smoke.style.opacity = opacity ?? 0.28;
  smoke.style.transform = `translate(-50%, -50%) rotate(${Math.random() * 360}deg) scale(${0.12 + Math.random() * 0.26})`;
  layer.appendChild(smoke);
  addParticle(smoke, x, y, w, h, opacity || 0.28);
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

// animation loop for smoke particles
let lastSmokeTick = performance.now();
function smokeTick(now) {
  const dt = Math.min(0.05, (now - lastSmokeTick) / 1000);
  lastSmokeTick = now;
  const particles = smokeManager.particles;
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.age += dt;
    // random jitter
    p.vx += (Math.random() - 0.5) * 0.02;
    p.vy += (Math.random() - 0.5) * 0.02;
    // natural drift
    p.x += p.vx * 60 * dt;
    p.y += p.vy * 60 * dt;
    p.rot += p.rotSpeed * 30 * dt;
    const lifeRatio = Math.max(0, 1 - p.age / p.life);
    const opacity = Math.min(1, p.baseOpacity * lifeRatio * 1.2);
    p.el.style.transform = `translate(-50%, -50%) translate(${p.x - parseFloat(p.el.style.left)}px, ${p.y - parseFloat(p.el.style.top)}px) rotate(${p.rot}deg) scale(1)`;
    p.el.style.opacity = `${opacity}`;
    // remove if too old or offscreen
    if (p.age > p.life || p.x < -200 || p.x > window.innerWidth + 200 || p.y < -200 || p.y > window.innerHeight + 200) {
      p.el.remove();
      particles.splice(i, 1);
    }
  }

  // attraction: pull nearby particles towards mouse if present
  if (smokeManager.mouse) {
    const mx = smokeManager.mouse.x;
    const my = smokeManager.mouse.y;
    for (const p of particles) {
      const dx = mx - p.x;
      const dy = my - p.y;
      const dist = Math.hypot(dx, dy) + 0.001;
      const influence = Math.max(0, 1 - dist / 220);
      p.vx += (dx / dist) * 0.06 * influence;
      p.vy += (dy / dist) * 0.06 * influence;
    }
  }

  requestAnimationFrame(smokeTick);
}

  // Canvas-based smoke system: white flame-like smoke with tails
  function initCanvasSmoke() {
    // detect low-performance devices and disable if needed
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const isLowPerf = typeof navigator !== 'undefined' && (navigator.hardwareConcurrency && navigator.hardwareConcurrency <= 2);
    if (prefersReduced || isLowPerf) {
      window.canvasSmoke = { enabled: false };
      return;
    }

    const canvas = document.createElement('canvas');
    canvas.className = 'canvas-smoke';
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    const ctx = canvas.getContext('2d');

    const PARTICLE_COUNT = 80; // 10x larger than before
    const particles = [];

    function rand(min, max) { return min + Math.random() * (max - min); }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: rand(-0.3, 0.3),
        vy: rand(-0.2, 0.4),
        life: rand(8, 16),
        age: Math.random() * 8,
        size: rand(18, 80),
        alpha: rand(0.12, 0.32),
        angle: Math.random() * Math.PI * 2,
        spin: rand(-0.02, 0.02),
      });
    }

    let mouse = null;

    function attract(x, y) {
      mouse = { x, y, time: performance.now() };
    }

    function burst(x, y) {
      for (let i = 0; i < 8; i++) {
        particles.push({ x: x + rand(-12,12), y: y + rand(-12,12), vx: rand(-1.2,1.2), vy: rand(-1.6,-0.2), life: rand(3,6), age: 0, size: rand(10,36), alpha: 0.45, angle: Math.random()*Math.PI*2, spin: rand(-0.06,0.06) });
      }
    }

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resize);

    function step(dt) {
      ctx.clearRect(0,0,canvas.width,canvas.height);
      // subtle global haze (dark green tone - #076 -> #007766)
      ctx.fillStyle = 'rgba(0,119,102,0.02)';
      ctx.fillRect(0,0,canvas.width,canvas.height);

      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        // attraction to mouse
        if (mouse && performance.now() - mouse.time < 1200) {
          const dx = mouse.x - p.x;
          const dy = mouse.y - p.y;
          const d = Math.hypot(dx, dy) + 0.001;
          const f = Math.max(0, 1 - d / 380);
          p.vx += (dx / d) * 0.18 * f * dt * 60;
          p.vy += (dy / d) * 0.16 * f * dt * 60;
        } else {
          // gentle random flow
          p.vx += (Math.random()-0.5) * 0.02;
          p.vy += (Math.random()-0.5) * 0.02 - 0.01;
        }

        p.x += p.vx * dt * 60;
        p.y += p.vy * dt * 60;
        p.angle += p.spin * dt * 60;
        p.age += dt;

        const lifeRatio = 1 - p.age / p.life;
        const alpha = Math.max(0, Math.min(1, p.alpha * lifeRatio * 1.4));

        // flame-like tail: draw gradient ellipse with motion blur
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.angle);
        const gradient = ctx.createLinearGradient(-p.size*0.4, 0, p.size*0.8, 0);
        // dark green smoke set to #076 (expanded #007766 -> rgb(0,119,102))
        gradient.addColorStop(0, `rgba(0,119,102,${alpha*0.9})`);
        gradient.addColorStop(0.6, `rgba(0,119,102,${alpha*0.45})`);
        gradient.addColorStop(1, `rgba(0,119,102,0)`);
        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.ellipse(0, 0, p.size*0.6, p.size*0.35, 0, 0, Math.PI*2);
        ctx.fill();
        ctx.restore();

        // respawn if dead or far offscreen
        if (p.age > p.life || p.x < -200 || p.x > canvas.width + 200 || p.y < -200 || p.y > canvas.height + 200) {
          p.x = Math.random() * canvas.width;
          p.y = Math.random() * canvas.height;
          p.vx = rand(-0.3,0.3);
          p.vy = rand(-0.2,0.4);
          p.age = 0;
          p.life = rand(8,16);
          p.size = rand(18,80);
          p.alpha = rand(0.18,0.5);
        }
      }
    }

    let last = performance.now();
    function loop(now) {
      const dt = Math.min(0.06, (now - last) / 1000);
      last = now;
      step(dt);
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);

    window.canvasSmoke = { enabled: true, attract, burst };
  }
