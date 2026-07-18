/*
 * Booking page enhancement (progressive — the form works without JS).
 *  - Smart date picker: min = today, hints for closed / next-available days.
 *  - Smart time picker: fetches real slots and disables past / fully-booked ones.
 *  - Live summary card that updates as the form is filled.
 *  - Loading state on submit.
 */
(() => {
    const form = document.getElementById('appt-form');
    if (!form) return;

    const dateInput = document.getElementById('id_preferred_date');
    const timeInput = document.getElementById('id_preferred_time');
    const doctorSel = document.getElementById('id_doctor');
    const clinicSel = document.getElementById('id_clinic');
    const typeSel = document.getElementById('id_appointment_type');

    const nativeTimeWrap = form.querySelector('[data-native-time]');
    const slotPicker = form.querySelector('[data-slot-picker]');
    const slotGrid = document.getElementById('slot-grid');
    const slotStatus = document.getElementById('slot-status');
    const dateHint = document.getElementById('date-hint');

    const submitBtn = document.getElementById('appt-submit');
    const spinner = document.getElementById('appt-spinner');

    const AVAIL_URL = '/api/appointments/availability/';
    const DAY_URL = '/api/appointments/day_availability/';
    const today = window.AFYA_TODAY || new Date().toISOString().slice(0, 10);

    // ---- helpers -----------------------------------------------------------
    const fmtDate = (iso) => {
        if (!iso) return '—';
        const d = new Date(iso + 'T00:00:00');
        if (Number.isNaN(d.getTime())) return iso;
        return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    };
    const fmtTime = (hhmm) => {
        if (!hhmm) return '—';
        const [h, m] = hhmm.split(':').map((v) => parseInt(v, 10));
        if (Number.isNaN(h)) return hhmm;
        const period = h >= 12 ? 'PM' : 'AM';
        const hour12 = ((h + 11) % 12) + 1;
        return `${hour12}:${String(m || 0).padStart(2, '0')} ${period}`;
    };
    const setSummary = (key, value) => {
        const el = form.closest('.grid')?.querySelector(`[data-summary="${key}"]`)
            || document.querySelector(`[data-summary="${key}"]`);
        if (el) el.textContent = value || '—';
    };
    const providerParams = () => {
        const p = new URLSearchParams();
        if (doctorSel && doctorSel.value) p.set('doctor', doctorSel.value);
        if (clinicSel && clinicSel.value) p.set('clinic', clinicSel.value);
        return p;
    };

    // ---- live summary ------------------------------------------------------
    const refreshSummary = () => {
        if (typeSel && typeSel.options) setSummary('type', typeSel.options[typeSel.selectedIndex]?.text);
        setSummary('date', fmtDate(dateInput ? dateInput.value : ''));
        setSummary('time', fmtTime(timeInput ? timeInput.value : ''));
        if (doctorSel && doctorSel.options) {
            const txt = doctorSel.value ? doctorSel.options[doctorSel.selectedIndex].text : 'Any available doctor';
            setSummary('doctor', txt);
        }
    };

    // ---- slot grid ---------------------------------------------------------
    const renderSlotMessage = (msg) => {
        slotGrid.innerHTML = `<p class="col-span-full text-sm text-foreground/55 py-2">${msg}</p>`;
    };

    const selectSlot = (value, btn) => {
        timeInput.value = value;
        slotGrid.querySelectorAll('button').forEach((b) => {
            b.classList.remove('bg-accent', 'text-white', 'border-accent');
            b.classList.add('border-border', 'text-foreground');
        });
        if (btn) {
            btn.classList.add('bg-accent', 'text-white', 'border-accent');
            btn.classList.remove('border-border', 'text-foreground');
        }
        // Clear any prior server-side time error once a fresh slot is picked.
        form.querySelectorAll('[data-time-error]').forEach((el) => el.remove());
        refreshSummary();
    };

    const loadSlots = async () => {
        if (!dateInput || !dateInput.value) {
            renderSlotMessage('Pick a date to see available times.');
            slotStatus.textContent = '';
            return;
        }
        slotStatus.textContent = 'Loading…';
        renderSlotMessage('Loading available times…');

        const params = providerParams();
        params.set('date', dateInput.value);
        try {
            const res = await fetch(`${AVAIL_URL}?${params.toString()}`, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
            });
            if (!res.ok) throw new Error('bad status');
            const data = await res.json();
            const slots = data.slots || [];

            if (slots.length === 0) {
                renderSlotMessage('The clinic is closed on this day. Please choose another date.');
                slotStatus.textContent = 'Closed';
                timeInput.value = '';
                refreshSummary();
                return;
            }

            const available = slots.filter((s) => s.available).length;
            slotStatus.textContent = available ? `${available} slot${available === 1 ? '' : 's'} free` : 'Fully booked';

            slotGrid.innerHTML = '';
            slots.forEach((slot) => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.textContent = slot.label;
                btn.dataset.value = slot.value;
                const base = 'px-2 py-2 rounded-soft border text-sm font-medium transition text-center';
                if (slot.available) {
                    btn.className = `${base} border-border text-foreground hover:border-accent hover:bg-accent-soft/60`;
                    btn.addEventListener('click', () => selectSlot(slot.value, btn));
                } else {
                    btn.className = `${base} border-border/60 text-foreground/30 bg-muted/40 cursor-not-allowed line-through`;
                    btn.disabled = true;
                    btn.setAttribute('aria-disabled', 'true');
                    btn.title = 'Unavailable';
                }
                slotGrid.appendChild(btn);
            });

            // Re-select the current time if it is still offered.
            if (timeInput.value) {
                const match = slotGrid.querySelector(`button[data-value="${timeInput.value}"]:not([disabled])`);
                if (match) selectSlot(timeInput.value, match);
                else timeInput.value = '';
            }
            refreshSummary();
        } catch (err) {
            renderSlotMessage('Could not load times. You can still type a time below.');
            slotStatus.textContent = '';
            // Fall back to the native time input so the user is never blocked.
            nativeTimeWrap.classList.remove('hidden');
        }
    };

    // ---- next-available-day hint ------------------------------------------
    const showNextAvailableHint = async () => {
        const start = new Date(today + 'T00:00:00');
        const end = new Date(start);
        end.setDate(end.getDate() + 30);
        const toISO = (d) => d.toISOString().slice(0, 10);
        const params = providerParams();
        params.set('start', toISO(start));
        params.set('end', toISO(end));
        try {
            const res = await fetch(`${DAY_URL}?${params.toString()}`, {
                headers: { Accept: 'application/json' },
                credentials: 'same-origin',
            });
            if (!res.ok) return;
            const data = await res.json();
            const next = (data.days || []).find((d) => d.has_slots);
            if (next) {
                dateHint.textContent = `Earliest availability: ${fmtDate(next.date)}.`;
                dateHint.classList.remove('hidden');
            }
        } catch (err) { /* hint is best-effort */ }
    };

    // ---- init --------------------------------------------------------------
    // Enhance only when the availability API is reachable in the browser.
    if (dateInput) {
        dateInput.min = today;
        // Switch from the native time field to the slot grid.
        nativeTimeWrap.classList.add('hidden');
        slotPicker.classList.remove('hidden');
        renderSlotMessage('Pick a date to see available times.');

        dateInput.addEventListener('change', () => { loadSlots(); refreshSummary(); });
        [doctorSel, clinicSel].forEach((sel) => sel && sel.addEventListener('change', () => { loadSlots(); showNextAvailableHint(); }));
        if (typeSel) typeSel.addEventListener('change', refreshSummary);

        if (dateInput.value) loadSlots();
        showNextAvailableHint();
    }
    refreshSummary();

    // ---- submit loading state ---------------------------------------------
    form.addEventListener('submit', () => {
        submitBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');
        submitBtn.querySelector('span').textContent = 'Booking…';
    });
})();
