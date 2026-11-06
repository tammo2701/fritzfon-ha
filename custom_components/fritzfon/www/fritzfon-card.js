/* FRITZ!Fon full-screen incoming call card. */
class FritzFonCallCard extends HTMLElement {
  set hass(hass) {
    if (!this._root) this._build();
    if (!this._subscribed) {
      this._subscribed = true;
      hass.connection.subscribeEvents((event) => this._show(event.data), "fritzfon_call");
    }
  }
  setConfig(config) { this._config = config || {}; }
  getCardSize() { return 1; }
  _build() {
    this._root = this.attachShadow({ mode: "open" });
    this._root.innerHTML = `<style>:host{display:block}.overlay{display:none;position:fixed;inset:0;z-index:99999;background:rgba(8,12,20,.96);color:white;align-items:center;justify-content:center;text-align:center;font-family:var(--primary-font-family,Roboto,sans-serif)}.overlay.visible{display:flex}.box{padding:32px;max-width:90vw}.icon{font-size:72px;color:#65d6a5}.title{font-size:clamp(32px,7vw,72px);margin:20px 0 8px}.number{font-size:clamp(22px,4vw,40px);opacity:.8}button{margin-top:38px;border:0;border-radius:999px;padding:14px 34px;font-size:20px;cursor:pointer}</style><div class="overlay" role="alertdialog" aria-modal="true"><div class="box"><div class="icon">☎</div><div class="title"></div><div class="number"></div><button>Schließen</button></div></div>`;
    this._overlay = this._root.querySelector(".overlay");
    this._root.querySelector("button").addEventListener("click", () => this._hide());
  }
  _show(data) {
    if (!data || data.state !== "ringing") return;
    this._root.querySelector(".title").textContent = data.from_name || "Eingehender Anruf";
    this._root.querySelector(".number").textContent = data.from || "Unbekannte Nummer";
    this._overlay.classList.add("visible");
  }
  _hide() { this._overlay.classList.remove("visible"); }
}
customElements.define("fritzfon-call-card", FritzFonCallCard);
window.customCards = window.customCards || [];
window.customCards.push({ type: "fritzfon-call-card", name: "FRITZ!Fon Anrufalarm", description: "Fullscreen-Benachrichtigung bei eingehenden FRITZ!Box-Anrufen" });
