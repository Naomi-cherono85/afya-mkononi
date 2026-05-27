(() => {
    const form = document.getElementById('rem-form');
    if (!form) return;

    const formCard = document.getElementById('rem-form-card');
    const successCard = document.getElementById('rem-success-card');
    const submitBtn = document.getElementById('rem-submit');
    const errorBanner = document.getElementById('rem-form-error');
    const createAnotherBtn = document.getElementById('rem-create-another');

    const FIELDS = ['patient_name', 'reminder_type', 'reminder_message', 'scheduled_for'];

    const TYPE_LABELS = {
        MEDICATION: 'Medication',
        APPOINTMENT: 'Appointment',
        FOLLOWUP: 'Follow-up',
        OTHER: 'Other',
    };

    const STATUS_LABELS = {
        PENDING: 'Pending',
        SENT: 'Sent',
        CANCELLED: 'Cancelled',
    };

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

    const formatDateTime = (iso) => {
        if (!iso) return '';
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return iso;
        return d.toLocaleString(undefined, {
            weekday: 'short', day: 'numeric', month: 'short', year: 'numeric',
            hour: 'numeric', minute: '2-digit',
        });
    };

    const renderSuccess = (data) => {
        const set = (field, value) => {
            const el = successCard.querySelector(`[data-field="${field}"]`);
            if (el) el.textContent = value || '—';
        };
        set('patient_name', data.patient_name);
        set('reminder_type', TYPE_LABELS[data.reminder_type] || data.reminder_type);
        set('scheduled_for', formatDateTime(data.scheduled_for));
        set('reminder_message', data.reminder_message);
        set('status', STATUS_LABELS[data.status] || data.status);

        formCard.classList.add('hidden');
        successCard.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    };

    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        clearErrors();
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving…';

        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        const payload = Object.fromEntries(
            FIELDS.map((name) => [name, form.elements[name].value.trim()])
        );

        try {
            const res = await fetch('/api/reminders/', {
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
            submitBtn.textContent = 'Set reminder';
        }
    });

    createAnotherBtn?.addEventListener('click', () => {
        form.reset();
        clearErrors();
        successCard.classList.add('hidden');
        formCard.classList.remove('hidden');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
})();
