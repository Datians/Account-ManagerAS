from datetime import date, timedelta
import io
import requests
from flask import current_app
from ..models import Account

# (opcional) para gráfico
try:
    import matplotlib.pyplot as plt
except Exception:  # si no está instalado, no pasa nada
    plt = None


# ---------- helpers visuales ----------

def _days_text(d):
    if d == 0:  return "hoy"
    if d == 1:  return "mañana"
    if d > 1:   return f"en {d} días"
    return f"hace {-d}"

def _pushover_enabled(cfg):
    return bool(cfg.get("PUSHOVER_USER_KEY") and cfg.get("PUSHOVER_API_TOKEN"))

def _send_pushover(message, title, cfg, *, priority=0, sound=None, html=False, url=None, url_title=None, attachment_bytes=None):
    if not _pushover_enabled(cfg):
        return False, "Pushover no configurado"

    data = {
        "token": cfg.get("PUSHOVER_API_TOKEN"),
        "user": cfg.get("PUSHOVER_USER_KEY"),
        "message": message,
        "title": title,
        "priority": priority,
    }
    if html:
        data["html"] = 1
    if sound:
        data["sound"] = sound
    device = cfg.get("PUSHOVER_DEVICE")
    if device:
        data["device"] = device
    if url:
        data["url"] = url
        if url_title:
            data["url_title"] = url_title

    files = None
    if attachment_bytes is not None:
        files = {"attachment": ("resumen.png", attachment_bytes, "image/png")}

    resp = requests.post("https://api.pushover.net/1/messages.json", data=data, files=files, timeout=15)
    try:
        resp.raise_for_status()
        return True, "OK"
    except Exception as e:
        return False, str(e)

def _chunk_lines(lines, char_limit):
    pages, cur, cur_len = [], [], 0
    for line in lines:
        add = line + "\n"
        if cur_len + len(add) > char_limit and cur:
            pages.append("\n".join(cur).rstrip())
            cur, cur_len = [line], len(add)
        else:
            cur.append(line); cur_len += len(add)
    if cur:
        pages.append("\n".join(cur).rstrip())
    return pages


# ---------- consultas ----------

def _query_sections(today, window_days):
    soon_limit = today + timedelta(days=window_days)

    q_today = Account.query.filter(Account.end_date == today).all()
    q_tomorrow = Account.query.filter(Account.end_date == today + timedelta(days=1)).all()
    q_soon = Account.query.filter(
        Account.end_date >= today + timedelta(days=2),
        Account.end_date <= soon_limit
    ).all()

    def rows(qs):
        out = []
        for a in qs:
            d = (a.end_date - today).days if a.end_date else None
            out.append({
                "id": a.id,
                "platform": a.platform,
                "username": a.username,
                "password": a.password or "",
                "client": a.client.name if a.client else "",
                "provider": a.provider.name if a.provider else "",
                "end_date": a.end_date.isoformat() if a.end_date else "",
                "d": d
            })
        return out

    return {"hoy": rows(q_today), "mañana": rows(q_tomorrow), "soon": rows(q_soon)}

def _summary_counts(sections):
    return {k: len(v) for k, v in sections.items()}


# ---------- render con HTML + emojis ----------

def _group_if_needed(items, group_by_provider: bool):
    if not group_by_provider:
        return {"": items}
    grouped = {}
    for r in items:
        key = r["provider"] or "(sin proveedor)"
        grouped.setdefault(key, []).append(r)
    return grouped

def _render_detail_html(title, items, cfg, include_passwords, max_items, group_by_provider):
    """
    Devuelve (title, [pages]) usando HTML (negritas, links).
    Cada item incluye un link Editar si APP_BASE_URL está configurado.
    """
    base = cfg.get("APP_BASE_URL", "")
    lines = [f"<b>— {title} —</b>"]
    shown = 0

    grouped = _group_if_needed(items, group_by_provider)
    for prov, rows in grouped.items():
        if prov:
            lines.append(f"<u>{prov}</u>")
        for r in rows:
            if shown >= max_items:
                break
            # CTA editar
            edit_url = f"{base}/accounts/{r['id']}/edit" if base else None
            head = f"• <b>{r['platform']}</b> | <a href='mailto:{r['username']}'>{r['username']}</a> | {r['client']}"
            if edit_url:
                head += f" | <a href='{edit_url}'>Editar</a>"
            lines.append(head)

            extra = f"&nbsp;&nbsp;⏳ {_days_text(r['d'])} &nbsp;|&nbsp; Vence {r['end_date']}"
            if include_passwords and r["password"]:
                extra += f" &nbsp;|&nbsp; 🔑 <code>{r['password']}</code>"
            lines.append(extra)
            shown += 1
        if prov and shown < max_items:
            lines.append("")  # separación entre grupos

        if shown >= max_items:
            break

    if len(items) > shown:
        lines.append(f"<i>+ {len(items) - shown} más…</i>")
    return lines

def _build_summary_chart_bytes(counts, today):
    if plt is None:
        return None
    fig, ax = plt.subplots(figsize=(4, 2.2), dpi=200)
    cats = ["Hoy", "Mañana", "≤7d"]
    vals = [counts["hoy"], counts["mañana"], counts["soon"]]
    ax.bar(cats, vals)
    ax.set_title(f"Vencimientos · {today.isoformat()}")
    for i, v in enumerate(vals):
        ax.text(i, v, str(v), ha="center", va="bottom")
    fig.tight_layout()
    bio = io.BytesIO()
    fig.savefig(bio, format="png")
    plt.close(fig)
    bio.seek(0)
    return bio.read()


# ---------- API pública ----------

def build_pushover_messages(today, window_days, cfg):
    """
    Devuelve lista de dicts con:
    {
      "title": str,
      "message": str,
      "priority": int,
      "sound": str,
      "html": True/False,
      "attachment": bytes|None,
    }
    Paginado automáticamente respetando NOTIFY_MESSAGE_CHAR_LIMIT.
    """
    char_limit = int(cfg.get("NOTIFY_MESSAGE_CHAR_LIMIT", 1000))
    include_pass = bool(cfg.get("NOTIFY_INCLUDE_PASSWORDS", False))
    max_items = int(cfg.get("NOTIFY_MAX_ITEMS_PER_SECTION", 8))
    group_by_provider = bool(cfg.get("NOTIFY_GROUP_BY_PROVIDER", True))
    attach_chart = bool(cfg.get("NOTIFY_ATTACH_CHART", False))

    sections = _query_sections(today, window_days)
    counts = _summary_counts(sections)

    # 1) Resumen (HTML + posible gráfico)
    resume_lines = [
        f"📣 <b>Andriux</b> &nbsp;·&nbsp; <i>{today.isoformat()}</i>",
        f"<small>(Por vencer ≤{window_days} días)</small>",
        "",
        f"✅ Vence <b>HOY</b>: {counts['hoy']}",
        f"🕘 Vence <b>MAÑANA</b>: {counts['mañana']}",
        f"⏳ Vence <b>≤{window_days}d</b>: {counts['soon']}",
    ]
    pages = _chunk_lines(resume_lines, char_limit)
    attachment = None
    if attach_chart:
        png = _build_summary_chart_bytes(counts, today)
        if png:
            attachment = png  # solo en la primera página del resumen

    messages = []
    for i, page in enumerate(pages):
        messages.append({
            "title": "Resumen vencimientos" + (f" (pág. {i+1}/{len(pages)})" if len(pages) > 1 else ""),
            "message": page,
            "priority": int(cfg.get("PUSH_OTHER_PRIORITY", 0)),
            "sound": cfg.get("PUSH_SUMMARY_SOUND", "magic"),
            "html": True,
            "attachment": (attachment if i == 0 else None),
        })

    # 2) Detalles por sección
    detail_specs = [
        ("VENCE HOY", sections["hoy"], int(cfg.get("PUSH_TODAY_PRIORITY", 1)), cfg.get("PUSH_TODAY_SOUND", "siren")),
        ("VENCE MAÑANA (1 día)", sections["mañana"], int(cfg.get("PUSH_OTHER_PRIORITY", 0)), cfg.get("PUSH_OTHER_PRIORITY", "echo")),
        (f"POR VENCER (≤ {window_days} días)", sections["soon"], int(cfg.get("PUSH_OTHER_PRIORITY", 0)), cfg.get("PUSH_SOON_SOUND", "echo")),
    ]
    for sec_title, items, prio, sound in detail_specs:
        if not items:
            continue
        lines = _render_detail_html(sec_title, items, cfg, include_pass, max_items, group_by_provider)
        pages = _chunk_lines(lines, char_limit)
        for i, page in enumerate(pages):
            messages.append({
                "title": sec_title + (f" (pág. {i+1}/{len(pages)})" if len(pages) > 1 else ""),
                "message": page,
                "priority": prio,
                "sound": sound,
                "html": True,
                "attachment": None,
            })

    return messages


def send_pushover_now():
    """
    Construye y envía mensajes con formato HTML + emojis y (opcional) imagen adjunta.
    Retorna [(title, ok, info), ...]
    """
    cfg = current_app.config
    if not _pushover_enabled(cfg):
        return [("Pushover", False, "No configurado")]

    today = date.today()
    window = int(cfg.get("NOTIFY_WINDOW_DAYS", 7))
    batches = build_pushover_messages(today, window, cfg)

    results = []
    for b in batches:
        ok, info = _send_pushover(
            b["message"], b["title"], cfg,
            priority=b["priority"], sound=b["sound"], html=b["html"], attachment_bytes=b["attachment"]
        )
        results.append((b["title"], ok, info))
    return results
