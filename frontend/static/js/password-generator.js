(() => {
    const root = document.querySelector("[data-password-generator]");
    if (!root) return;

    const range = root.querySelector("#password-length");
    const lengthOutput = root.querySelector("[data-length-output]");
    const passwordOutput = root.querySelector("[data-generated-password]");
    const generateButton = root.querySelector("[data-generate-password]");
    const regenerateButton = root.querySelector("[data-regenerate-password]");
    const copyButton = root.querySelector("[data-copy-password]");
    const message = root.querySelector("[data-generator-message]");
    const placeholder = "Choose settings and generate a password";
    let generatedPassword = "";

    const selectedCategories = () => {
        const selected = {};
        root.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
            selected[checkbox.name] = checkbox.checked;
        });
        return selected;
    };

    const clearPassword = () => {
        generatedPassword = "";
        passwordOutput.textContent = placeholder;
        copyButton.disabled = true;
        regenerateButton.disabled = true;
    };

    range.addEventListener("input", () => {
        lengthOutput.value = range.value;
        clearPassword();
    });
    root.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
        checkbox.addEventListener("change", clearPassword);
    });

    const generate = async () => {
        const categories = selectedCategories();
        if (!Object.values(categories).some(Boolean)) {
            message.textContent = "Choose at least one character type.";
            message.classList.add("field-error");
            return;
        }
        message.classList.remove("field-error");
        message.textContent = "Generating securely…";
        generateButton.disabled = true;
        regenerateButton.disabled = true;
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        try {
            const response = await fetch("/tools/password-generator", {
                method: "POST",
                credentials: "same-origin",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                },
                body: JSON.stringify({ length: Number(range.value), categories }),
            });
            const payload = await response.json();
            if (!response.ok) throw new Error(payload.error || "Password could not be generated.");
            generatedPassword = payload.password;
            passwordOutput.textContent = generatedPassword;
            copyButton.disabled = false;
            regenerateButton.disabled = false;
            message.textContent = "Generated securely. It is not saved in your account or activity history.";
        } catch (error) {
            clearPassword();
            message.textContent = error.message || "Password could not be generated. Try again.";
            message.classList.add("field-error");
        } finally {
            generateButton.disabled = false;
        }
    };

    generateButton.addEventListener("click", generate);
    regenerateButton.addEventListener("click", generate);
    copyButton.addEventListener("click", async () => {
        if (!generatedPassword) return;
        try {
            await navigator.clipboard.writeText(generatedPassword);
            message.classList.remove("field-error");
            message.textContent = "Copied to clipboard. Remember to save it in a password manager.";
        } catch {
            message.classList.add("field-error");
            message.textContent = "Clipboard access was denied. Select and copy the password manually.";
        }
    });
})();
