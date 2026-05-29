(() => {
    const form = document.getElementById('chat-form');
    if (!form) return;

    const input = document.getElementById('chat-input');
    const sendBtn = document.getElementById('chat-send');
    const sendIcon = sendBtn ? sendBtn.querySelector('[data-send-icon]') : null;
    const sendSpinner = sendBtn ? sendBtn.querySelector('[data-send-spinner]') : null;
    const thread = document.getElementById('chat-thread');
    const intro = document.getElementById('chat-intro');
    const loading = document.getElementById('chat-loading');
    const titleEl = document.getElementById('chat-title');
    const userTpl = document.getElementById('chat-user-bubble');
    const aiTpl = document.getElementById('chat-ai-bubble');
    const errTpl = document.getElementById('chat-error-bubble');
    const typingTpl = document.getElementById('chat-typing-bubble');
    const convItemTpl = document.getElementById('conversation-item-template');
    const convPanel = document.getElementById('conversation-panel');
    const convList = document.getElementById('conversation-list');
    const convEmpty = document.getElementById('conversation-empty');
    const csrfInput = document.querySelector('input[name=csrfmiddlewaretoken]');

    let conversationId = null;
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

    const hideIntro = () => intro && intro.classList.add('hidden');
    const showIntro = () => intro && intro.classList.remove('hidden');

    // Remove all rendered bubbles, keeping the intro and loading placeholders.
    const clearThread = () => {
        Array.from(thread.children).forEach((child) => {
            if (child !== intro && child !== loading) child.remove();
        });
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

    // ---- Conversation history sidebar ----

    const titleSpan = (item) => item.querySelector('[data-title]') || item.querySelector('span');

    const setActive = (id) => {
        convList.querySelectorAll('.conversation-item').forEach((item) => {
            const isActive = item.dataset.conversationId === id;
            item.classList.toggle('bg-accent-soft', isActive);
            titleSpan(item).classList.toggle('text-accent', isActive);
        });
    };

    const formatNow = () => {
        const d = new Date();
        return d.toLocaleDateString(undefined, { day: 'numeric', month: 'short' }) +
            ', ' + d.toLocaleTimeString(undefined, { hour: 'numeric', minute: '2-digit' });
    };

    // Insert a new conversation item at the top, or update an existing one.
    const upsertConversation = (id, title) => {
        if (convEmpty) convEmpty.classList.add('hidden');
        let item = convList.querySelector(`[data-conversation-id="${id}"]`);
        if (!item) {
            item = convItemTpl.content.firstElementChild.cloneNode(true);
            item.dataset.conversationId = id;
            bindConversationItem(item);
        } else {
            item.remove();
        }
        titleSpan(item).textContent = title;
        const timeSpan = item.querySelector('[data-time]') || item.querySelectorAll('span')[1];
        if (timeSpan) timeSpan.textContent = formatNow();
        convList.prepend(item);
        setActive(id);
    };

    const openConversation = async (id) => {
        if (pending || id === conversationId) {
            closeMobilePanel();
            return;
        }
        closeMobilePanel();
        clearThread();
        hideIntro();
        loading.classList.remove('hidden');
        loading.classList.add('flex');
        thread.scrollTop = 0;

        try {
            const res = await fetch(`/api/chat/conversations/${id}/`, {
                headers: { 'Accept': 'application/json' },
                credentials: 'same-origin',
            });
            loading.classList.add('hidden');
            loading.classList.remove('flex');

            if (!res.ok) {
                appendError('Could not load this conversation. Please try again.');
                return;
            }
            const data = await res.json();
            conversationId = data.id;
            if (titleEl) titleEl.textContent = data.display_title || 'Chat Assistant';
            clearThread();
            (data.messages || []).forEach((m) => {
                if (m.sender_type === 'USER') appendUser(m.message_content);
                else if (m.sender_type === 'AI') appendAi(m.message_content);
            });
            setActive(id);
        } catch (err) {
            loading.classList.add('hidden');
            loading.classList.remove('flex');
            appendError('Could not load this conversation. Please try again.');
        }
    };

    const bindConversationItem = (item) => {
        item.addEventListener('click', () => openConversation(item.dataset.conversationId));
    };

    convList.querySelectorAll('.conversation-item').forEach(bindConversationItem);

    const startNewChat = () => {
        conversationId = null;
        clearThread();
        showIntro();
        if (titleEl) titleEl.textContent = 'Chat Assistant';
        setActive(null);
        closeMobilePanel();
        input.focus();
    };

    // ---- Mobile history panel toggle ----

    const openMobilePanel = () => convPanel && convPanel.classList.add('!flex');
    const closeMobilePanel = () => convPanel && convPanel.classList.remove('!flex');
    const toggleMobilePanel = () => convPanel && convPanel.classList.toggle('!flex');

    const historyToggle = document.getElementById('history-toggle');
    if (historyToggle) historyToggle.addEventListener('click', toggleMobilePanel);

    document.getElementById('new-chat-btn')?.addEventListener('click', startNewChat);
    document.getElementById('new-chat-btn-mobile')?.addEventListener('click', startNewChat);

    // ---- Sending ----

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
                    ...(conversationId ? { conversation_id: conversationId } : {}),
                }),
            });

            typingNode.remove();

            if (res.ok) {
                const data = await res.json();
                if (data.conversation_id) conversationId = data.conversation_id;
                if (data.title && titleEl) titleEl.textContent = data.title;
                appendAi(data.reply || '(no reply)');
                if (conversationId) upsertConversation(conversationId, data.title || 'New conversation');
            } else {
                let detail = FRIENDLY_ERROR;
                if (res.status === 400) {
                    try {
                        const body = await res.json();
                        if (body.message) {
                            detail = Array.isArray(body.message) ? body.message.join(' ') : body.message;
                        }
                    } catch (_) { /* ignore body parse errors */ }
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
