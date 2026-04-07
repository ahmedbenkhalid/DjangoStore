document.addEventListener('alpine:init', () => {

  Alpine.store('toast', {
    message: '',
    type: 'info',
    visible: false,
    timer: null,

    show(message, type = 'info') {
      this.message = message;
      this.type = type;
      this.visible = true;
      if (this.timer) clearTimeout(this.timer);
      this.timer = setTimeout(() => { this.visible = false; }, 4000);
    },

    hide() {
      this.visible = false;
      if (this.timer) clearTimeout(this.timer);
    }
  });

  Alpine.store('cart', {
    adding: false,
    addedId: null,

    async addToCart(form) {
      if (this.adding) return;
      this.adding = true;

      const formData = new FormData(form);
      const csrf = document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';

      try {
        const res = await fetch(form.action, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': csrf,
          },
          body: formData,
        });
        if (res.ok) await this.refresh();
        this.addedId = form.dataset.productId || Date.now();
        setTimeout(() => { this.addedId = null; }, 1500);
      } catch (e) {
        console.error('Cart error:', e);
        Alpine.store('toast').show('Failed to add to cart. Please try again.', 'error');
      } finally {
        this.adding = false;
      }
    },

    async refresh() {
      try {
        const res = await fetch('/cart/fragment/', {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        const data = await res.json();
        document.querySelector('.js-cart-body').innerHTML = data.items_html;
        document.querySelector('.js-cart-footer').innerHTML = data.footer_html;
        document.querySelectorAll('.js-cart-badge').forEach(el => el.textContent = data.cart_count);
      } catch (e) {
        console.error('Cart refresh error:', e);
      }
    },

    showOffcanvas() {
      const offcanvas = document.getElementById('cartOffcanvas');
      if (offcanvas) {
        const alpineData = Alpine.$data(offcanvas);
        if (alpineData && alpineData.open !== undefined) {
          alpineData.open = true;
        }
      }
    }
  });

  Alpine.store('utils', {
    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (e) {
        console.error('Copy error:', e);
        return false;
      }
    },

    csrf() {
      return document.querySelector('[name=csrfmiddlewaretoken]')?.value
        || document.cookie.split('; ').find(c => c.startsWith('csrftoken='))?.split('=')[1] || '';
    }
  });
});
