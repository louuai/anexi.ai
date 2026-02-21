/* ═══════════════════════════════════════════════════════════════════
   ANEXI.AI — ULTIMATE ANIMATIONS
   Parallax, Scroll reveals, Counter animations, Navbar behavior
   ═══════════════════════════════════════════════════════════════════ */

(function() {
  'use strict';

  // ───────────────────── NAVBAR SCROLL ─────────────────────
  const navbar = document.getElementById('navbar');
  let lastScrollY = window.scrollY;

  function handleNavbarScroll() {
    const currentScrollY = window.scrollY;
    
    if (currentScrollY > 100) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    
    lastScrollY = currentScrollY;
  }

  window.addEventListener('scroll', handleNavbarScroll, { passive: true });
  handleNavbarScroll();

  // ───────────────────── PARALLAX EFFECT ─────────────────────
  const parallaxElements = document.querySelectorAll('[data-parallax], [data-scroll-speed]');

  function handleParallax() {
    const scrolled = window.scrollY;
    
    parallaxElements.forEach(el => {
      const speed = el.dataset.parallax || el.dataset.scrollSpeed || 0.5;
      const yPos = -(scrolled * parseFloat(speed));
      el.style.transform = `translateY(${yPos}px)`;
    });
  }

  if (parallaxElements.length > 0) {
    window.addEventListener('scroll', handleParallax, { passive: true });
  }

  // ───────────────────── SCROLL REVEAL ─────────────────────
  const revealElements = document.querySelectorAll('[data-reveal]');
  const maskRevealElements = document.querySelectorAll('[data-mask-reveal]');

  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('revealed');
        revealObserver.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.1,
    rootMargin: '0px 0px -100px 0px'
  });

  revealElements.forEach(el => revealObserver.observe(el));

  if ('IntersectionObserver' in window) {
    const maskRevealObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
          maskRevealObserver.unobserve(entry.target);
        }
      });
    }, {
      threshold: 0.2,
      rootMargin: '0px 0px -80px 0px'
    });

    maskRevealElements.forEach(el => {
      el.classList.add('mask-ready');
      maskRevealObserver.observe(el);
    });
  } else {
    maskRevealElements.forEach(el => el.classList.add('is-revealed'));
  }

  // ───────────────────── COUNTER ANIMATION ─────────────────────
  const counterElements = document.querySelectorAll('[data-count]');

  function animateCounter(element) {
    const target = parseInt(element.dataset.count);
    const duration = 2000; // 2 seconds
    const start = 0;
    const increment = target / (duration / 16); // 60fps
    let current = start;

    const updateCounter = () => {
      current += increment;
      if (current < target) {
        element.textContent = Math.floor(current);
        requestAnimationFrame(updateCounter);
      } else {
        element.textContent = target;
      }
    };

    updateCounter();
  }

  const counterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  counterElements.forEach(el => counterObserver.observe(el));

  // ───────────────────── HAMBURGER MENU ─────────────────────
  const hamburger = document.getElementById('hamburger');
  const navLinks = document.querySelector('.nav-links');

  if (hamburger) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      if (navLinks) {
        navLinks.classList.toggle('mobile-open');
      }
    });
  }

  // ───────────────────── SMOOTH SCROLL ─────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const href = this.getAttribute('href');
      if (href === '#') return;
      
      const target = document.querySelector(href);
      if (target) {
        e.preventDefault();
        const offsetTop = target.offsetTop - 80; // navbar height
        window.scrollTo({
          top: offsetTop,
          behavior: 'smooth'
        });
      }
    });
  });

  // ───────────────────── 3D ROBOT INTERACTION ─────────────────────
  const robotModel = document.getElementById('anexiRobot');

  if (robotModel) {
    // Adjust robot rotation based on mouse position
    let mouseX = 0;
    let mouseY = 0;

    document.addEventListener('mousemove', (e) => {
      mouseX = (e.clientX / window.innerWidth) * 2 - 1;
      mouseY = (e.clientY / window.innerHeight) * 2 - 1;
      
      // Update camera orbit based on mouse
      const baseOrbitX = 25;
      const baseOrbitY = 75;
      const offsetX = mouseX * 15; // max 15deg offset
      const offsetY = mouseY * 10; // max 10deg offset
      
      robotModel.cameraOrbit = `${baseOrbitX + offsetX}deg ${baseOrbitY - offsetY}deg 2.2m`;
    });

    // Change robot animation based on scroll
    let lastScrollForRobot = 0;
    window.addEventListener('scroll', () => {
      const scrollY = window.scrollY;
      const scrollSpeed = Math.abs(scrollY - lastScrollForRobot);
      
      if (scrollSpeed > 5) {
        // Increase rotation speed when scrolling
        robotModel.autoRotate = true;
        robotModel.rotationPerSecond = '40deg';
      } else {
        // Normal rotation
        robotModel.rotationPerSecond = '20deg';
      }
      
      lastScrollForRobot = scrollY;
    }, { passive: true });
  }

  // ───────────────────── ORBIT RINGS PARALLAX ─────────────────────
  const orbitRings = document.querySelectorAll('.orbit-ring');

  function updateOrbitRings() {
    const scrolled = window.scrollY;
    
    orbitRings.forEach((ring, index) => {
      const speed = 0.03 * (index + 1);
      const rotation = scrolled * speed;
      ring.style.transform = `translate(-50%, -50%) rotate(${rotation}deg)`;
    });
  }

  window.addEventListener('scroll', updateOrbitRings, { passive: true });

  // ───────────────────── TRUST METER ANIMATION ─────────────────────
  const trustMeterObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const bar = entry.target.querySelector('.meter-bar');
        if (bar) {
          bar.style.width = bar.style.getPropertyValue('--score');
        }
        trustMeterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  const trustMeters = document.querySelectorAll('.trust-meter');
  trustMeters.forEach(meter => trustMeterObserver.observe(meter));

  // ───────────────────── BUTTON RIPPLE EFFECT ─────────────────────
  const rippleButtons = document.querySelectorAll('.btn-primary, .btn-hero-primary, .btn-cta-primary');

  rippleButtons.forEach(button => {
    button.addEventListener('click', function(e) {
      const rect = this.getBoundingClientRect();
      const ripple = document.createElement('span');
      const size = Math.max(rect.width, rect.height);
      
      ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${e.clientX - rect.left - size/2}px;
        top: ${e.clientY - rect.top - size/2}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: rippleEffect 0.6s ease-out;
        pointer-events: none;
      `;
      
      // Ensure button has position relative
      if (getComputedStyle(this).position === 'static') {
        this.style.position = 'relative';
      }
      this.style.overflow = 'hidden';
      
      this.appendChild(ripple);
      
      setTimeout(() => ripple.remove(), 600);
    });
  });

  // Add ripple animation style
  const style = document.createElement('style');
  style.textContent = `
    @keyframes rippleEffect {
      to {
        transform: scale(4);
        opacity: 0;
      }
    }
  `;
  document.head.appendChild(style);

  // ───────────────────── FLOATING UI CARDS ─────────────────────
  const floatingCards = document.querySelectorAll('.float-ui');

  function animateFloatingCards() {
    const scrolled = window.scrollY;
    
    floatingCards.forEach((card, index) => {
      const speed = 0.05 + (index * 0.02);
      const yOffset = Math.sin((scrolled + index * 100) * 0.002) * 10;
      card.style.transform = `translateY(${yOffset}px)`;
    });
  }

  if (floatingCards.length > 0) {
    window.addEventListener('scroll', animateFloatingCards, { passive: true });
  }

  // ───────────────────── INITIALIZE ─────────────────────
  console.log('✅ Anexi.ai Ultimate Animations initialized');

  // Initial calls
  handleNavbarScroll();
  if (parallaxElements.length > 0) handleParallax();
  updateOrbitRings();

})();
