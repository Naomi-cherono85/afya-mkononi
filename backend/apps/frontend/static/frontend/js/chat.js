(() => {
    const form = document.getElementById('chat-form');
    if (!form) return;

    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const thread = document.getElementById('chat-thread');
    const intro = document.getElementById('chat-intro');
    const userTpl = document.getElementById('chat-user-bubble');
    const aiTpl = document.getElementById('chat-ai-bubble');
    const errTpl = document.getElementById('chat-error-bubble');
    const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');

    let sessionId = null;
    let pending = false;

    const hideIntro = () => {
        if (intro && !intro.classList.contains('hidden')) {
            intro.classList.add('hidden');
        }
    };

    const appendBubble = (template, text) => {
        const node = template.content.firstElementChild.cloneNode(true);
        const slot = node.querySelector('[data-content]');
        slot.textContent = text;
        thread.appendChild(node);
        thread.scrollTop = thread.scrollHeight;
        return slot;
    };

    const setPending = (state) => {
        pending = state;
        sendBtn.disabled = state;
        input.disabled = state;
    };

    const sendMessage = async (message) => {
        const trimmed = message.trim();
        if (!trimmed || pending) return;

        hideIntro();
        appendBubble(userTpl, trimmed);
        input.value = '';
        setPending(true);

        const typingNode = aiTpl.content.firstElementChild.cloneNode(true);
        typingNode.querySelector('[data-content]').textContent = 'Typing…';
        typingNode.dataset.typing = '1';
        thread.appendChild(typingNode);
        thread.scrollTop = thread.scrollHeight;

        try {
            const res = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfInput.value,
                },
                credentials: 'same-origin',
                body: JSON.stringify({
                    message: trimmed,
                    ...(sessionId ? { session_id: sessionId } : {}),
                }),
            });

            typingNode.remove();

            if (res.ok) {
                const data = await res.json();
                if (data.session_id) sessionId = data.session_id;
                appendBubble(aiTpl, data.reply || '(no reply)');
            } else {
                let detail = `Request failed (HTTP ${res.status})`;
                try {
                    const body = await res.json();
                    if (body.message) detail = Array.isArray(body.message) ? body.message.join(' ') : body.message;
                } catch (_) {
                    /* ignore body parse errors */
                }
                appendBubble(errTpl, detail);
            }
        } catch (err) {
            typingNode.remove();
            appendBubble(errTpl, 'Network error — please check your connection and try again.');
        } finally {
            setPending(false);
            input.focus();
        }
    };

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        sendMessage(input.value);
    });

    document.querySelectorAll('.chat-chip').forEach((chip) => {
        chip.addEventListener('click', () => {
            const prompt = chip.dataset.prompt || chip.textContent.trim();
            input.value = prompt;
            sendMessage(prompt);
        });
    });

    input.focus();
})();
