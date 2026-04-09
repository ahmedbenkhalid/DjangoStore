document.addEventListener("alpine:init", () => {
  Alpine.store("toast", {
    message: "",
    type: "info",
    visible: false,
    timer: null,

    show(message, type = "info") {
      this.message = message;
      this.type = type;
      this.visible = true;
      if (this.timer) clearTimeout(this.timer);
      this.timer = setTimeout(() => {
        this.visible = false;
      }, 4000);
    },

    hide() {
      this.visible = false;
      if (this.timer) clearTimeout(this.timer);
    },
  });

  Alpine.store("cart", {
    adding: false,
    addedId: null,

    async addToCart(form) {
      if (this.adding) return;
      this.adding = true;

      const formData = new FormData(form);
      const csrf = Alpine.store("utils").csrf();

      try {
        const res = await fetch(form.action, {
          method: "POST",
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrf,
          },
          body: formData,
        });
        const data = await res.json();
        if (res.ok && data.success) {
          this.updateUI(data);
          this.addedId = form.dataset.productId || Date.now();
          setTimeout(() => { this.addedId = null; }, 1500);
        } else {
          Alpine.store("toast").show(data.error || "Error updating cart", "error");
        }
      } catch (e) {
        console.error("Cart error:", e);
        Alpine.store("toast").show("Connection error", "error");
      } finally {
        this.adding = false;
      }
    },

    updateUI(data) {
      if (data.items_html) document.querySelector(".js-cart-body").innerHTML = data.items_html;
      if (data.footer_html) document.querySelector(".js-cart-footer").innerHTML = data.footer_html;
      document.querySelectorAll(".js-cart-badge").forEach((el) => (el.textContent = data.cart_count));
    },

    async refresh() {
      try {
        const url = window.CART_FRAGMENT_URL || "/cart/fragment/";
        const res = await fetch(url, {
          headers: { "X-Requested-With": "XMLHttpRequest" },
        });
        const data = await res.json();
        this.updateUI(data);
      } catch (e) {
        console.error("Cart refresh error:", e);
      }
    },

    showOffcanvas() {
      window.dispatchEvent(new CustomEvent("cart-open"));
    },
  });

  Alpine.store("utils", {
    async copy(text) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch (e) {
        console.error("Copy error:", e);
        return false;
      }
    },

    csrf() {
      return (
        document.querySelector("[name=csrfmiddlewaretoken]")?.value ||
        document.cookie
          .split("; ")
          .find((c) => c.startsWith("csrftoken="))
          ?.split("=")[1] ||
        ""
      );
    },
  });
});
