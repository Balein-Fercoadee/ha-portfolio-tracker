class PortfolioTrackerPanel extends HTMLElement {
  constructor() {
    super();
    this._holdings = [];
    this._busy = false;
    this._loaded = false;
    this.attachShadow({ mode: "open" });
    this._render();
  }

  set hass(hass) {
    this._hass = hass;
    if (!this._loaded) {
      this._loaded = true;
      this._load();
    }
  }

  async _load() {
    try {
      const portfolio = await this._hass.callWS({
        type: "portfolio_tracker/get_holdings",
      });
      this._holdings = portfolio.holdings;
      this._currency = portfolio.currency;
      this._interval = portfolio.scan_interval;
      this._minInterval = portfolio.min_scan_interval;
      this._maxInterval = portfolio.max_scan_interval;
      this._render();
    } catch (error) {
      this._showError(error);
    }
  }

  async _addHolding(event) {
    event.preventDefault();
    if (this._busy) {
      return;
    }

    const symbol = this.shadowRoot.querySelector("#symbol").value.trim();
    const amount = this.shadowRoot.querySelector("#amount").value.trim();
    this._busy = true;
    this._render();
    try {
      const portfolio = await this._hass.callWS({
        type: "portfolio_tracker/add_holding",
        symbol,
        amount,
      });
      this._holdings = portfolio.holdings;
      this.shadowRoot.querySelector("#symbol").value = "";
      this.shadowRoot.querySelector("#amount").value = "";
      this._setMessage("Holding added.", false);
      this._renderHoldings();
    } catch (error) {
      this._showError(error);
    } finally {
      this._busy = false;
      this._setBusy(false);
    }
  }

  async _removeHolding(symbol) {
    if (this._busy) {
      return;
    }

    this._busy = true;
    this._setBusy(true);
    try {
      const portfolio = await this._hass.callWS({
        type: "portfolio_tracker/remove_holding",
        symbol,
      });
      this._holdings = portfolio.holdings;
      this._setMessage("Holding removed.", false);
      this._renderHoldings();
    } catch (error) {
      this._showError(error);
    } finally {
      this._busy = false;
      this._setBusy(false);
    }
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        :host { display: block; padding: 24px; color: var(--primary-text-color); }
        main { max-width: 720px; margin: 0 auto; }
        h1 { font-size: 1.5rem; }
        form, .holding { display: flex; align-items: end; gap: 12px; }
        form { flex-wrap: wrap; margin: 24px 0; }
        label { display: grid; flex: 1 1 180px; gap: 6px; }
        input { box-sizing: border-box; width: 100%; padding: 10px; }
        button { min-height: 40px; min-width: 44px; cursor: pointer; }
        .holding { justify-content: space-between; padding: 12px 0; border-bottom: 1px solid var(--divider-color); }
        .holding span { flex: 1; }
        .remove { color: var(--error-color); }
        #message { min-height: 1.5em; color: var(--error-color); }
        #message[data-error="false"] { color: var(--success-color, var(--primary-text-color)); }
        @media (max-width: 520px) {
          :host { padding: 16px; }
          form { align-items: stretch; }
          form button { width: 100%; }
        }
      </style>
      <main>
        <h1>Investment Portfolio</h1>
        <p id="currency"></p>
        <form id="interval-form">
          <label>
            Update frequency (minutes, min: ${this._minInterval ?? 10}, max: ${this._maxInterval ?? 120})
            <input id="interval" name="interval" type="number" step="1" required />
          </label>
          <button id="save-interval" type="submit">Save</button>
        </form>
        <p id="message" role="status" aria-live="polite"></p>
        <form id="holding-form">
          <label>
            Symbol
            <input id="symbol" name="symbol" autocomplete="off" required />
          </label>
          <label>
            Quantity
            <input id="amount" name="amount" type="number" min="0" step="any" required />
          </label>
          <button id="add" type="submit" aria-label="Add holding">+</button>
        </form>
        <section aria-label="Configured holdings">
          <h2>Holdings (Symbol — Quantity)</h2>
          <div id="holdings"></div>
        </section>
      </main>
    `;

    this.shadowRoot.querySelector("#holding-form").addEventListener("submit", (event) => {
      return this._addHolding(event);
    });
    this.shadowRoot.querySelector("#interval-form").addEventListener("submit", (event) => {
      return this._saveInterval(event);
    });
    this._renderHoldings();
    this._renderInterval();
    this._setBusy(this._busy);
  }

  _renderInterval() {
    const input = this.shadowRoot.querySelector("#interval");
    input.min = String(this._minInterval ?? 10);
    input.max = String(this._maxInterval ?? 120);
    if (this._interval !== undefined) {
      input.value = String(this._interval);
    }
  }

  async _saveInterval(event) {
    event.preventDefault();
    if (this._busy) {
      return;
    }

    const input = this.shadowRoot.querySelector("#interval");
    const minutes = Number(input.value);
    const min = this._minInterval ?? 10;
    const max = this._maxInterval ?? 120;
    if (!Number.isInteger(minutes) || minutes < min || minutes > max) {
      this._setMessage(`Update frequency must be between ${min} and ${max} minutes.`, true);
      return;
    }

    this._busy = true;
    this._setBusy(true);
    try {
      const result = await this._hass.callWS({
        type: "portfolio_tracker/set_scan_interval",
        minutes,
      });
      this._interval = result.scan_interval;
      this._setMessage("Update frequency saved.", false);
    } catch (error) {
      this._showError(error);
    } finally {
      this._busy = false;
      this._setBusy(false);
    }
  }

  _renderHoldings() {
    const list = this.shadowRoot.querySelector("#holdings");
    const currency = this.shadowRoot.querySelector("#currency");
    list.replaceChildren();
    currency.textContent = this._currency
      ? `Portfolio currency: ${this._currency}`
      : "";

    if (!this._holdings.length) {
      const empty = document.createElement("p");
      empty.textContent = "No holdings yet.";
      list.append(empty);
      return;
    }

    for (const holding of this._holdings) {
      const row = document.createElement("div");
      row.className = "holding";
      const label = document.createElement("span");
      label.textContent = `${holding.symbol} — ${holding.quantity}`;
      const remove = document.createElement("button");
      remove.type = "button";
      remove.className = "remove";
      remove.textContent = "−";
      remove.setAttribute("aria-label", `Remove ${holding.symbol}`);
      remove.disabled = this._busy;
      remove.addEventListener("click", () => this._removeHolding(holding.symbol));
      row.append(label, remove);
      list.append(row);
    }
  }

  _showError(error) {
    this._setMessage(error.message || "Unable to update holdings.", true);
  }

  _setMessage(message, isError) {
    const element = this.shadowRoot.querySelector("#message");
    element.textContent = message;
    element.dataset.error = String(isError);
  }

  _setBusy(busy) {
    this.shadowRoot.querySelector("#symbol").disabled = busy;
    this.shadowRoot.querySelector("#amount").disabled = busy;
    this.shadowRoot.querySelector("#add").disabled = busy;
    this.shadowRoot.querySelector("#interval").disabled = busy;
    this.shadowRoot.querySelector("#save-interval").disabled = busy;
    for (const button of this.shadowRoot.querySelectorAll(".remove")) {
      button.disabled = busy;
    }
  }
}

customElements.define("portfolio-tracker-panel", PortfolioTrackerPanel);
