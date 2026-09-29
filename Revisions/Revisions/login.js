/**
 * ============================================================================
 * MARITIME SURVEILLANCE SYSTEM — Login / Sign-Up Interface Script
 * ============================================================================
 * Handles tactical radar canvas simulation, Login / Sign-Up tab switching,
 * password visibility toggling, form validation, and portal redirection.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --------------------------------------------------------------------------
  // 1. DOM Element References
  // --------------------------------------------------------------------------
  const radarCanvas       = document.getElementById('radar-canvas');
  const modeTabs          = document.querySelectorAll('.role-tab-btn');

  // Login form elements
  const loginForm         = document.getElementById('login-form');
  const emailInput        = document.getElementById('email-input');
  const passwordInput     = document.getElementById('password-input');
  const passwordToggleBtn = document.getElementById('password-toggle-btn');
  const loginBtn          = document.getElementById('login-btn');
  const authFeedback      = document.getElementById('auth-feedback');
  const demoEmployeeBtn   = document.getElementById('demo-employee-btn');

  // Sign-up form elements
  const signupForm            = document.getElementById('signup-form');
  const signupName            = document.getElementById('signup-name');
  const signupEmail           = document.getElementById('signup-email');
  const signupDesignation     = document.getElementById('signup-designation');
  const signupPassword        = document.getElementById('signup-password');
  const signupConfirmPassword = document.getElementById('signup-confirm-password');
  const signupPasswordToggle  = document.getElementById('signup-password-toggle');
  const signupBtn             = document.getElementById('signup-btn');
  const signupFeedback        = document.getElementById('signup-feedback');

  // --------------------------------------------------------------------------
  // 2. Tactical Naval Radar Canvas Simulation
  // --------------------------------------------------------------------------
  if (radarCanvas) {
    const ctx = radarCanvas.getContext('2d');
    let radarWidth, radarHeight, radarDpr;
    let radarRadius, centerX, centerY;
    let sweepAngle = 0.8; // Initial sweep angle (radians)

    // Ship blips on the radar
    const radarBlips = [
      { rRatio: 0.62, angle: -0.72, heading: 0.95, scale: 1.05, lastEcho: 0 },
      { rRatio: 0.48, angle: -0.08, heading: 1.15, scale: 0.95, lastEcho: 0 },
      { rRatio: 0.54, angle:  0.52, heading: 0.90, scale: 1.1,  lastEcho: 0 },
      { rRatio: 0.74, angle:  0.88, heading: 0.85, scale: 1.0,  lastEcho: 0 }
    ];

    /**
     * Resizes radar canvas accounting for high-DPI retina displays.
     */
    function resizeRadar() {
      const rect = radarCanvas.getBoundingClientRect();
      radarDpr    = Math.min(window.devicePixelRatio || 1, 2);
      radarWidth  = rect.width  || (window.innerWidth * 0.5);
      radarHeight = rect.height || window.innerHeight;

      radarCanvas.width  = radarWidth  * radarDpr;
      radarCanvas.height = radarHeight * radarDpr;
      ctx.setTransform(radarDpr, 0, 0, radarDpr, 0, 0);

      centerX     = Math.max(34, radarWidth * 0.055);
      centerY     = radarHeight * 0.38;
      radarRadius = Math.max(radarWidth * 0.92, 450);
    }

    /**
     * Draws a tactical ship silhouette marker at specified coordinates.
     */
    function drawVesselIcon(x, y, heading, scale, alpha, echoGlow) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(heading);
      ctx.scale(scale, scale);

      // Echo flare when sweep beam passes over
      if (echoGlow > 0.05) {
        const glowGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, 24);
        glowGrad.addColorStop(0, `rgba(130, 215, 255, ${echoGlow * 0.6})`);
        glowGrad.addColorStop(1, 'rgba(80, 170, 240, 0)');
        ctx.fillStyle = glowGrad;
        ctx.beginPath();
        ctx.arc(0, 0, 24, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.fillStyle   = `rgba(107, 182, 240, ${alpha})`;
      ctx.strokeStyle = `rgba(175, 225, 255, ${alpha * 0.9})`;
      ctx.lineWidth   = 1;

      ctx.beginPath();
      ctx.moveTo( 0, -9);
      ctx.lineTo( 4, -4);
      ctx.lineTo( 4,  7);
      ctx.lineTo(-4,  7);
      ctx.lineTo(-4, -4);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();

      // Superstructure bridge mark
      ctx.fillStyle = `rgba(220, 240, 255, ${alpha})`;
      ctx.fillRect(-2, -1, 4, 3);

      ctx.restore();
    }

    /**
     * Draws radar range rings, crosshairs, rotating sweep, and vessels.
     */
    function renderRadar() {
      ctx.clearRect(0, 0, radarWidth, radarHeight);

      // 1. Concentric Range Rings
      const ringCount = 5;
      for (let i = 1; i <= ringCount; i++) {
        const r = (radarRadius / ringCount) * i;
        ctx.strokeStyle = 'rgba(45, 95, 150, 0.22)';
        ctx.lineWidth   = 1;
        ctx.beginPath();
        ctx.arc(centerX, centerY, r, 0, Math.PI * 2);
        ctx.stroke();
      }

      // 2. Radial Crosshair Lines
      ctx.strokeStyle = 'rgba(45, 95, 150, 0.18)';
      ctx.lineWidth   = 1;

      ctx.beginPath();
      ctx.moveTo(centerX - radarRadius, centerY);
      ctx.lineTo(centerX + radarRadius, centerY);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(centerX, centerY - radarRadius);
      ctx.lineTo(centerX, centerY + radarRadius);
      ctx.stroke();

      [-0.52, -0.26, 0.26, 0.52].forEach((angleOffset) => {
        ctx.beginPath();
        ctx.moveTo(
          centerX + Math.cos(angleOffset) * 20,
          centerY + Math.sin(angleOffset) * 20
        );
        ctx.lineTo(
          centerX + Math.cos(angleOffset) * radarRadius,
          centerY + Math.sin(angleOffset) * radarRadius
        );
        ctx.stroke();
      });

      // 3. Rotating Radar Sweep Beam (Wedge Gradient)
      const sweepSpread = 0.52;
      const segments   = 24;

      for (let s = 0; s < segments; s++) {
        const segStart = sweepAngle - (sweepSpread * (s + 1)) / segments;
        const segEnd   = sweepAngle - (sweepSpread * s) / segments;
        const fade     = Math.pow(1 - s / segments, 1.6);

        ctx.fillStyle = `rgba(56, 150, 235, ${fade * 0.18})`;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radarRadius, segStart, segEnd, false);
        ctx.closePath();
        ctx.fill();
      }

      // Bright leading edge line
      ctx.strokeStyle = 'rgba(120, 205, 255, 0.45)';
      ctx.lineWidth   = 1.5;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + Math.cos(sweepAngle) * radarRadius,
        centerY + Math.sin(sweepAngle) * radarRadius
      );
      ctx.stroke();

      // 4. Draw Radar Vessel Blips
      radarBlips.forEach((blip) => {
        const bx = centerX + Math.cos(blip.angle) * (blip.rRatio * radarRadius);
        const by = centerY + Math.sin(blip.angle) * (blip.rRatio * radarRadius);

        let diff = (sweepAngle - blip.angle) % (Math.PI * 2);
        if (diff < 0) diff += Math.PI * 2;

        if (diff < 0.08) {
          blip.lastEcho = 1.0;
        } else {
          blip.lastEcho = Math.max(0, blip.lastEcho - 0.008);
        }

        const alpha = 0.4 + blip.lastEcho * 0.6;
        drawVesselIcon(bx, by, blip.heading, blip.scale, alpha, blip.lastEcho);
      });

      // 5. Center Pivot Reticle
      ctx.fillStyle = '#79c8ff';
      ctx.beginPath();
      ctx.arc(centerX, centerY, 3, 0, Math.PI * 2);
      ctx.fill();

      sweepAngle = (sweepAngle + 0.012) % (Math.PI * 2);

      requestAnimationFrame(renderRadar);
    }

    window.addEventListener('resize', resizeRadar);
    window.addEventListener('pageshow', (event) => {
      if (event.persisted) resizeRadar();
    });
    resizeRadar();
    requestAnimationFrame(renderRadar);
  }

  // --------------------------------------------------------------------------
  // 3. Login / Sign-Up Tab Switcher
  // --------------------------------------------------------------------------
  let currentMode = 'login'; // 'login' | 'signup'

  modeTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      const mode = tab.dataset.mode;
      if (mode === currentMode) return;
      currentMode = mode;

      // Update tab active state
      modeTabs.forEach((t) => {
        const isActive = t.dataset.mode === mode;
        t.classList.toggle('active', isActive);
        t.setAttribute('aria-selected', isActive ? 'true' : 'false');
      });

      // Show / hide forms
      if (mode === 'login') {
        loginForm.style.display  = '';
        signupForm.style.display = 'none';
      } else {
        loginForm.style.display  = 'none';
        signupForm.style.display = '';
      }

      // Clear all feedback
      if (authFeedback)   { authFeedback.textContent  = ''; authFeedback.className  = 'auth-feedback'; }
      if (signupFeedback) { signupFeedback.textContent = ''; signupFeedback.className = 'auth-feedback'; }
    });
  });

  // --------------------------------------------------------------------------
  // 4. Demo Employee Quick-Fill
  // --------------------------------------------------------------------------
  if (demoEmployeeBtn) {
    demoEmployeeBtn.addEventListener('click', () => {
      if (emailInput)    emailInput.value    = 'officer.patil@maritime.gov.in';
      if (passwordInput) passwordInput.value = 'Surveillance@2026';
      showFeedback(authFeedback, 'Demo Employee credentials populated. Authenticating...', 'info');
      setTimeout(() => {
        if (loginForm) loginForm.dispatchEvent(new Event('submit'));
      }, 150);
    });
  }

  // --------------------------------------------------------------------------
  // 5. Password Show / Hide Toggle (Login)
  // --------------------------------------------------------------------------
  if (passwordToggleBtn && passwordInput) {
    passwordToggleBtn.addEventListener('click', () => {
      togglePasswordVisibility(passwordInput, passwordToggleBtn);
    });
  }

  // --------------------------------------------------------------------------
  // 6. Password Show / Hide Toggle (Sign-Up)
  // --------------------------------------------------------------------------
  if (signupPasswordToggle && signupPassword) {
    signupPasswordToggle.addEventListener('click', () => {
      togglePasswordVisibility(signupPassword, signupPasswordToggle);
    });
  }

  /**
   * Toggles an input between password and text types and swaps the eye icon.
   * @param {HTMLInputElement} input
   * @param {HTMLButtonElement} btn
   */
  function togglePasswordVisibility(input, btn) {
    const isPassword = input.type === 'password';
    input.type = isPassword ? 'text' : 'password';
    btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');

    btn.innerHTML = isPassword
      ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
           <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
           <line x1="1" y1="1" x2="23" y2="23"></line>
         </svg>`
      : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
           <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
           <circle cx="12" cy="12" r="3"></circle>
         </svg>`;
  }

  // --------------------------------------------------------------------------
  // 7. Login Form Submission Handler
  // --------------------------------------------------------------------------
  if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const email    = emailInput    ? emailInput.value.trim()    : '';
      const password = passwordInput ? passwordInput.value : '';

      if (!email) {
        showFeedback(authFeedback, 'Please enter your authorized email address.', 'error');
        if (emailInput) emailInput.focus();
        return;
      }
      if (!password) {
        showFeedback(authFeedback, 'Please enter your security access credentials.', 'error');
        if (passwordInput) passwordInput.focus();
        return;
      }

      loginBtn.disabled = true;
      loginBtn.classList.add('loading');
      loginBtn.querySelector('.btn-text').textContent = 'VERIFYING CREDENTIALS...';
      showFeedback(authFeedback, 'Authenticating clearance...', 'info');

      setTimeout(() => {
        loginBtn.classList.remove('loading');
        loginBtn.querySelector('.btn-text').textContent = 'ACCESS GRANTED';
        showFeedback(authFeedback, 'Clearance verified. Launching Maritime Search Console...', 'success');
        setTimeout(() => {
          window.location.href = 'employee.html';
        }, 800);
      }, 1100);
    });
  }

  // --------------------------------------------------------------------------
  // 8. Sign-Up Form Submission Handler
  // --------------------------------------------------------------------------
  if (signupForm) {
    signupForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const name         = signupName            ? signupName.value.trim()            : '';
      const email        = signupEmail           ? signupEmail.value.trim()           : '';
      const designation  = signupDesignation     ? signupDesignation.value.trim()     : '';
      const password     = signupPassword        ? signupPassword.value               : '';
      const confirmPass  = signupConfirmPassword ? signupConfirmPassword.value        : '';

      if (!name) {
        showFeedback(signupFeedback, 'Please enter your full name.', 'error');
        signupName.focus();
        return;
      }
      if (!email) {
        showFeedback(signupFeedback, 'Please enter a valid work email address.', 'error');
        signupEmail.focus();
        return;
      }
      if (!designation) {
        showFeedback(signupFeedback, 'Please enter your designation or organisation.', 'error');
        signupDesignation.focus();
        return;
      }
      if (password.length < 8) {
        showFeedback(signupFeedback, 'Password must be at least 8 characters.', 'error');
        signupPassword.focus();
        return;
      }
      if (password !== confirmPass) {
        showFeedback(signupFeedback, 'Passwords do not match. Please re-enter.', 'error');
        signupConfirmPassword.focus();
        return;
      }

      signupBtn.disabled = true;
      signupBtn.classList.add('loading');
      signupBtn.querySelector('.btn-text').textContent = 'SUBMITTING REQUEST...';
      showFeedback(signupFeedback, 'Sending access request to the system administrator...', 'info');

      setTimeout(() => {
        signupBtn.classList.remove('loading');
        signupBtn.querySelector('.btn-text').textContent = 'REQUEST SENT';
        showFeedback(
          signupFeedback,
          `✓ Access request submitted for ${email}. You will receive an email confirmation once your account is approved.`,
          'success'
        );
        // Reset form fields after success
        signupForm.reset();
        setTimeout(() => {
          signupBtn.disabled = false;
          signupBtn.querySelector('.btn-text').textContent = 'REQUEST ACCESS';
        }, 4000);
      }, 1400);
    });
  }

  // --------------------------------------------------------------------------
  // 9. Utility: Display Feedback Message
  // --------------------------------------------------------------------------
  /**
   * Displays a status, error, or success message in the given feedback element.
   * @param {HTMLElement} el - The feedback container.
   * @param {string} message - The text to display.
   * @param {'info'|'error'|'success'} type - Visual styling type.
   */
  function showFeedback(el, message, type) {
    if (!el) return;
    el.textContent = message;
    el.className   = `auth-feedback visible ${type}`;
  }
});
