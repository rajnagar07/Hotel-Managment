document.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('[data-password-toggle]').forEach((button) => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-target');
      const input = document.getElementById(targetId);
      if (!input) return;
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      button.textContent = isPassword ? 'Hide' : 'Show';
    });
  });

  setTimeout(() => {
    document.querySelectorAll('.alert').forEach((alert) => {
      alert.classList.remove('show');
      window.setTimeout(() => alert.remove(), 300);
    });
  }, 4500);

  document.querySelectorAll('[data-delete-url]').forEach((button) => {
    button.addEventListener('click', () => {
      const modalId = button.getAttribute('data-delete-modal');
      const itemName = button.getAttribute('data-item-name') || 'this item';
      const deleteUrl = button.getAttribute('data-delete-url');
      if (!modalId || !deleteUrl) return;
      const modal = document.getElementById(modalId);
      if (!modal) return;

      const form = modal.querySelector('form');
      const title = modal.querySelector('[data-delete-item-name]');
      if (form) form.action = deleteUrl;
      if (title) title.textContent = itemName;
    });
  });

  document.querySelectorAll('input[type="file"]').forEach((input) => {
    const listId = input.getAttribute('data-preview-target') || (input.id === 'hotel-images' ? 'hotel-image-list' : null);
    if (!listId) return;
    const list = document.getElementById(listId);
    if (!list) return;

    input.addEventListener('change', () => {
      const files = Array.from(input.files || []);
      if (!files.length) {
        list.textContent = '';
        return;
      }
      list.textContent = files.map((file) => file.name).join(', ');
    });
  });

  const contactModal = document.getElementById('hotelContactModal');
  if (contactModal && window.bootstrap) {
    const hotelNameEl = document.getElementById('contactModalHotelName');
    const hotelNameTextEl = document.getElementById('contactModalHotelNameText');
    const addressEl = document.getElementById('contactModalHotelAddress');
    const addressTextEl = document.getElementById('contactModalAddressText');
    const phoneTextEl = document.getElementById('contactModalPhoneText');
    const whatsappTextEl = document.getElementById('contactModalWhatsappText');
    const emailTextEl = document.getElementById('contactModalEmailText');
    const callBtn = document.getElementById('contactModalCallBtn');
    const whatsappBtn = document.getElementById('contactModalWhatsappBtn');
    const emailBtn = document.getElementById('contactModalEmailBtn');

    const normalizeDigits = (value) => (value || '').toString().replace(/\D+/g, '');

    contactModal.addEventListener('show.bs.modal', (event) => {
      const trigger = event.relatedTarget;
      if (!trigger) return;

      const hotelName = trigger.getAttribute('data-hotel-name') || 'Family Hotel';
      const phone = trigger.getAttribute('data-phone') || '+919630099023';
      const whatsapp = trigger.getAttribute('data-whatsapp') || phone;
      const email = trigger.getAttribute('data-email') || 'ujjainhotelbooking@gmail.com';
      const address = trigger.getAttribute('data-address') || 'Ujjain, Madhya Pradesh, India';

      const phoneDigits = normalizeDigits(phone);
      const whatsappDigits = normalizeDigits(whatsapp);

      if (hotelNameEl) hotelNameEl.textContent = hotelName;
      if (hotelNameTextEl) hotelNameTextEl.textContent = hotelName;
      if (addressEl) addressEl.textContent = address;
      if (addressTextEl) addressTextEl.textContent = address;
      if (phoneTextEl) phoneTextEl.textContent = phone;
      if (whatsappTextEl) whatsappTextEl.textContent = whatsapp;
      if (emailTextEl) emailTextEl.textContent = email;

      if (callBtn && phoneDigits) callBtn.setAttribute('href', `tel:+${phoneDigits}`);
      if (whatsappBtn && whatsappDigits) whatsappBtn.setAttribute('href', `https://wa.me/${whatsappDigits}`);
      if (emailBtn && email) emailBtn.setAttribute('href', `mailto:${email}?subject=${encodeURIComponent(`${hotelName} inquiry`)}`);
    });
  }

  // Enquiry form handling (AJAX)
  const enquiryForm = document.getElementById('enquiryForm');
  if (enquiryForm) {
    enquiryForm.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const nameInput = document.getElementById('enquiryName');
      const phoneInput = document.getElementById('enquiryPhone');
      const resultEl = document.getElementById('enquiryResult');

      // simple client-side validation
      let valid = true;
      if (!nameInput.value.trim()) {
        nameInput.classList.add('is-invalid');
        valid = false;
      } else {
        nameInput.classList.remove('is-invalid');
      }

      const digits = (phoneInput.value || '').replace(/\D+/g, '');
      if (digits.length < 7 || digits.length > 15) {
        phoneInput.classList.add('is-invalid');
        valid = false;
      } else {
        phoneInput.classList.remove('is-invalid');
      }

      if (!valid) return;

      const submitBtn = document.getElementById('enquirySubmit');
      const originalText = submitBtn.textContent;
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending...';

      try {
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        const resp = await fetch('/enquire', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}) },
          body: JSON.stringify({ name: nameInput.value.trim(), phone: phoneInput.value.trim() }),
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
          // show success and reset
          if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.className = 'alert alert-success';
            resultEl.textContent = data.message || 'Enquiry received.';
          }
          enquiryForm.reset();
          // close modal after short delay
          setTimeout(() => {
            const modalEl = document.getElementById('enquiryModal');
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
            if (resultEl) {
              resultEl.style.display = 'none';
              resultEl.textContent = '';
            }
          }, 1200);
        } else {
          const msg = (data && data.message) || 'Submission failed. Please try again later.';
          if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.className = 'alert alert-danger';
            resultEl.textContent = msg;
          }
        }
      } catch (err) {
        if (resultEl) {
          resultEl.style.display = 'block';
          resultEl.className = 'alert alert-danger';
          resultEl.textContent = 'Network error. Please try again.';
        }
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalText;
      }
    });
  }

  // Scroll-reveal animations
  const revealTargets = document.querySelectorAll('.reveal');
  const revealAll = () => revealTargets.forEach((el) => el.classList.add('visible'));
  if (revealTargets.length && 'IntersectionObserver' in window && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0, rootMargin: '0px 0px -10% 0px' });
    revealTargets.forEach((el) => revealObserver.observe(el));
    window.setTimeout(() => {
      revealAll();
      revealObserver.disconnect();
    }, 1500);
  } else {
    revealAll();
  }

  // Animated stat counters
  const counters = document.querySelectorAll('[data-count-to]');
  if (counters.length && 'IntersectionObserver' in window) {
    const counterObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.getAttribute('data-count-to'), 10) || 0;
        const suffix = el.getAttribute('data-count-suffix') || '';
        const duration = 1400;
        const start = performance.now();
        const step = (now) => {
          const progress = Math.min((now - start) / duration, 1);
          const eased = 1 - Math.pow(1 - progress, 3);
          el.textContent = Math.round(eased * target) + suffix;
          if (progress < 1) requestAnimationFrame(step);
        };
        requestAnimationFrame(step);
        counterObserver.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach((el) => counterObserver.observe(el));
  }

  // Gallery lightbox
  const lightbox = document.getElementById('lightboxOverlay');
  const lightboxImg = document.getElementById('lightboxImage');
  const lightboxClose = document.getElementById('lightboxClose');
  const lightboxPrev = document.getElementById('lightboxPrev');
  const lightboxNext = document.getElementById('lightboxNext');
  const lightboxCounter = document.getElementById('lightboxCounter');
  if (lightbox && lightboxImg) {
    const galleryImages = Array.from(document.querySelectorAll('.gallery-img'));
    let currentIndex = 0;
    let previousFocus = null;
    let touchStartX = 0;

    const showImage = (index) => {
      if (!galleryImages.length) return;
      currentIndex = (index + galleryImages.length) % galleryImages.length;
      const image = galleryImages[currentIndex];
      lightboxImg.setAttribute('src', image.currentSrc || image.src);
      lightboxImg.setAttribute('alt', image.alt || 'Enlarged hotel photo');
      if (lightboxCounter) lightboxCounter.textContent = `${currentIndex + 1} / ${galleryImages.length}`;
    };

    const openLightbox = (index) => {
      previousFocus = document.activeElement;
      showImage(index);
      lightbox.classList.add('open');
      lightbox.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
      if (lightboxClose) lightboxClose.focus();
    };

    const closeLightbox = () => {
      lightbox.classList.remove('open');
      lightbox.setAttribute('aria-hidden', 'true');
      lightboxImg.setAttribute('src', '');
      document.body.style.overflow = '';
      if (previousFocus && typeof previousFocus.focus === 'function') previousFocus.focus();
    };
    galleryImages.forEach((img, index) => img.addEventListener('click', () => openLightbox(index)));
    if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
    if (lightboxPrev) lightboxPrev.addEventListener('click', () => showImage(currentIndex - 1));
    if (lightboxNext) lightboxNext.addEventListener('click', () => showImage(currentIndex + 1));
    lightbox.addEventListener('click', (ev) => {
      if (ev.target === lightbox) closeLightbox();
    });
    lightbox.addEventListener('touchstart', (ev) => {
      touchStartX = ev.changedTouches[0].screenX;
    }, { passive: true });
    lightbox.addEventListener('touchend', (ev) => {
      const distance = ev.changedTouches[0].screenX - touchStartX;
      if (Math.abs(distance) < 45) return;
      showImage(currentIndex + (distance < 0 ? 1 : -1));
    }, { passive: true });
    document.addEventListener('keydown', (ev) => {
      if (!lightbox.classList.contains('open')) return;
      if (ev.key === 'Escape') closeLightbox();
      if (ev.key === 'ArrowLeft') showImage(currentIndex - 1);
      if (ev.key === 'ArrowRight') showImage(currentIndex + 1);
    });
  }

  // Active nav link highlighting while scrolling
  const scrollNav = document.querySelector('[data-scroll-nav]');
  if (scrollNav) {
    const sectionLinks = Array.from(scrollNav.querySelectorAll('a[href^="#"]'));
    const sections = sectionLinks
      .map((link) => document.querySelector(link.getAttribute('href')))
      .filter(Boolean);
    if (sections.length && 'IntersectionObserver' in window) {
      const navObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          const id = '#' + entry.target.id;
          const link = sectionLinks.find((l) => l.getAttribute('href') === id);
          if (!link) return;
          if (entry.isIntersecting) {
            sectionLinks.forEach((l) => l.classList.remove('active-section'));
            link.classList.add('active-section');
          }
        });
      }, { threshold: 0.3, rootMargin: '-80px 0px -60% 0px' });
      sections.forEach((sec) => navObserver.observe(sec));
    }
  }
});
