/* ============================================================
   predict.js — Validation, auto-calc, and prediction logic
   for the Predict Activity Level page
   ============================================================ */

// ── Validation rules ──────────────────────────────────────────────────────────
const RULES = {
    total_rental:     { min: 1,   max: 500, label: 'Total Rental',     unit: '',       integer: true  },
    active_months:    { min: 1,   max: 60,  label: 'Active Months',    unit: 'months', integer: true  },
    rental_frequency: { min: 0.1, max: 50,  label: 'Rental Frequency', unit: '/month', integer: false },
    avg_interval:     { min: 0.5, max: 365, label: 'Average Interval', unit: 'days',   integer: false },
};

// ── Insights per cluster ──────────────────────────────────────────────────────
const insights = {
    High: {
        title: "Cluster: HIGH Activity",
        text: "K-Means placed this customer in the High cluster based on high rental volume, high frequency, and short intervals between rentals. Purely data-driven, no manual rules applied.",
    },
    Medium: {
        title: "Cluster: MEDIUM Activity",
        text: "K-Means placed this customer in the Medium cluster. They show a consistent but moderate rental pattern, distinct from both High and Low clusters.",
    },
    Low: {
        title: "Cluster: LOW Activity",
        text: "K-Means placed this customer in the Low cluster due to infrequent rentals and long gaps between transactions. Re-engagement may be needed.",
    }
};

// ── Recommendations per cluster ───────────────────────────────────────────────
const recommendations = {
    High: {
        title: "Recommendation: Retain & Reward",
        items: [
            "Offer a loyalty program or exclusive discounts to maintain engagement.",
            "Provide early access to new releases or premium content.",
            "Use this segment as a benchmark for service quality.",
        ]
    },
    Medium: {
        title: "Recommendation: Push Toward High",
        items: [
            "Send personalized film recommendations to boost rental frequency.",
            "Offer a 'rent X, get one free' promo to encourage more transactions.",
            "Monitor trends, intervene quickly if frequency declines.",
        ]
    },
    Low: {
        title: "Recommendation: Re-engagement Campaign",
        items: [
            "Send a limited-time discount or promo via email/notification.",
            "Offer a free trial on new titles to reignite interest.",
            "Investigate churn reasons. Price, content, or service issues?",
        ]
    }
};

// ── Cross-field logical consistency check ─────────────────────────────────────
function getLogicErrors(total, months, freq, interval) {
    const errs = [];
    const expectedFreq     = total / months;
    const expectedInterval = (months * 30) / total;

    if (freq > expectedFreq * 3) {
        errs.push(
            `Rental Frequency (${freq}/month) is too high for ${total} rentals ` +
            `over ${months} months — expected ~${expectedFreq.toFixed(1)}/month.`
        );
    } else if (freq < expectedFreq / 3) {
        errs.push(
            `Rental Frequency (${freq}/month) is too low for ${total} rentals ` +
            `over ${months} months — expected ~${expectedFreq.toFixed(1)}/month.`
        );
    }

    if (interval > expectedInterval * 3) {
        errs.push(
            `Average Interval (${interval} days) is too long for ${total} rentals ` +
            `over ${months} months — expected ~${expectedInterval.toFixed(1)} days.`
        );
    } else if (interval < expectedInterval / 3) {
        errs.push(
            `Average Interval (${interval} days) is too short for ${total} rentals ` +
            `over ${months} months — expected ~${expectedInterval.toFixed(1)} days.`
        );
    }

    if (freq > total) {
        errs.push(`Rental Frequency (${freq}/month) cannot exceed Total Rental (${total}).`);
    }

    return errs;
}

// ── Real-time numeric validation ──────────────────────────────────────────────
function validateNumeric(id) {
    const inp = document.getElementById(id);
    const err = document.getElementById('err_' + id);
    const val = inp.value.trim();

    if (val === '') {
        err.style.display = 'none';
        inp.classList.remove('input-error');
        return;
    }

    const numericPattern = /^-?\d+\.?\d*$/;
    if (!numericPattern.test(val)) {
        err.textContent = 'Only numbers allowed (e.g. 27)';
        err.style.display = 'flex';
        inp.classList.add('input-error');
    } else {
        err.style.display = 'none';
        inp.classList.remove('input-error');
    }
}

function clearError(id) {
    document.getElementById('err_' + id).style.display = 'none';
    document.getElementById(id).classList.remove('input-error');
}

// ── Show / hide global alert ──────────────────────────────────────────────────
function showGlobalAlert(msgs) {
    const box  = document.getElementById('global-alert');
    const list = document.getElementById('global-alert-list');
    if (msgs.length === 0) {
        box.style.display = 'none';
        list.innerHTML = '';
        return;
    }
    list.innerHTML = msgs.map(m => `<li>${m}</li>`).join('');
    box.style.display = 'block';
    box.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ── Auto-calculate Rental Frequency and Avg Interval ─────────────────────────
function autoCalcAll() {
    const total  = parseFloat(document.getElementById('total_rental').value);
    const months = parseFloat(document.getElementById('active_months').value);
    const freqEl = document.getElementById('rental_frequency');
    const intEl  = document.getElementById('avg_interval');

    if (total > 0 && months > 0) {
        freqEl.value = (total / months).toFixed(2);
        intEl.value  = ((months * 30) / total).toFixed(1);
        clearError('rental_frequency');
        clearError('avg_interval');
    }
}

// ── Full form validation ──────────────────────────────────────────────────────
function validate() {
    const fields = ['total_rental', 'active_months', 'rental_frequency', 'avg_interval'];
    let valid = true;

    fields.forEach(id => {
        const input = document.getElementById(id);
        const err   = document.getElementById('err_' + id);
        const rule  = RULES[id];

        // Auto-calculated fields: skip validation
        if (input.disabled) {
            err.style.display = 'none';
            input.classList.remove('input-error');
            return;
        }

        // Required check
        if (input.value === '') {
            err.textContent = 'This field is required.';
            err.style.display = 'flex';
            input.classList.add('input-error');
            valid = false;
            return;
        }

        // Numeric format check
        const numericPattern = /^-?\d+\.?\d*$/;
        if (!numericPattern.test(input.value.trim())) {
            err.textContent = 'Only numbers allowed (e.g. 27).';
            err.style.display = 'flex';
            input.classList.add('input-error');
            valid = false;
            return;
        }

        // Range & integer check
        const val = parseFloat(input.value);
        if (isNaN(val)) {
            err.textContent = 'This field is required.';
            err.style.display = 'flex';
            input.classList.add('input-error');
            valid = false;
        } else if (val < rule.min) {
            err.textContent = `Minimum is ${rule.min}${rule.unit ? ' ' + rule.unit : ''}.`;
            err.style.display = 'flex';
            input.classList.add('input-error');
            valid = false;
        } else if (val > rule.max) {
            err.textContent = `Maximum is ${rule.max}${rule.unit ? ' ' + rule.unit : ''}. Value ${val} seems unrealistic.`;
            err.style.display = 'flex';
            input.classList.add('input-error');
            valid = false;
        } else if (rule.integer && !Number.isInteger(val)) {
            err.textContent = `${rule.label} must be a whole number (no decimals).`;
            err.style.display = 'flex';
            input.classList.add('input-error');
            valid = false;
        } else {
            err.style.display = 'none';
            input.classList.remove('input-error');
        }
    });

    return valid;
}

// ── Main predict function ─────────────────────────────────────────────────────
async function predictActivity() {
    showGlobalAlert([]);
    document.getElementById('result').style.display = 'none';

    if (!validate()) return;

    const total  = parseFloat(document.getElementById('total_rental').value);
    const months = parseFloat(document.getElementById('active_months').value);
    const freq   = parseFloat(document.getElementById('rental_frequency').value);
    const intv   = parseFloat(document.getElementById('avg_interval').value);

    // Cross-field logic check
    const logicErrors = getLogicErrors(total, months, freq, intv);
    if (logicErrors.length > 0) {
        showGlobalAlert(logicErrors);
        return;
    }

    const btn = document.getElementById('btn-predict');
    btn.classList.add('loading');
    btn.textContent = 'Processing...';

    const data = { total_rental: total, rental_frequency: freq, avg_interval: intv };

    try {
        const response = await fetch('/api/kmeans-predict/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.error) {
            showGlobalAlert([`Server error: ${result.error}`]);
            return;
        }

        const prediction = result.prediction;
        const confidence = result.confidence;

        // ── Render result card ──
        const resultDiv = document.getElementById('result');
        resultDiv.className = `result ${prediction}`;
        resultDiv.style.display = 'block';
        document.getElementById('pred-value').textContent = prediction.toUpperCase();

        // Input summary stats
        document.getElementById('result-stats').innerHTML = `
            <div class="stat-cell">
                <div class="sv">${total}</div>
                <div class="sk">Total Rental</div>
            </div>
            <div class="stat-cell">
                <div class="sv">${months}</div>
                <div class="sk">Active Months</div>
            </div>
            <div class="stat-cell">
                <div class="sv">${freq.toFixed(1)}</div>
                <div class="sk">Freq / Month</div>
            </div>
            <div class="stat-cell">
                <div class="sv">${intv.toFixed(1)}</div>
                <div class="sk">Avg Interval (days)</div>
            </div>
        `;

        // Insight
        const ins = insights[prediction];
        document.getElementById('result-insight').innerHTML = `
            <div class="insight-title">${ins.title}</div>
            ${ins.text}
        `;

        // Recommendation
        const rec = recommendations[prediction];
        document.getElementById('recommendation').innerHTML = `
            <div class="rec-title">${rec.title}</div>
            <ul>${rec.items.map(i => `<li>${i}</li>`).join('')}</ul>
        `;

        // Confidence bars
        let confHtml = '';
        for (const [cls, pct] of Object.entries(confidence)) {
            confHtml += `
                <div class="conf-bar ${cls}">
                    <span class="bar-label">${cls}</span>
                    <div class="bar-track">
                        <div class="bar-fill" style="width:0%" data-pct="${pct}"></div>
                    </div>
                    <span class="bar-pct">${pct}%</span>
                </div>`;
        }
        document.getElementById('confidence').innerHTML = confHtml;

        // Animate bars after brief delay
        setTimeout(() => {
            document.querySelectorAll('.bar-fill').forEach(el => {
                el.style.width = el.dataset.pct + '%';
            });
        }, 80);

        resultDiv.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
        showGlobalAlert([`Failed to connect to the server: ${err.message}. Make sure the Django server is running.`]);
    } finally {
        btn.classList.remove('loading');
        btn.innerHTML = 'Predict Activity Level';
    }
}
