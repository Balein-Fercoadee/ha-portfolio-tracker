const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

class FakeElement {
  constructor(tagName = "div") {
    this.tagName = tagName;
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.value = "";
    this.disabled = false;
  }

  addEventListener(name, callback) {
    this.listeners[name] = callback;
  }

  dispatch(name, event = {}) {
    return this.listeners[name]?.(event);
  }

  append(...elements) {
    this.children.push(...elements);
  }

  replaceChildren(...elements) {
    this.children = elements;
  }

  setAttribute(name, value) {
    this[name] = value;
  }
}

class FakeShadowRoot extends FakeElement {
  set innerHTML(_html) {
    this.elements = {
      form: new FakeElement("form"),
      "#symbol": new FakeElement("input"),
      "#amount": new FakeElement("input"),
      "#add": new FakeElement("button"),
      "#currency": new FakeElement("p"),
      "#message": new FakeElement("p"),
      "#holdings": new FakeElement("div"),
    };
  }

  querySelector(selector) {
    return this.elements[selector];
  }

  querySelectorAll(selector) {
    if (selector === ".remove") {
      return this.elements["#holdings"].children.flatMap((row) =>
        row.children.filter((child) => child.className === "remove"),
      );
    }
    return [];
  }
}

class FakeHTMLElement {
  attachShadow() {
    this.shadowRoot = new FakeShadowRoot();
    return this.shadowRoot;
  }
}

const customElements = {
  registry: new Map(),
  define(name, element) {
    this.registry.set(name, element);
  },
};

const source = fs.readFileSync(
  path.join(
    __dirname,
    "..",
    "custom_components",
    "portfolio_tracker",
    "www",
    "portfolio-tracker.js",
  ),
  "utf8",
);
vm.runInNewContext(source, {
  HTMLElement: FakeHTMLElement,
  customElements,
  document: {
    createElement: (tagName) => new FakeElement(tagName),
  },
});

test("panel adds a pair and removes it with the row minus action", async () => {
  const PortfolioPanel = customElements.registry.get(
    "portfolio-tracker-panel",
  );
  const panel = new PortfolioPanel();
  const holdings = [];
  const calls = [];
  panel.hass = {
    callWS: async (message) => {
      calls.push(message);
      if (message.type.endsWith("/get_holdings")) {
        return { currency: "USD", holdings };
      }
      if (message.type.endsWith("/add_holding")) {
        holdings.push({ symbol: "AAPL", quantity: "2.5" });
        return { currency: "USD", holdings: [...holdings] };
      }
      holdings.splice(0, holdings.length);
      return { currency: "USD", holdings: [...holdings] };
    },
  };
  await Promise.resolve();
  await Promise.resolve();

  panel.shadowRoot.querySelector("#symbol").value = "AAPL";
  panel.shadowRoot.querySelector("#amount").value = "2.5";
  await panel.shadowRoot
    .querySelector("form")
    .dispatch("submit", { preventDefault() {} });

  assert.equal(panel.shadowRoot.querySelector("#holdings").children.length, 1);
  assert.match(
    panel.shadowRoot.querySelector("#holdings").children[0].children[0]
      .textContent,
    /AAPL.*2\.5/,
  );
  assert.equal(calls[1].symbol, "AAPL");
  assert.equal(calls[1].amount, "2.5");

  await panel.shadowRoot.querySelectorAll(".remove")[0].dispatch("click");
  assert.equal(panel.shadowRoot.querySelector("#holdings").children.length, 1);
  assert.equal(
    panel.shadowRoot.querySelector("#holdings").children[0].textContent,
    "No holdings yet.",
  );
  assert.equal(calls[2].symbol, "AAPL");
});

test("panel displays backend validation errors", async () => {
  const PortfolioPanel = customElements.registry.get(
    "portfolio-tracker-panel",
  );
  const panel = new PortfolioPanel();
  panel.hass = {
    callWS: async (message) => {
      if (message.type.endsWith("/get_holdings")) {
        return { currency: "USD", holdings: [] };
      }
      throw new Error("duplicate_symbol");
    },
  };
  await Promise.resolve();
  await Promise.resolve();

  panel.shadowRoot.querySelector("#symbol").value = "AAPL";
  panel.shadowRoot.querySelector("#amount").value = "1";
  await panel.shadowRoot
    .querySelector("form")
    .dispatch("submit", { preventDefault() {} });

  assert.equal(
    panel.shadowRoot.querySelector("#message").textContent,
    "duplicate_symbol",
  );
  assert.equal(
    panel.shadowRoot.querySelector("#holdings").children[0].textContent,
    "No holdings yet.",
  );
});
