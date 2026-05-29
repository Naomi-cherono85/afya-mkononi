(() => {
    const form = document.getElementById('chat-form');
    if (!form) return;

    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const sendIcon = sendBtn ? sendBtn.querySelector('[data-send-icon]') : null;
    const sendSpinner = sendBtn ? sendBtn.querySelector('[data-send-spinner]') : null;
    const thread = document.getElementById('chat-thread');
    const intro = document.getElementById('chat-intro');
    const userTpl = document.getElementById('chat-user-bubble');
    const aiTpl = document.getElementById('chat-ai-bubble');
    const errTpl = document.getElementById('chat-error-bubble');
    const typingTpl = document.getElementById('chat-typing-bubble');
    const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');

    let sessionId = null;
    let pending = false;

    const ESC = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
    const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) => ESC[c]);

    const renderInline = (s) => {
        s = s.replace(/\*\*([^*\n]+?)\*\*/g, '<strong>$1</strong>');
        s = s.replace(/(^|[\s(>])\*([^*\n]+?)\*(?=[\s).,!?;:<]|$)/g, '$1<em>$2</em>');
        return s;
    };

    const renderMarkdown = (raw) => {
        const escaped = escapeHtml(raw.trim());
        const blocks = escaped.split(/\n{2,}/);

        return blocks.map((block) => {
            const lines = block.split('\n');

            if (lines.every((l) => /^\s*\d+\.\s+/.test(l))) {
                const items = lines
                    .map((l) => `<li>${renderInline(l.replace(/^\s*\d+\.\s+/, ''))}</li>`)
                    .join('');
                return `<ol class="list-decimal pl-5 space-y-1 my-2">${items}</ol>`;
            }

            if (lines.every((l) => /^\s*[-*]\s+/.test(l))) {
                const items = lines
                    .map((l) => `<li>${renderInline(l.replace(/^\s*[-*]\s+/, ''))}</li>`)
                    .join('');
                return `<ul class="list-disc pl-5 space-y-1 my-2">${items}</ul>`;
            }

            return `<p class="mb-2 last:mb-0">${renderInline(lines.join('<br>'))}</p>`;
        }).join('');
    };

    const hideIntro = () => {
        if (intro && !intro.classList.contains('hidden')) {
            intro.classList.add('hidden');
        }
    };

    const appendUser = (text) => {
        const node = userTpl.content.firstElementChild.cloneNode(true);
        node.querySelector('[data-content]').textContent = text;
        thread.appendChild(node);
        thread.scrollTop = thread.scrollHeight;
    };

    const appendAi = (text) => {
        const node = aiTpl.content.firstElementChild.cloneNode(true);
        const slot = node.querySelector('[data-content]');
        slot.classList.remove('whitespace-pre-line');
        slot.innerHTML = renderMarkdown(text);
        thread.appendChild(node);
        thread.scrollTop = thread.scrollHeight;
    };

    const appendError = (text) => {
        const node = errTpl.content.firstElementChild.cloneNode(true);
        node.querySelector('[data-content]').textContent = text;
        thread.appendChild(node);
        thread.scrollTop = thread.scrollHeight;
    };

    const showTyping = () => {
        const node = typingTpl.content.firstElementChild.cloneNode(true);
        node.dataset.typing = '1';
        thread.appendChild(node);
        thread.scrollTop = thread.scrollHeight;
        return node;
    };

    const setPending = (state) => {
        pending = state;
        sendBtn.disabled = state;
        input.disabled = state;
        if (sendIcon && sendSpinner) {
            sendIcon.classList.toggle('hidden', state);
            sendSpinner.classList.toggle('hidden', !state);
        }
    };

    const FRIENDLY_ERROR = 'Sorry, the assistant is temporarily unavailable. Please try again in a moment.';

    const sendMessage = async (message) => {
        const trimmed = message.trim();
        if (!trimmed || pending) return;

        hideIntro();
        appendUser(trimmed);
        input.value = '';
        setPending(true);

        const typingNode = showTyping();

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
                appendAi(data.reply || '(no reply)');
            } else {
                let detail = FRIENDLY_ERROR;
                if (res.status === 400) {
                    try {
                        const body = await res.json();
                        if (body.message) {
                            detail = Array.isArray(body.message) ? body.message.join(' ') : body.message;
                        }
                    } catch (_) {
                        /* ignore body parse errors */
                    }
                }
                appendError(detail);
            }
        } catch (err) {
            typingNode.remove();
            appendError(FRIENDLY_ERROR);
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
            if (pending) return;
            const prompt = chip.dataset.prompt || chip.textContent.trim();
            input.value = prompt;
            sendMessage(prompt);
        });
    });

    input.focus();
})();
