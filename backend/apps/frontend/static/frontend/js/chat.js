(() => {
    const form = document.getElementById('chat-form');
    if (!form) return;

    const input = document.getElementById('chat-input');
    const attachBtn = document.getElementById('chat-attach');
    const fileInput = document.getElementById('chat-file');
    const attachPreview = document.getElementById('attachment-preview');
    const attachName = document.getElementById('attachment-name');
    const attachRemove = document.getElementById('attachment-remove');
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
    let selectedFile = null;

    // Mirror the server-side attachment policy (apps/chatbot/models.py).
    const ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'pdf', 'docx', 'txt'];
    const IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp'];
    const MAX_FILE_BYTES = 10 * 1024 * 1024; // 10 MB
    const extOf = (name) => (name.split('.').pop() || '').toLowerCase();

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

    // Build the rendered attachment for a user bubble.
    // `att` = { url, name, is_image }.
    // Images and PDFs preview inline (no download needed); other docs show a
    // labelled link that opens in a new tab.
    const buildAttachment = (att) => {
        if (att.is_image) {
            const link = document.createElement('a');
            link.href = att.url;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            const img = document.createElement('img');
            img.src = att.url;
            img.alt = att.name;
            img.className = 'rounded-lg max-h-56 max-w-full object-contain';
            link.appendChild(img);
            return link;
        }

        const wrapper = document.createElement('div');
        wrapper.className = 'flex flex-col gap-2';

        const link = document.createElement('a');
        link.href = att.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.className = 'flex items-center gap-2 px-3 py-2 rounded-soft bg-background/70 border border-accent-tint hover:bg-background transition';
        link.innerHTML =
            '<svg class="w-5 h-5 text-accent shrink-0" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">' +
            '<path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m.75 12 3 3m0 0 3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z"/></svg>' +
            '<span class="truncate"></span>';
        link.querySelector('span').textContent = att.name;
        wrapper.appendChild(link);

        // PDFs get an inline, toggleable preview so they can be read without downloading.
        if (extOf(att.name) === 'pdf') {
            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'self-start text-xs font-medium text-accent hover:underline';
            toggle.textContent = 'Preview PDF';
            const frame = document.createElement('iframe');
            frame.src = att.url;
            frame.title = att.name;
            frame.className = 'hidden w-full h-80 rounded-lg border border-border bg-white';
            toggle.addEventListener('click', () => {
                const nowHidden = frame.classList.toggle('hidden');
                toggle.textContent = nowHidden ? 'Preview PDF' : 'Hide preview';
                if (!nowHidden) thread.scrollTop = thread.scrollHeight;
            });
            wrapper.appendChild(toggle);
            wrapper.appendChild(frame);
        }
        return wrapper;
    };

    const appendUser = (text, attachments) => {
        removeFollowups();  // the previous turn's suggestions no longer apply
        const node = userTpl.content.firstElementChild.cloneNode(true);
        const slot = node.querySelector('[data-content]');
        if (text) {
            slot.textContent = text;
        } else {
            slot.remove();
        }
        const attSlot = node.querySelector('[data-attachment]');
        const list = (attachments || []).filter((a) => a && a.url);
        if (list.length) {
            attSlot.classList.remove('hidden');
            attSlot.classList.add('flex', 'flex-col', 'gap-2');
            list.forEach((att) => attSlot.appendChild(buildAttachment(att)));
        } else {
            attSlot.remove();
        }
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

    // ---- Suggested follow-up chips (shown under the latest AI reply) ----

    const FOLLOWUP_SUGGESTIONS = [
        'Tell me more',
        'What should I do?',
        'Should I see a doctor?',
        'Prevention tips',
        'Related symptoms',
    ];
    // Never nudge further self-exploration on emergency or refused replies —
    // the safe action there is to seek professional/emergency care.
    const SUPPRESS_CHIP_CATEGORIES = ['EMERGENCY', 'REFUSED'];

    const removeFollowups = () => {
        thread.querySelectorAll('[data-followups]').forEach((el) => el.remove());
    };

    const showFollowups = (safetyCategory) => {
        removeFollowups();
        if (SUPPRESS_CHIP_CATEGORIES.includes(safetyCategory)) return;
        const group = document.createElement('div');
        group.dataset.followups = '1';
        group.className = 'flex flex-wrap gap-2 ml-12';
        FOLLOWUP_SUGGESTIONS.forEach((label) => {
            const chip = document.createElement('button');
            chip.type = 'button';
            chip.className = 'followup-chip text-xs font-medium px-3 py-1.5 rounded-pill border border-border bg-background text-foreground/75 hover:border-accent hover:bg-accent-soft/60 hover:text-accent transition';
            chip.textContent = label;
            chip.addEventListener('click', () => {
                if (pending) return;
                sendMessage(label);
            });
            group.appendChild(chip);
        });
        thread.appendChild(group);
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
        if (attachBtn) attachBtn.disabled = state;
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
            let lastAiSafety = null;
            (data.messages || []).forEach((m) => {
                if (m.sender_type === 'USER') {
                    appendUser(m.message_content, m.attachments || []);
                } else if (m.sender_type === 'AI') {
                    appendAi(m.message_content);
                    lastAiSafety = m.safety_category;
                }
            });
            // Offer follow-ups under the most recent AI reply only.
            if (lastAiSafety !== null) showFollowups(lastAiSafety);
            setActive(id);
        } catch (err) {
            loading.classList.add('hidden');
            loading.classList.remove('flex');
            appendError('Could not load this conversation. Please try again.');
        }
    };

    // ---- Inline rename (ChatGPT-style pencil) ----

    const commitRename = async (id, value, restore) => {
        const trimmed = value.trim();
        if (!trimmed) {
            restore();
            return;
        }
        try {
            const res = await fetch(`/api/chat/conversations/${id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfInput.value,
                },
                credentials: 'same-origin',
                body: JSON.stringify({ title: trimmed }),
            });
            if (res.ok) {
                const data = await res.json();
                const newTitle = data.display_title || trimmed;
                restore(newTitle);
                if (id === conversationId && titleEl) titleEl.textContent = newTitle;
            } else {
                restore();
            }
        } catch (err) {
            restore();
        }
    };

    const startRename = (item) => {
        const span = titleSpan(item);
        if (!span || item.querySelector('input[data-rename]')) return;

        const id = item.dataset.conversationId;
        const input = document.createElement('input');
        input.type = 'text';
        input.dataset.rename = '1';
        input.value = span.textContent;
        input.maxLength = 120;
        input.className = 'w-full text-sm font-medium text-foreground bg-background border border-accent rounded px-1.5 py-0.5 focus:outline-none focus:ring-2 focus:ring-accent/20';

        span.classList.add('hidden');
        span.parentNode.insertBefore(input, span);
        input.focus();
        input.select();

        let done = false;
        const restore = (newText) => {
            if (done) return;
            done = true;
            if (newText) span.textContent = newText;
            span.classList.remove('hidden');
            input.remove();
        };

        input.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                commitRename(id, input.value, restore);
            } else if (event.key === 'Escape') {
                event.preventDefault();
                restore();
            }
        });
        input.addEventListener('blur', () => commitRename(id, input.value, restore));
    };

    const bindConversationItem = (item) => {
        item.addEventListener('click', (event) => {
            // Clicks on the pencil or the rename input must not open the chat.
            if (event.target.closest('.conv-rename') || event.target.closest('input[data-rename]')) return;
            openConversation(item.dataset.conversationId);
        });
        const renameBtn = item.querySelector('.conv-rename');
        if (renameBtn) {
            renameBtn.addEventListener('click', (event) => {
                event.stopPropagation();
                startRename(item);
            });
        }
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

    // ---- Attachment picking ----

    const clearAttachment = () => {
        selectedFile = null;
        if (fileInput) fileInput.value = '';
        if (attachPreview) {
            attachPreview.classList.add('hidden');
            attachPreview.classList.remove('flex');
        }
        if (attachName) attachName.textContent = '';
    };

    const showAttachment = (file) => {
        selectedFile = file;
        if (attachName) attachName.textContent = file.name;
        if (attachPreview) {
            attachPreview.classList.remove('hidden');
            attachPreview.classList.add('flex');
        }
    };

    if (attachBtn) {
        attachBtn.addEventListener('click', () => {
            if (pending) return;
            fileInput.click();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', () => {
            const file = fileInput.files && fileInput.files[0];
            if (!file) return;
            if (!ALLOWED_EXTENSIONS.includes(extOf(file.name))) {
                appendError('Unsupported file type. Allowed: images (JPG, PNG, WEBP), PDF, DOCX, or TXT.');
                clearAttachment();
                return;
            }
            if (file.size > MAX_FILE_BYTES) {
                appendError('That file is too large. The maximum size is 10 MB.');
                clearAttachment();
                return;
            }
            showAttachment(file);
        });
    }

    if (attachRemove) attachRemove.addEventListener('click', clearAttachment);

    // ---- Sending ----

    const FRIENDLY_ERROR = 'Sorry, the assistant is temporarily unavailable. Please try again in a moment.';

    const sendMessage = async (message) => {
        const trimmed = message.trim();
        const file = selectedFile;
        // Need either text or a file to send.
        if ((!trimmed && !file) || pending) return;

        hideIntro();

        // Render the user's bubble immediately, including a local preview of the
        // attachment (object URL for images, filename chip otherwise).
        const localAttachments = file ? [{
            name: file.name,
            is_image: IMAGE_EXTENSIONS.includes(extOf(file.name)),
            url: URL.createObjectURL(file),
        }] : [];
        appendUser(trimmed, localAttachments);

        input.value = '';
        setPending(true);

        const typingNode = showTyping();

        // Multipart so the file rides along with the message fields.
        const body = new FormData();
        if (trimmed) body.append('message', trimmed);
        if (file) body.append('attachment', file);
        if (conversationId) body.append('conversation_id', conversationId);

        try {
            const res = await fetch('/api/chat/', {
                method: 'POST',
                headers: {
                    // No Content-Type: the browser sets the multipart boundary.
                    'Accept': 'application/json',
                    'X-CSRFToken': csrfInput.value,
                },
                credentials: 'same-origin',
                body,
            });

            typingNode.remove();

            if (res.ok) {
                const data = await res.json();
                if (data.conversation_id) conversationId = data.conversation_id;
                if (data.title && titleEl) titleEl.textContent = data.title;
                appendAi(data.reply || '(no reply)');
                showFollowups(data.safety_category);
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
            clearAttachment();
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
