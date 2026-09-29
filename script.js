/**
 * ============================================================================
 * ORBITAL — Enhanced Interactive 3D Earth Globe Engine  (v2)
 * ============================================================================
 * An interactive, software-projected 3D Earth globe rendered on an HTML5
 * 2D canvas.  Additions over v1:
 *
 *  • Deep nebula / aurora layers behind the globe
 *  • Shooting-star / meteor particles
 *  • Multi-tier starfield (large slow + small fast parallax)
 *  • Thick multi-stop atmospheric limb with colour gradient
 *  • Specular sun highlight (top-left) and twilight terminator band
 *  • Orbiting satellite dot with trailing comet tail
 *  • Subtle city-light glow corona bleeding out of the sphere edge
 *  • Inertia-damped mouse + touch rotation (unchanged API)
 */

// ----------------------------------------------------------------------------
// 1. DOM Elements & Canvas Context
// ----------------------------------------------------------------------------
const canvas = document.querySelector('#space');
const ctx    = canvas.getContext('2d');

// ----------------------------------------------------------------------------
// 2. Global State & Configuration
// ----------------------------------------------------------------------------
let w, h, dpr;           // Viewport & pixel-ratio
let cx, cy, radius;      // Globe centre and radius
let frameSize;           // Offscreen projection buffer dimension

// Deep starfield layers — populated in setup()
let starsNear = [];      // Large, slow-moving foreground stars
let starsFar  = [];      // Tiny, fast background stars

// Shooting-star / meteor state
const METEOR_MAX  = 5;
let meteors = [];

// Satellite orbit state
const satellite = {
  angle  : 0.4,          // Current orbital angle (radians)
  trail  : [],           // Stores recent {x,y} positions for the comet tail
  TRAIL  : 32            // Max tail length
};

// Inertia target & current rotation angles
const target   = { x: -2.9, y: 0.45 };
const rotation = { x: -0.25, y: -4.28 };

// Offscreen Projection Buffers
let earthMap;            // Raw texture ImageData
let earthFrame;          // Projected sphere frame ImageData
let earthFrameCtx;       // 2D context of offscreen projection canvas

// Earth Texture Asset
const earthTexture = new Image();

// Utility: clamp
const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

// Utility: random in range
const rand = (a, b) => a + Math.random() * (b - a);

// ----------------------------------------------------------------------------
// 3. Texture Pre-processing
// ----------------------------------------------------------------------------
/**
 * Renders the loaded equirectangular Earth texture onto an offscreen canvas
 * and extracts raw ImageData for fast per-pixel sampling in the render loop.
 */
function makeEarthMap() {
  const mapW = 1024;
  const mapH = 512;
  const map  = document.createElement('canvas');
  map.width  = mapW;
  map.height = mapH;
  const mapCtx = map.getContext('2d');
  mapCtx.drawImage(earthTexture, 0, 0, mapW, mapH);
  earthMap = mapCtx.getImageData(0, 0, mapW, mapH);
}

// ----------------------------------------------------------------------------
// 4. 3D Spherical Raycasting & Projection
// ----------------------------------------------------------------------------
/**
 * Raycasts each pixel onto the 3D unit sphere, applies rotation matrices,
 * samples the equirectangular Earth map, computes Lambertian + specular
 * directional lighting, and writes the result to the projection buffer.
 */
function renderEarthMap() {
  if (!earthMap) return;

  const pixels = earthFrame.data;
  const map    = earthMap.data;
  const mapW   = earthMap.width;
  const mapH   = earthMap.height;

  // Precompute trig for current rotation
  const sy  = Math.sin(rotation.y);
  const cyy = Math.cos(rotation.y);
  const sx  = Math.sin(rotation.x);
  const cxx = Math.cos(rotation.x);

  const half = frameSize / 2;

  for (let y = 0; y < frameSize; y++) {
    for (let x = 0; x < frameSize; x++) {
      const dx = (x - half) / half;
      const qy = -(y - half) / half;
      const d2 = dx * dx + qy * qy;
      const idx = (y * frameSize + x) * 4;

      if (d2 > 1) {
        pixels[idx + 3] = 0; // Outside sphere — transparent
        continue;
      }

      // Front-hemisphere surface Z
      const qz = Math.sqrt(1 - d2);

      // 3-D rotation (X-pitch then Y-yaw)
      const z1 = qz * cxx - qy * sx;
      const py = qy * cxx + qz * sx;
      const px = dx * cyy + z1 * sy;
      const pz = -dx * sy + z1 * cyy;

      // Spherical → UV texture coordinates
      const lon = Math.atan2(pz, px);
      const lat = Math.asin(clamp(py, -1, 1));
      const tx  = Math.min(mapW - 1, Math.floor(((lon + Math.PI) / (2 * Math.PI)) * mapW));
      const ty  = Math.min(mapH - 1, Math.floor(((Math.PI / 2 - lat) / Math.PI) * mapH));
      const src = (ty * mapW + tx) * 4;

      // Simple Lambertian shading: qz is 1 at centre (facing viewer) and 0
      // at the limb — produces the natural centre-bright / edge-dark look
      // without any directional artefacts that would distort the texture.
      const light = 0.48 + qz * 0.52;

      pixels[idx]     = map[src]     * light; // R
      pixels[idx + 1] = map[src + 1] * light; // G
      pixels[idx + 2] = map[src + 2] * light; // B
      pixels[idx + 3] = 255;                  // A (opaque)
    }
  }

  earthFrameCtx.putImageData(earthFrame, 0, 0);
  ctx.drawImage(earthFrameCtx.canvas, cx - radius, cy - radius, radius * 2, radius * 2);
}

// ----------------------------------------------------------------------------
// 5. Shooting-Star / Meteor Utilities
// ----------------------------------------------------------------------------
/** Spawns a new meteor at a random screen edge position. */
function spawnMeteor() {
  const angle = rand(-0.55, -0.15);          // Diagonal slash direction
  const speed = rand(7, 16);
  meteors.push({
    x    : rand(0, w * 0.8),
    y    : rand(0, h * 0.3),
    vx   : Math.cos(angle) * speed,
    vy   : Math.sin(angle + Math.PI * 0.5) * speed,
    life : 1.0,
    decay: rand(0.008, 0.022),
    len  : rand(60, 180),
    w    : rand(0.8, 2.0)
  });
}

/** Updates all live meteors and draws them onto the canvas. */
function drawMeteors() {
  // Spawn if under cap and randomly
  if (meteors.length < METEOR_MAX && Math.random() < 0.004) spawnMeteor();

  meteors = meteors.filter((m) => m.life > 0);

  meteors.forEach((m) => {
    const tailX = m.x - m.vx * (m.len / m.speed || 4);
    const tailY = m.y - m.vy * (m.len / m.speed || 4);

    const grad = ctx.createLinearGradient(tailX, tailY, m.x, m.y);
    grad.addColorStop(0, `rgba(200, 230, 255, 0)`);
    grad.addColorStop(0.7, `rgba(210, 240, 255, ${m.life * 0.35})`);
    grad.addColorStop(1,   `rgba(255, 255, 255, ${m.life * 0.9})`);

    ctx.save();
    ctx.strokeStyle = grad;
    ctx.lineWidth   = m.w;
    ctx.lineCap     = 'round';
    ctx.beginPath();
    ctx.moveTo(tailX, tailY);
    ctx.lineTo(m.x,   m.y);
    ctx.stroke();
    ctx.restore();

    m.x    += m.vx;
    m.y    += m.vy;
    m.life -= m.decay;
  });
}

// ----------------------------------------------------------------------------
// 6. Orbiting Satellite
// ----------------------------------------------------------------------------
/**
 * Advances the satellite along its elliptical orbit and draws it with a
 * glowing comet tail.
 * @param {number} now - Performance timestamp (ms), used for pulsing.
 */
function drawSatellite(now) {
  const orbitA = radius * 1.48;   // Semi-major axis
  const orbitB = radius * 1.14;   // Semi-minor axis
  const tilt   = -0.38;           // Orbit tilt (radians)

  // Advance orbital position
  satellite.angle = (satellite.angle + 0.005) % (Math.PI * 2);

  // Raw elliptical coordinates
  const ex = orbitA * Math.cos(satellite.angle);
  const ey = orbitB * Math.sin(satellite.angle);

  // Apply tilt rotation
  const sx = cx + ex * Math.cos(tilt) - ey * Math.sin(tilt);
  const sy = cy + ex * Math.sin(tilt) + ey * Math.cos(tilt);

  // Record trail position
  satellite.trail.push({ x: sx, y: sy });
  if (satellite.trail.length > satellite.TRAIL) satellite.trail.shift();

  // Draw comet tail
  if (satellite.trail.length > 2) {
    for (let i = 1; i < satellite.trail.length; i++) {
      const t  = i / satellite.trail.length;
      const p0 = satellite.trail[i - 1];
      const p1 = satellite.trail[i];
      ctx.save();
      ctx.strokeStyle = `rgba(150, 230, 255, ${t * 0.45})`;
      ctx.lineWidth   = t * 1.8;
      ctx.beginPath();
      ctx.moveTo(p0.x, p0.y);
      ctx.lineTo(p1.x, p1.y);
      ctx.stroke();
      ctx.restore();
    }
  }

  // Draw satellite body dot
  const pulse = 0.7 + 0.3 * Math.sin(now * 0.003);
  const dotR  = 2.5 * pulse;

  const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, dotR * 5);
  glow.addColorStop(0,   `rgba(180, 240, 255, ${0.9 * pulse})`);
  glow.addColorStop(0.4, `rgba(100, 200, 255, ${0.4 * pulse})`);
  glow.addColorStop(1,   'rgba(40, 100, 200, 0)');

  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(sx, sy, dotR * 5, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = '#d8f5ff';
  ctx.beginPath();
  ctx.arc(sx, sy, dotR, 0, Math.PI * 2);
  ctx.fill();
}

// ----------------------------------------------------------------------------
// 7. Canvas Resizing & Environment Initialization
// ----------------------------------------------------------------------------
/**
 * Sets up canvas resolution, responsive scale, multi-tier starfield,
 * and offscreen projection buffers.
 */
function setup() {
  dpr = Math.min(window.devicePixelRatio || 1, 2);
  w   = window.innerWidth;
  h   = window.innerHeight;

  canvas.width  = w * dpr;
  canvas.height = h * dpr;
  canvas.style.width  = `${w}px`;
  canvas.style.height = `${h}px`;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  cx     = w / 2;
  cy     = h / 2 - Math.min(25, h * 0.025);
  radius = Math.min(w, h) * (w < 600 ? 0.275 : 0.31);

  // --- Near (large) stars — fewer, bigger, slower parallax ---
  const nearCount = Math.max(40, Math.floor((w * h) / 35000));
  starsNear = Array.from({ length: nearCount }, () => ({
    x : Math.random() * w,
    y : Math.random() * h,
    r : rand(1.0, 2.4),
    a : rand(0.35, 0.85),
    // Twinkle phase (individual)
    phase : rand(0, Math.PI * 2),
    speed : rand(0.5, 1.4)
  }));

  // --- Far (tiny) stars — more, smaller ---
  const farCount = Math.max(120, Math.floor((w * h) / 6000));
  starsFar = Array.from({ length: farCount }, () => ({
    x : Math.random() * w,
    y : Math.random() * h,
    r : rand(0.15, 0.9),
    a : rand(0.08, 0.45)
  }));

  // Offscreen projection buffer
  frameSize = Math.max(220, Math.round(radius * 2));
  const frameCanvas = document.createElement('canvas');
  frameCanvas.width  = frameSize;
  frameCanvas.height = frameSize;
  earthFrameCtx = frameCanvas.getContext('2d');
  earthFrame    = earthFrameCtx.createImageData(frameSize, frameSize);

  if (earthTexture.complete) makeEarthMap();
}

// ----------------------------------------------------------------------------
// 8. Main Render Loop
// ----------------------------------------------------------------------------
/**
 * Per-frame render: deep space background, multi-tier nebula, starfield,
 * meteors, atmosphere halo, city-light limb glow, globe projection,
 * specular rim highlight, satellite orbit.
 */
function draw(now) {
  ctx.clearRect(0, 0, w, h);

  // ── A. Deep Space Background ─────────────────────────────────────────────
  // Three-stop radial gradient going from deep indigo-navy centre to pure black
  const bg = ctx.createRadialGradient(cx, cy - h * 0.1, 0, cx, cy, Math.max(w, h) * 0.85);
  bg.addColorStop(0,    '#0c1428');
  bg.addColorStop(0.35, '#060c1f');
  bg.addColorStop(0.7,  '#03060f');
  bg.addColorStop(1,    '#010204');
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, w, h);

  // ── B. Nebula Clouds (three soft colour patches) ─────────────────────────
  const nebulaData = [
    { x: cx * 0.25, y: cy * 0.4,  rx: w * 0.28, ry: h * 0.22, c1: 'rgba(60,20,120,0.07)',  c2: 'rgba(40,10,80,0)' },
    { x: cx * 1.75, y: cy * 0.6,  rx: w * 0.22, ry: h * 0.18, c1: 'rgba(10,40,120,0.08)',  c2: 'rgba(5,20,60,0)'  },
    { x: cx * 1.4,  y: cy * 1.6,  rx: w * 0.3,  ry: h * 0.2,  c1: 'rgba(0,60,100,0.06)',   c2: 'rgba(0,30,50,0)'  },
  ];
  nebulaData.forEach((n) => {
    ctx.save();
    ctx.scale(1, n.ry / n.rx);
    const ng = ctx.createRadialGradient(n.x, n.y * (n.rx / n.ry), 0, n.x, n.y * (n.rx / n.ry), n.rx);
    ng.addColorStop(0, n.c1);
    ng.addColorStop(1, n.c2);
    ctx.fillStyle = ng;
    ctx.beginPath();
    ctx.arc(n.x, n.y * (n.rx / n.ry), n.rx, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  });

  // ── C. Far (tiny) Starfield ───────────────────────────────────────────────
  starsFar.forEach((s) => {
    ctx.fillStyle = `rgba(180, 210, 255, ${s.a})`;
    ctx.fillRect(s.x, s.y, s.r, s.r);
  });

  // ── D. Near (large, twinkling) Starfield ─────────────────────────────────
  starsNear.forEach((s) => {
    const tw = s.a * (0.65 + 0.35 * Math.sin(now * 0.001 * s.speed + s.phase));
    // Draw a cross-shaped sparkle for large stars
    if (s.r > 1.6) {
      ctx.save();
      ctx.strokeStyle = `rgba(200, 230, 255, ${tw * 0.5})`;
      ctx.lineWidth   = 0.6;
      const arm = s.r * 3.5;
      ctx.beginPath();
      ctx.moveTo(s.x - arm, s.y); ctx.lineTo(s.x + arm, s.y);
      ctx.moveTo(s.x, s.y - arm); ctx.lineTo(s.x, s.y + arm);
      ctx.stroke();
      ctx.restore();
    }
    ctx.fillStyle = `rgba(220, 235, 255, ${tw})`;
    ctx.beginPath();
    ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
    ctx.fill();
  });

  // ── E. Meteors / Shooting Stars ───────────────────────────────────────────
  drawMeteors();

  // ── F. Atmospheric Outer Halo (multi-stop, wider than v1) ─────────────────
  const haloR = radius * 2.1;
  const halo  = ctx.createRadialGradient(cx, cy, radius * 0.78, cx, cy, haloR);
  halo.addColorStop(0,    'rgba(30,  160, 240,  0.14)');
  halo.addColorStop(0.18, 'rgba(20,  120, 210,  0.09)');
  halo.addColorStop(0.42, 'rgba(10,   70, 180,  0.05)');
  halo.addColorStop(0.65, 'rgba(5,    30, 100,  0.025)');
  halo.addColorStop(1,    'rgba(0,     0,   0,  0)');
  ctx.fillStyle = halo;
  ctx.beginPath();
  ctx.arc(cx, cy, haloR, 0, Math.PI * 2);
  ctx.fill();

  // ── G. City-Light Glow (orange tint bleeding just outside the dark limb) ──
  const cityR = radius * 1.06;
  const cityG = ctx.createRadialGradient(cx, cy, radius * 0.95, cx, cy, cityR);
  cityG.addColorStop(0, 'rgba(255, 160, 60, 0.04)');
  cityG.addColorStop(1, 'rgba(255, 100, 20, 0)');
  ctx.fillStyle = cityG;
  ctx.beginPath();
  ctx.arc(cx, cy, cityR, 0, Math.PI * 2);
  ctx.fill();

  // ── H. Globe Projection (clipped circle) ─────────────────────────────────
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.clip();
  renderEarthMap();
  ctx.restore();

  // ── I. Specular Limb Highlight (blue-white crescent on top-left) ──────────
  const rim = ctx.createRadialGradient(
    cx - radius * 0.28, cy - radius * 0.32, radius * 0.62,
    cx, cy, radius * 1.03
  );
  rim.addColorStop(0.58, 'rgba(130, 245, 255, 0)');
  rim.addColorStop(0.82, 'rgba(100, 200, 255, 0.15)');
  rim.addColorStop(0.93, 'rgba(180, 245, 255, 0.48)');
  rim.addColorStop(1,    'rgba(220, 255, 255, 0.12)');
  ctx.strokeStyle = rim;
  ctx.lineWidth   = 2.0;
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.stroke();

  // ── J. Inner atmosphere fringe (thin cyan ring just inside limb) ──────────
  const innerRim = ctx.createRadialGradient(cx, cy, radius * 0.91, cx, cy, radius);
  innerRim.addColorStop(0,   'rgba(20, 160, 255, 0)');
  innerRim.addColorStop(0.7, 'rgba(40, 180, 255, 0.06)');
  innerRim.addColorStop(1,   'rgba(80, 210, 255, 0.18)');
  ctx.fillStyle = innerRim;
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.clip();
  ctx.fillRect(cx - radius, cy - radius, radius * 2, radius * 2);
  ctx.restore();

  // ── K. Orbiting Satellite ─────────────────────────────────────────────────
  drawSatellite(now);

  // ── L. Inertia / Rotation Update ─────────────────────────────────────────
  rotation.y += (-target.x * 0.95 - rotation.y) * 0.025;
  rotation.x += ( target.y * 0.55 - rotation.x) * 0.025;

  requestAnimationFrame(draw);
}

// ----------------------------------------------------------------------------
// 9. Input Event Handlers (Pointer / Touch)
// ----------------------------------------------------------------------------
/**
 * Normalises cursor / touch position relative to the screen centre
 * to drive globe rotation angles with proportional limits.
 *
 * @param {number} x - Client X coordinate.
 * @param {number} y - Client Y coordinate.
 */
function move(x, y) {
  target.x = -2.9 + clamp((x / w - 0.5) * 1.9, -0.95, 0.95);
  target.y = clamp((y / h - 0.5) * 1.5, -0.75, 0.75);
}

window.addEventListener('pointermove', (e) => { move(e.clientX, e.clientY); });

window.addEventListener('touchmove', (e) => {
  const t = e.touches[0];
  if (t) move(t.clientX, t.clientY);
}, { passive: true });

// ----------------------------------------------------------------------------
// 10. Lifecycle & Bootstrapping
// ----------------------------------------------------------------------------
earthTexture.onload = makeEarthMap;
earthTexture.src    = 'earth-texture.jpg';

window.addEventListener('resize', setup);

window.addEventListener('pageshow', (event) => {
  if (event.persisted) setup();
});

setup();
requestAnimationFrame(draw);
