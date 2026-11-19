(() => {
    const readJson = async (response) => {
        if (response.redirected) throw new Error("Your session may have expired. Sign in and try again.");
        if (!(response.headers.get("Content-Type") || "").includes("application/json")) {
            throw new Error("The request was not completed. Refresh the page and try again.");
        }
        return response.json();
    };

    const downloadBlob = async (response, filename) => {
        if (response.redirected) throw new Error("Your session may have expired. Sign in and try again.");
        if (!response.ok) {
            const payload = await readJson(response);
            throw new Error(payload.error || "The report could not be created.");
        }
        const contentType = response.headers.get("Content-Type") || "";
        if (!contentType.startsWith("text/csv") && !contentType.startsWith("text/plain")) {
            throw new Error("The report response was not a supported text format.");
        }
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
    };

    const formatSize = (size) => {
        if (size < 1024) return `${size} bytes`;
        if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KiB`;
        return `${(size / (1024 * 1024)).toFixed(2)} MiB`;
    };

    document.querySelectorAll("[data-file-tool]").forEach((root) => {
        const form = root.querySelector("[data-analysis-form]");
        const result = root.querySelector("[data-result]");
        const message = root.querySelector("[data-tool-message]");
        const submitButton = root.querySelector("[data-submit-button]");
        const fileInputs = [...form.querySelectorAll('input[type="file"]')];
        let latestResult = null;
        let selectionVersion = 0;

        const postReport = async () => {
            const body = new FormData(form);
            body.append("format", root.querySelector("[data-report-format]").value);
            const response = await fetch(root.dataset.reportEndpoint, {
                method: "POST",
                credentials: "same-origin",
                body,
            });
            const name = root.hasAttribute("data-comparison")
                ? "cyberguard-file-comparison-report"
                : "cyberguard-hash-report";
            await downloadBlob(
                response,
                `${name}.${root.querySelector("[data-report-format]").value}`,
            );
        };

        form.addEventListener("change", () => {
            selectionVersion += 1;
            latestResult = null;
            result.hidden = true;
            message.textContent = "";
        });

        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            const oversized = fileInputs
                .some((input) => input.files[0] && input.files[0].size > 16 * 1024 * 1024);
            if (oversized) {
                message.textContent = "Each file must be 16 MiB or smaller.";
                return;
            }
            const requestVersion = selectionVersion;
            const body = new FormData(form);
            result.hidden = true;
            latestResult = null;
            message.textContent = "Processing file content in chunks…";
            submitButton.disabled = true;
            try {
                const response = await fetch(root.dataset.endpoint, {
                    method: "POST",
                    credentials: "same-origin",
                    body,
                });
                const payload = await readJson(response);
                if (!response.ok) throw new Error(payload.error || "The operation could not be completed.");
                if (requestVersion !== selectionVersion) return;
                latestResult = payload;
                if (root.hasAttribute("data-comparison")) {
                    root.querySelector("[data-comparison-result]").textContent = payload.match
                        ? "SHA-256 hashes match"
                        : "SHA-256 hashes differ";
                    root.querySelector("[data-original-name]").textContent = payload.original_filename;
                    root.querySelector("[data-original-hash]").textContent = payload.original_hash;
                    root.querySelector("[data-comparison-name]").textContent = payload.comparison_filename;
                    root.querySelector("[data-comparison-hash]").textContent = payload.comparison_hash;
                } else {
                    root.querySelector("[data-file-name]").textContent = payload.filename;
                    root.querySelector("[data-file-size]").textContent = formatSize(payload.size);
                    root.querySelector("[data-hash-value]").textContent = payload.sha256;
                }
                result.hidden = false;
                message.textContent = "Complete. The uploaded file content was not saved.";
            } catch (error) {
                message.textContent = error.message || "The operation could not be completed.";
            } finally {
                submitButton.disabled = false;
            }
        });

        const copyButton = root.querySelector("[data-copy-value]");
        if (copyButton) {
            copyButton.addEventListener("click", async () => {
                try {
                    await navigator.clipboard.writeText(root.querySelector("[data-hash-value]").textContent);
                    message.textContent = "SHA-256 hash copied.";
                } catch {
                    message.textContent = "Clipboard access was denied. Select and copy the hash manually.";
                }
            });
        }

        root.querySelector("[data-download-report]").addEventListener("click", async () => {
            if (!latestResult) return;
            message.textContent = "Creating report…";
            try {
                await postReport();
                message.textContent = "Report downloaded. It is not stored by CyberGuard.";
            } catch (error) {
                message.textContent = error.message || "The report could not be created.";
            }
        });
    });

    const root = document.querySelector("[data-url-tool]");
    if (!root) return;
    const form = root.querySelector("[data-analysis-form]");
    const result = root.querySelector("[data-result]");
    const message = root.querySelector("[data-tool-message]");
    const submitButton = root.querySelector("[data-submit-button]");
    const reportButton = root.querySelector("[data-download-report]");
    let hasResult = false;

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        result.hidden = true;
        hasResult = false;
        message.textContent = "Reviewing URL structure…";
        submitButton.disabled = true;
        try {
            const response = await fetch(root.dataset.endpoint, {
                method: "POST",
                credentials: "same-origin",
                body: new FormData(form),
            });
            const payload = await readJson(response);
            if (!response.ok) throw new Error(payload.error || "The URL could not be analyzed.");
            root.querySelector("[data-risk-level]").textContent = payload.risk_level;
            root.querySelector("[data-risk-level]").className = `risk-${payload.risk_level.toLowerCase()}`;
            root.querySelector("[data-hostname]").textContent = payload.hostname;
            root.querySelector("[data-disclaimer]").textContent = payload.disclaimer;
            for (const [selector, items, emptyText] of [
                ["[data-indicators]", payload.indicators, "No listed indicators were detected."],
                ["[data-recommendations]", payload.recommendations, ""],
            ]) {
                const list = root.querySelector(selector);
                list.replaceChildren();
                const values = items.length ? items : [emptyText];
                for (const value of values) {
                    const item = document.createElement("li");
                    item.textContent = value;
                    list.append(item);
                }
            }
            hasResult = true;
            result.hidden = false;
            message.textContent = "Analysis complete. The submitted URL was not visited or fetched.";
        } catch (error) {
            hasResult = false;
            message.textContent = error.message || "The URL could not be analyzed.";
        } finally {
            submitButton.disabled = false;
        }
    });

    reportButton.addEventListener("click", async () => {
        if (!hasResult) return;
        message.textContent = "Creating report…";
        try {
            const body = new FormData(form);
            body.append("format", root.querySelector("[data-report-format]").value);
            const response = await fetch(root.dataset.reportEndpoint, {
                method: "POST",
                credentials: "same-origin",
                body,
            });
            await downloadBlob(
                response,
                `cyberguard-url-analysis-report.${root.querySelector("[data-report-format]").value}`,
            );
            message.textContent = "Report downloaded. It is not stored by CyberGuard.";
        } catch (error) {
            message.textContent = error.message || "The report could not be created.";
        }
    });

    form.addEventListener("input", () => {
        hasResult = false;
        result.hidden = true;
        message.textContent = "";
    });
})();