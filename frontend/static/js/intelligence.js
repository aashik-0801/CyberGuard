(function () {
    const endpoint = "/intelligence/analytics.json" + window.location.search;
    const colors = {
        cyan: "#00D4FF",
        blue: "#3B82F6",
        green: "#39D9A5",
        red: "#FF727F",
        line: "#253248",
        text: "#94A3B8",
    };

    function setupCanvas(canvas) {
        const rect = canvas.getBoundingCanvasRect ? canvas.getBoundingCanvasRect() : canvas.getBoundingClientRect();
        const width = rect.width || 600;
        const height = Number(canvas.getAttribute("height")) || 220;
        canvas.width = width * window.devicePixelRatio;
        canvas.height = height * window.devicePixelRatio;
        const ctx = canvas.getContext("2d");
        ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
        return { ctx, width, height };
    }

    function drawAxes(ctx, width, height, maxValue) {
        ctx.strokeStyle = colors.line;
        ctx.fillStyle = colors.text;
        ctx.lineWidth = 1;
        ctx.font = "10px Segoe UI";
        for (let i = 0; i <= 4; i += 1) {
            const y = 20 + (height - 50) * i / 4;
            ctx.beginPath();
            ctx.moveTo(42, y);
            ctx.lineTo(width - 10, y);
            ctx.stroke();
            ctx.fillText(String(Math.round(maxValue * (4 - i) / 4)), 8, y + 3);
        }
    }

    function lineChart(canvas, labels, series) {
        const { ctx, width, height } = setupCanvas(canvas);
        const maxValue = Math.max(1, ...series.flatMap((item) => item.values));
        drawAxes(ctx, width, height, maxValue);
        const plotWidth = width - 52;
        const plotHeight = height - 50;
        ctx.textAlign = "center";
        labels.forEach((label, index) => {
            if (labels.length > 12 && index % Math.ceil(labels.length / 8) !== 0) return;
            const x = 42 + plotWidth * (labels.length === 1 ? 0.5 : index / (labels.length - 1));
            ctx.fillStyle = colors.text;
            ctx.fillText(label.slice(5), x, height - 10);
        });
        series.forEach((item) => {
            ctx.beginPath();
            ctx.strokeStyle = item.color;
            ctx.lineWidth = 2;
            item.values.forEach((value, index) => {
                const x = 42 + plotWidth * (item.values.length === 1 ? 0.5 : index / (item.values.length - 1));
                const y = 20 + plotHeight - plotHeight * value / maxValue;
                if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            });
            ctx.stroke();
        });
    }

    function barChart(canvas, labels, values, color) {
        const { ctx, width, height } = setupCanvas(canvas);
        const maxValue = Math.max(1, ...values);
        drawAxes(ctx, width, height, maxValue);
        const plotWidth = width - 52;
        const slot = plotWidth / Math.max(labels.length, 1);
        ctx.textAlign = "center";
        labels.forEach((label, index) => {
            const barWidth = Math.max(8, slot * 0.55);
            const x = 42 + slot * index + slot / 2;
            const barHeight = (height - 50) * values[index] / maxValue;
            ctx.fillStyle = color;
            ctx.fillRect(x - barWidth / 2, height - 30 - barHeight, barWidth, barHeight);
            ctx.fillStyle = colors.text;
            ctx.fillText(label, x, height - 10);
        });
    }

    function distributionChart(canvas, distribution) {
        const entries = Object.entries(distribution);
        const { ctx, width, height } = setupCanvas(canvas);
        if (!entries.length) {
            ctx.fillStyle = colors.text;
            ctx.textAlign = "center";
            ctx.fillText("No recorded events", width / 2, height / 2);
            return;
        }
        const palette = [colors.cyan, colors.blue, colors.green, colors.red, "#B39AFF", "#F0B429"];
        const total = entries.reduce((sum, item) => sum + item[1], 0);
        let start = -Math.PI / 2;
        const centerX = width * 0.38;
        const centerY = height / 2;
        const radius = Math.min(width * 0.22, height * 0.38);
        entries.forEach(([label, value], index) => {
            const end = start + (value / total) * Math.PI * 2;
            ctx.beginPath();
            ctx.moveTo(centerX, centerY);
            ctx.arc(centerX, centerY, radius, start, end);
            ctx.closePath();
            ctx.fillStyle = palette[index % palette.length];
            ctx.fill();
            start = end;
        });
        ctx.textAlign = "left";
        entries.forEach(([label, value], index) => {
            const y = 45 + index * 24;
            ctx.fillStyle = palette[index % palette.length];
            ctx.fillRect(width * 0.66, y - 8, 10, 10);
            ctx.fillStyle = colors.text;
            ctx.fillText(label.replace(/_/g, " "), width * 0.66 + 16, y);
        });
    }

    fetch(endpoint, { credentials: "same-origin", headers: { "Accept": "application/json" } })
        .then((response) => {
            if (!response.ok) throw new Error("Analytics request failed");
            return response.json();
        })
        .then((data) => {
            if (data.total_events === 0) {
                document.getElementById("analytics-empty").hidden = false;
            }
            lineChart(document.getElementById("login-chart"), data.labels, [
                { values: data.login, color: colors.cyan },
                { values: data.failed_login, color: colors.red },
                { values: data.logout, color: colors.blue },
            ]);
            distributionChart(document.getElementById("distribution-chart"), data.distribution);
            lineChart(document.getElementById("trend-chart"), data.labels, [
                { values: data.daily_total, color: colors.cyan },
                { values: data.tool_usage, color: colors.green },
            ]);
            const toolLabels = ["Checks", "Generated", "Hashes", "Compare", "URLs"];
            const toolValues = [
                data.tool_counts["Password checks"],
                data.tool_counts["Passwords generated"],
                data.tool_counts["File hashes"],
                data.tool_counts["File comparisons"],
                data.tool_counts["URL analyses"],
            ];
            barChart(document.getElementById("tool-chart"), toolLabels, toolValues, colors.cyan);
        })
        .catch(() => {
            document.getElementById("analytics-empty").hidden = false;
            document.getElementById("analytics-empty").querySelector("strong").textContent = "Analytics unavailable";
            document.getElementById("analytics-empty").querySelector("p").textContent = "The chart data could not be loaded.";
        });
})();
