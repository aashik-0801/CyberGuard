(() => {
    const root = document.querySelector("[data-password-checker]");
    if (!root) return;

    const input = root.querySelector("#password-input");
    const toggle = root.querySelector("[data-password-toggle]");
    const label = root.querySelector("[data-strength-label]");
    const meter = root.querySelector(".strength-meter");
    const suggestions = root.querySelector("[data-suggestions] p");
    const commonPasswords = new Set([
        "123456", "123456789", "12345678", "password", "password1",
        "qwerty", "qwerty123", "letmein", "welcome", "admin",
        "iloveyou", "changeme", "abc123", "111111",
    ]);
    let checkerEventSent = false;

    const hasSequentialPattern = (value) => {
        const lowered = value.toLowerCase();
        return ["1234", "2345", "3456", "abcd", "bcde", "qwerty"].some((part) => lowered.includes(part));
    };

    const analyze = (value) => {
        const length = Array.from(value).length;
        const checks = {
            uppercase: /[A-Z]/.test(value),
            lowercase: /[a-z]/.test(value),
            number: /[0-9]/.test(value),
            symbol: /[^A-Za-z0-9]/.test(value),
        };
        const common = commonPasswords.has(value.toLowerCase());
        const sequential = hasSequentialPattern(value);
        const classes = Object.values(checks).filter(Boolean).length;
        const lengthPoints = length >= 20 ? 4 : length >= 16 ? 3 : length >= 12 ? 2 : length >= 8 ? 1 : 0;
        let score = lengthPoints + classes;
        if (common) score = 0;
        else if (sequential || /(.)\1{3,}/.test(value)) score = Math.max(0, score - 2);

        let strength = "Very Weak";
        if (length >= 8 && score >= 2 && score <= 3) strength = "Weak";
        if (length >= 8 && score >= 4 && score <= 5) strength = "Moderate";
        if (length >= 12 && score >= 6 && score <= 7) strength = "Strong";
        if (length >= 16 && score >= 8) strength = "Very Strong";

        const advice = [];
        if (common) advice.push("This is a commonly used password. Replace it with something unique.");
        if (length < 16) advice.push("Use at least 16 characters; a longer passphrase can be easier to remember.");
        if (!checks.uppercase || !checks.lowercase || !checks.number || !checks.symbol) {
            advice.push("Consider adding a mix of uppercase, lowercase, numbers, and symbols.");
        }
        if (sequential || /(.)\1{3,}/.test(value)) advice.push("Avoid predictable sequences and repeated characters.");
        if (!advice.length) advice.push("This has useful length and variety. Keep it unique to one account.");
        return { length, checks, strength, advice, common };
    };

    const showCheck = (selector, passed, empty) => {
        const element = root.querySelector(selector);
        element.textContent = empty ? "—" : passed ? "Yes" : "No";
        element.classList.toggle("check-good", !empty && passed);
        element.classList.toggle("check-miss", !empty && !passed);
    };

    const update = () => {
        const value = input.value;
        const empty = value.length === 0;
        if (empty) {
            label.textContent = "Waiting for input";
            label.className = "";
            meter.dataset.level = "0";
            root.querySelector("[data-length-check]").textContent = "—";
            suggestions.textContent = "Start typing to see practical ways to improve a password.";
            showCheck("[data-uppercase-check]", false, true);
            showCheck("[data-lowercase-check]", false, true);
            showCheck("[data-number-check]", false, true);
            showCheck("[data-symbol-check]", false, true);
            return;
        }

        const result = analyze(value);
        label.textContent = result.strength;
        label.className = `strength-${result.strength.toLowerCase().replaceAll(" ", "-")}`;
        const levels = { "Very Weak": 1, Weak: 2, Moderate: 3, Strong: 4, "Very Strong": 5 };
        meter.dataset.level = String(levels[result.strength]);
        root.querySelector("[data-length-check]").textContent = `${result.length} characters`;
        showCheck("[data-uppercase-check]", result.checks.uppercase, false);
        showCheck("[data-lowercase-check]", result.checks.lowercase, false);
        showCheck("[data-number-check]", result.checks.number, false);
        showCheck("[data-symbol-check]", result.checks.symbol, false);
        suggestions.textContent = result.advice.join(" ");

        if (!checkerEventSent) {
            checkerEventSent = true;
            const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
            fetch("/tools/password-checker/used", {
                method: "POST",
                credentials: "same-origin",
                headers: { "X-CSRFToken": csrfToken },
            }).catch(() => {
                checkerEventSent = false;
            });
        }
    };

    toggle.addEventListener("click", () => {
        const reveal = input.type === "password";
        input.type = reveal ? "text" : "password";
        toggle.textContent = reveal ? "Hide" : "Show";
        toggle.setAttribute("aria-label", reveal ? "Hide password" : "Show password");
        toggle.setAttribute("aria-pressed", String(reveal));
    });
    input.addEventListener("input", update);
    update();
})();
