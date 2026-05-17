# Afya Mkononi — Branding

> Locked color palette for the project. Use the exact hex values across UI, mockups, demo video, LinkedIn graphics, and any visual asset. No "close enough" substitutes.

---

## Color palette

| Role | Use for | Hex | CSS variable |
|---|---|---|---|
| **Primary Blue** | Main brand color, CTAs, links | `#3b82f6` | `hsl(var(--primary))` |
| **Accent Green** | Success states, highlights, speech bubbles | `#10b981` | `hsl(var(--accent))` |
| **Background** | Page backgrounds, cards | `#ffffff` | `hsl(var(--background))` |
| **Foreground** | Primary text, headings | `#0f172a` | `hsl(var(--foreground))` |
| **Muted** | Secondary backgrounds, subtle elements | `#f1f5f9` | `hsl(var(--muted))` |
| **Border** | Borders, dividers, outlines | `#e2e8f0` | — |

---

## Tailwind config

When `tailwind.config.js` is set up in Week 3, extend the theme with these tokens so the team can write `bg-primary`, `text-foreground`, `border-border`, etc., instead of raw hex values.

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary:    '#3b82f6',
        accent:     '#10b981',
        background: '#ffffff',
        foreground: '#0f172a',
        muted:      '#f1f5f9',
        border:     '#e2e8f0',
      },
    },
  },
};
```

For a CSS-variable setup (recommended if dark mode comes later), define in `base.html` or a global stylesheet:

```css
:root {
  --primary:    221 83% 53%;   /* #3b82f6 in HSL */
  --accent:     160 84% 39%;   /* #10b981 in HSL */
  --background: 0 0% 100%;     /* #ffffff */
  --foreground: 222 47% 11%;   /* #0f172a */
  --muted:      210 40% 96%;   /* #f1f5f9 */
  --border:     214 32% 91%;   /* #e2e8f0 */
}
```

---

## Usage rules

**Primary Blue (`#3b82f6`)**
- Brand logo / wordmark
- All primary CTAs ("Book Appointment", "Send", "Set Reminder")
- Links inside content
- User message bubbles in chat
- Active nav states

**Accent Green (`#10b981`)**
- Success toasts ("Appointment booked", "Reminder saved")
- Confirmation badges on Appointment status (`CONFIRMED`, `COMPLETED`)
- Highlight strokes on important UI moments
- **Not for CTAs.** Green is reward, not action.

**Background (`#ffffff`)**
- Page background
- Card surfaces
- Form input backgrounds

**Foreground (`#0f172a`)**
- Body text
- Headings
- Icons in default state

**Muted (`#f1f5f9`)**
- AI message bubbles in chat
- Disabled inputs
- Section dividers' fill (when shaded)
- Hover states on subtle elements

**Border (`#e2e8f0`)**
- All borders on cards, inputs, dividers
- 1px default weight

---

## Chat UI mapping (the most important screen)

| Element | Color |
|---|---|
| Page background | Background `#ffffff` |
| Header / navbar | Background with bottom Border |
| Safety disclaimer banner | Muted background, Foreground text, Primary left-border (4px) |
| User message bubble | Primary background, white text |
| AI message bubble | Muted background, Foreground text |
| Suggested-prompt chips | Border outline, Foreground text, Primary on hover |
| Send button | Primary background, white text |
| Loading indicator | Primary (the spinning element) |
| Emergency escalation message | Accent Green left-border (4px) + Muted background |

---

## Off-brand things to avoid

- ❌ Red anywhere in the standard UI. Red signals "danger" / "error" — and this is a healthcare product where the *real* emergency escalation language must stand out. Reserve red only for `ERROR` toast states if absolutely needed.
- ❌ Gradients. The palette is flat. Keep it flat.
- ❌ Other blues. `#3b82f6` is the only blue. Do not use `#2563eb`, `#1e40af`, or any other shade as a "darker primary."
- ❌ Mixing the green with the blue as a duotone. They live in different roles.

---

## LinkedIn graphics

For Canva or any post graphic:
- **Background:** White
- **Hero text color:** Foreground `#0f172a`
- **Brand accent / underline / chip:** Primary `#3b82f6`
- **Success / "shipped" badges:** Accent `#10b981`
- **Borders / dividers:** Border `#e2e8f0`
- **Avoid:** Stock photo overlays, gradient text, drop shadows. Keep it clean and product-y.
