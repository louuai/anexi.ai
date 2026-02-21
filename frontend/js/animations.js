// ========================================
// ANEXI.AI - ORBIT INTERACTIONS
// ========================================

const topbar = document.querySelector('.topbar');
if (topbar) {
    const syncTopbar = () => {
        if (window.pageYOffset > 50) {
            topbar.classList.add('is-scrolled');
        } else {
            topbar.classList.remove('is-scrolled');
        }
    };
    syncTopbar();
    window.addEventListener('scroll', syncTopbar, { passive: true });
}

Array.from(document.querySelectorAll('a[href^="#"]')).forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const href = anchor.getAttribute('href');
        const target = href ? document.querySelector(href) : null;
        if (target) {
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    });
});

const parallaxItems = document.querySelectorAll('[data-parallax]');
const runParallax = () => {
    const scrollY = window.scrollY || window.pageYOffset;
    parallaxItems.forEach((item) => {
        const speed = Number(item.dataset.parallax || '0');
        item.style.transform = `translate3d(0, ${scrollY * speed * -0.18}px, 0)`;
    });
};
if (parallaxItems.length) {
    runParallax();
    window.addEventListener('scroll', runParallax, { passive: true });
}

const revealItems = document.querySelectorAll('.reveal-item');
if (revealItems.length) {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (!entry.isIntersecting) {
                return;
            }
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
        });
    }, {
        threshold: 0.16,
        rootMargin: '0px 0px -70px 0px'
    });

    revealItems.forEach((item) => observer.observe(item));
}

const robotStage = document.getElementById('robotStage');
const robotModel = document.getElementById('robotModel');
const steps = document.querySelectorAll('.step');

if (robotStage && robotModel) {
    robotStage.addEventListener('mousemove', (e) => {
        const rect = robotStage.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const nx = (x / rect.width) - 0.5;
        const ny = (y / rect.height) - 0.5;

        const orbitX = 35 + nx * 18;
        const orbitY = 74 - ny * 12;
        robotModel.setAttribute('camera-orbit', `${orbitX.toFixed(2)}deg ${orbitY.toFixed(2)}deg 2.4m`);
    });

    robotStage.addEventListener('mouseleave', () => {
        robotModel.setAttribute('camera-orbit', '35deg 74deg 2.4m');
    });

    const updateRobotByScroll = () => {
        const scrollY = window.scrollY || window.pageYOffset;
        let activeScene = 1;
        let activeOrbit = 35;

        steps.forEach((step, index) => {
            const rect = step.getBoundingClientRect();
            const center = rect.top + rect.height * 0.5;
            const focus = center > window.innerHeight * 0.22 && center < window.innerHeight * 0.78;
            if (focus) {
                activeScene = Math.min(index + 1, 3);
                activeOrbit = Number(step.getAttribute('data-orbit') || '35');
            }
        });

        document.body.setAttribute('data-scene', String(activeScene));

        const wobble = Math.sin(scrollY * 0.0028) * 3.5;
        const elevation = 74 + Math.cos(scrollY * 0.0022) * 2.5;
        robotModel.setAttribute('camera-orbit', `${(activeOrbit + wobble).toFixed(2)}deg ${elevation.toFixed(2)}deg 2.4m`);
    };

    updateRobotByScroll();
    window.addEventListener('scroll', updateRobotByScroll, { passive: true });
}

console.log('Anexi orbit landing loaded');