from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from . import core_bp
from ...models import Account, Provider, Client
from datetime import date, timedelta
from sqlalchemy import or_, and_
from ...services.notify import send_pushover_now

@core_bp.route('/')
@login_required
def dashboard():
    today = date.today()
    window_days = 7
    soon_limit = today + timedelta(days=window_days)

    total_accounts   = Account.query.count()
    total_providers  = Provider.query.count()
    total_clients    = Client.query.count()

    # Sin fecha
    no_date = Account.query.filter(Account.end_date.is_(None)).count()

    # Vencidas
    expired = Account.query.filter(
        Account.end_date.is_not(None),
        Account.end_date < today
    ).count()

    # Por vencer (en los próximos N días, incluye hoy)
    expiring = Account.query.filter(
        Account.end_date.is_not(None),
        Account.end_date >= today,
        Account.end_date <= soon_limit
    ).count()

    # Activas (más allá de la ventana)
    active = Account.query.filter(
        Account.end_date.is_not(None),
        Account.end_date > soon_limit
    ).count()

    return render_template(
        'core/dashboard.html',
        total_accounts=total_accounts,
        total_providers=total_providers,
        total_clients=total_clients,
        active=active,
        expiring=expiring,
        expired=expired,
        no_date=no_date,
        window_days=window_days
    )

@core_bp.route('/admin/run-pushover')
@login_required
def run_pushover():
    # Solo admin
    if not getattr(current_user, "is_admin", False):
        flash("Solo admin puede enviar notificaciones.", "warning")
        return redirect(url_for('core.dashboard'))

    results = send_pushover_now()
    ok_any = any(ok for _, ok, _ in results)

    # 👇 OJO: comillas normales, sin barras invertidas
    detail = " · ".join([f"{t}: {'OK' if ok else 'FAIL'}({info})" for t, ok, info in results])

    flash(f"Envío Pushover: {detail}", "success" if ok_any else "danger")
    return redirect(url_for('core.dashboard'))
