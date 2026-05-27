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
});
