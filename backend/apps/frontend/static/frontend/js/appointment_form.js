(() => {
    const form = document.getElementById('appt-form');
    if (!form) return;

    const formCard = document.getElementById('appt-form-card');
    const successCard = document.getElementById('appt-success-card');
    const submitBtn = document.getElementById('appt-submit');
    const errorBanner = document.getElementById('appt-form-error');
    const bookAnotherBtn = document.getElementById('appt-book-another');

    const FIELDS = ['patient_name', 'phone_number', 'email', 'preferred_date', 'preferred_time', 'reason_for_visit'];

    const clearErrors = () => {
        errorBanner.classList.add('hidden');
        errorBanner.textContent = '';
        FIELDS.forEach((name) => {
            const el = form.querySelector(`[data-error-for="${name}"]`);
            if (el) {
                el.classList.add('hidden');
                el.textContent = '';
            }
        });
    };

    const showFieldErrors = (errors) => {
        Object.entries(errors).forEach(([name, messages]) => {
            const el = form.querySelector(`[data-error-for="${name}"]`);
            if (el) {
                el.textContent = Array.isArray(messages) ? messages.join(' ') : String(messages);
                el.classList.remove('hidden');
            }
        });
    };

    const showBanner = (message) => {
        errorBanner.textContent = message;
        errorBanner.classList.remove('hidden');
    };

    const formatDate = (iso) => {
        if (!iso) return '';
        const d = new Date(iso + 'T00:00:00');
        if (Number.isNaN(d.getTime())) return iso;
        return d.toLocaleDateString(undefined, { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    };

    const formatTime = (hhmm) => {
        if (!hhmm) return '';
        const [h, m] = hhmm.split(':').map((v) => parseInt(v, 10));
        if (Number.isNaN(h)) return hhmm;
        const period = h >= 12 ? 'PM' : 'AM';
        const hour12 = ((h + 11) % 12) + 1;
        return `${hour12}:${String(m || 0).padStart(2, '0')} ${period}`;
    };

    const renderSuccess = (data) => {
        const set = (field, value) => {
            const el = successCard.querySelector(`[data-field="${field}"]`);
            if (el) el.textContent = value || '—';
        };
        set('patient_name', data.patient_name);
        set('phone_number', data.phone_number);
        set('preferred_date', formatDate(data.preferred_date));
        set('preferred_time', formatTime(data.preferred_time));
        set('reason_for_visit', data.reason_for_visit);
        set('status', data.status === 'PENDING' ? 'Pending confirmation' : data.status);

        formCard.classList.add('hidden');
        successCard.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearErrors();
        submitBtn.disabled = true;
        submitBtn.textContent = 'Booking…';

        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        const payload = Object.fromEntries(
            FIELDS.map((name) => [name, form.elements[name].value.trim()])
        );
        if (!payload.email) delete payload.email;

        try {
            const res = await fetch('/api/appointments/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'same-origin',
                body: JSON.stringify(payload),
            });

            if (res.status === 201) {
                const data = await res.json();
                renderSuccess(data);
                return;
            }

            if (res.status === 400) {
                const errors = await res.json();
                showFieldErrors(errors);
                showBanner('Please correct the highlighted fields and try again.');
                return;
            }

            showBanner(`Something went wrong (HTTP ${res.status}). Please try again.`);
        } catch (err) {
            showBanner('Network error — please check your connection and try again.');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Book appointment';
        }
    });

    bookAnotherBtn?.addEventListener('click', () => {
        form.reset();
        clearErrors();
        successCard.classList.add('hidden');
        formCard.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
