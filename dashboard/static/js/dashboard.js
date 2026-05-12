document.addEventListener("DOMContentLoaded", function () {
    const mithaqSearchInput = document.getElementById("mithaqContractSearch");
    const mithaqTable = document.getElementById("mithaqContractsTable");
    const mithaqProgressFills = document.querySelectorAll(".mithaq-progress-fill");
    const mithaqCircleProgress = document.querySelector(".mithaq-circle-progress");

    mithaqProgressFills.forEach(function (fill) {
        const progress = Number(fill.dataset.progress || 0);
        const safeProgress = Math.max(0, Math.min(progress, 100));
        fill.style.width = safeProgress + "%";
    });

    if (mithaqCircleProgress) {
        const progress = Number(mithaqCircleProgress.dataset.progress || 0);
        const safeProgress = Math.max(0, Math.min(progress, 100));
        const degree = safeProgress * 3.6;

        mithaqCircleProgress.style.background =
            conic-gradient(`var(--mithaq-brown) ${degree}deg, #eadccc ${degree}deg`);
    }

    if (mithaqSearchInput && mithaqTable) {
        mithaqSearchInput.addEventListener("keyup", function () {
            const searchValue = mithaqSearchInput.value.toLowerCase();
            const rows = mithaqTable.querySelectorAll("tbody tr");

            rows.forEach(function (row) {
                const rowText = row.innerText.toLowerCase();
                row.style.display = rowText.includes(searchValue) ? "" : "none";
            });
        });
    }
});