// SecureMe Password Generator - front end.
// The password only ever lives in this page's memory. It is not saved
// to localStorage, cookies or the URL.

(function () {
  const $ = (id) => document.getElementById(id);
  const form = $("form");
  const pwEl = $("password");
  const copyBtn = $("copy");
  const lengthInput = $("length");
  const lengthValue = $("length-value");
  const wordsField = $("words-field");
  const errorEl = $("error");
  let mode = "random";

  lengthInput.addEventListener("input", () => {
    lengthValue.textContent = lengthInput.value;
  });

  document.querySelectorAll(".tab").forEach((tab) => {
    tab.addEventListener("click", () => {
      mode = tab.dataset.mode;
      document.querySelectorAll(".tab").forEach((t) => {
        const on = t === tab;
        t.classList.toggle("active", on);
        t.setAttribute("aria-selected", on);
      });
      wordsField.hidden = mode !== "words";
      document.querySelectorAll(".random-only").forEach((el) => {
        el.hidden = mode === "words";
      });
      errorEl.textContent = "";
      if (mode === "words") $("words").focus();
    });
  });

  function showStrength(s) {
    const fill = $("meter-fill");
    const label = $("strength-label");
    const colours = { weak: "var(--weak)", medium: "var(--medium)", strong: "var(--strong)" };
    fill.style.width = Math.max(8, s.score) + "%";
    fill.style.background = colours[s.label];
    label.textContent = s.label;
    label.className = s.label;
    $("entropy").textContent = "≈ " + s.entropy + " bits";
    const tip = $("tip");
    if (s.label === "strong") {
      tip.hidden = true;
    } else {
      tip.hidden = false;
      tip.textContent = mode === "words"
        ? "Tip: add another word or slide the length up to make it strong."
        : "Tip: make it longer or switch on more character types.";
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    errorEl.textContent = "";

    const body = {
      mode,
      length: parseInt(lengthInput.value, 10),
      upper: $("upper").checked,
      lower: $("lower").checked,
      digits: $("digits").checked,
      symbols: $("symbols").checked,
      avoid_ambiguous: $("avoid").checked,
      words: $("words").value,
    };

    try {
      const res = await fetch("/api/generate/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          // Django's CSRF protection: token comes from the page's meta tag.
          "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
        },
        credentials: "same-origin",
        body: JSON.stringify(body),
        cache: "no-store",
      });
      const data = await res.json();
      if (!res.ok) {
        errorEl.textContent = data.error || "Something went wrong.";
        return;
      }
      pwEl.textContent = data.password;
      pwEl.classList.add("filled");
      copyBtn.disabled = false;
      copyBtn.textContent = "Copy";
      copyBtn.classList.remove("copied");
      showStrength(data.strength);
    } catch (err) {
      errorEl.textContent = "Couldn't reach the server. Is it running?";
    }
  });

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      return;
    }
    // Fallback for older browsers.
    const ta = document.createElement("textarea");
    ta.value = text;
    ta.setAttribute("readonly", "");
    ta.style.position = "fixed";
    ta.style.opacity = "0";
    document.body.appendChild(ta);
    ta.select();
    document.execCommand("copy");
    document.body.removeChild(ta);
  }

  copyBtn.addEventListener("click", async () => {
    try {
      await copyText(pwEl.textContent);
      copyBtn.textContent = "Copied ✓";
      copyBtn.classList.add("copied");
      setTimeout(() => {
        copyBtn.textContent = "Copy";
        copyBtn.classList.remove("copied");
      }, 2000);
    } catch (err) {
      errorEl.textContent = "Copy failed. Select the password and copy it manually.";
    }
  });
})();
