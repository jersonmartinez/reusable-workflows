document.querySelectorAll("table thead th[data-sort]").forEach(th => {
    th.style.cursor = "pointer";
    th.addEventListener("click", () => {
        const key = th.dataset.sort;
        const idx = th.cellIndex;
        const table = th.closest("table");
        const rows = [...table.tBodies[0].rows];
        const asc = th.dataset.order != "desc";
        function val(row) {
            const attr = row.getAttribute("data-" + key);
            if (attr) return attr;
            return row.cells[idx].innerText.trim();
        }
        rows.sort((a, b) => {
            let va = val(a), vb = val(b);
            if (key === "num") {
                va = parseInt(String(va).replace(/[^0-9]/g, '')) || 0;
                vb = parseInt(String(vb).replace(/[^0-9]/g, '')) || 0;
                return asc ? va - vb : vb - va;
            }
            if (key === "created") {
                const da = Date.parse(va) || 0, db = Date.parse(vb) || 0;
                return asc ? da - db : db - da;
            }
            if (key === "age") {
                va = parseInt(va) || 0;
                vb = parseInt(vb) || 0;
                return asc ? va - vb : vb - va;
            }
            return asc ? String(va).localeCompare(String(vb)) : String(vb).localeCompare(String(va));
        });
        rows.forEach(r => table.tBodies[0].appendChild(r));
        th.dataset.order = asc ? "desc" : "asc";
    });
});

function cssColors() {
    const style = getComputedStyle(document.body);
    return {
        text: style.getPropertyValue('--bs-body-color') || '#adb5bd',
        grid: style.getPropertyValue('--bs-border-color') || '#495057'
    };
}

let chartTypes, chartEcos;

function initCharts() {
    try {
        const ct = document.getElementById("chartTypes");
        const ce = document.getElementById("chartEcos");
        const cc = cssColors();
        
        if (ct && window.reportData && window.reportData.types) {
            chartTypes = new Chart(ct, {
                type: "bar",
                data: {
                    labels: ["major", "minor", "patch", "other"],
                    datasets: [{
                        label: "Tipos",
                        data: window.reportData.types,
                        backgroundColor: ["#dc3545", "#ffc107", "#198754", "#6c757d"]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: cc.text }, grid: { color: cc.grid } },
                        y: { ticks: { color: cc.text }, grid: { color: cc.grid } }
                    }
                }
            });
        }
        if (ce && window.reportData && window.reportData.ecos) {
            chartEcos = new Chart(ce, {
                type: "doughnut",
                data: {
                    labels: window.reportData.ecos.labels,
                    datasets: [{
                        data: window.reportData.ecos.values,
                        backgroundColor: ["#0d6efd", "#6610f2", "#6f42c1", "#20c997", "#fd7e14", "#198754", "#dc3545", "#6c757d"]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { labels: { color: cc.text } } }
                }
            });
        }
    } catch (e) { console.error(e); }
}

// Initialize charts if Chart.js is loaded
if (typeof Chart !== 'undefined') {
    initCharts();
}
