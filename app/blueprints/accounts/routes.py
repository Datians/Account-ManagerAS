import os
from datetime import date, datetime, timedelta
from io import BytesIO

from flask import (
    render_template, request, redirect, url_for,
    flash, send_file, current_app
)
from flask_login import login_required
from sqlalchemy import or_, func

from . import accounts_bp
from ...extensions import db
from ...models import Account, Provider, Client
from ...services.excel_io import generate_template_bytes
import pandas as pd


def parse_date_str(s: str):
    if not s:
        return None
    s = s.strip()
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except Exception:
        pass
    try:
        return datetime.strptime(s, "%d/%m/%Y").date()
    except Exception:
        return None


def parse_date_cell(v):
    if pd.isna(v):
        return None
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None


@accounts_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    # Crear nueva
    if request.method == 'POST' and request.form.get('action') == 'create':
        a = Account(
            platform=request.form.get('platform'),
            username=request.form.get('username'),
            password=request.form.get('password'),
            client_id=request.form.get('client_id') or None,
            provider_id=request.form.get('provider_id') or None,
            start_date=parse_date_str(request.form.get('start_date')),
            end_date=parse_date_str(request.form.get('end_date')),
            time_allocated=int(request.form.get('time_allocated')) if request.form.get('time_allocated') else None,
            notes=request.form.get('notes'),
            # <<< NUEVO >>>
            status_manual=request.form.get('status_manual') or None
        )
        db.session.add(a)
        db.session.commit()
        flash('Cuenta creada', 'success')
        return redirect(url_for('accounts.index'))

    # Filtros
    today = date.today()
    soon_limit = today + timedelta(days=7)

    q        = (request.args.get('q') or "").strip()            # libre
    status   = (request.args.get('status') or 'all').strip()    # estado (incluye 'down')
    platform = (request.args.get('platform') or "").strip()     # selector plataforma

    page = int(request.args.get('page', 1) or 1)
    per_page = 10

    query = (Account.query.outerjoin(Client).outerjoin(Provider))

    if platform:
        query = query.filter(
            func.lower(func.trim(Account.platform)) ==
            func.lower(func.trim(func.cast(platform, db.String())))
        )

    if q:
        term = f"%{q.replace('%','').replace('_','').strip()}%"
        term_l = func.lower(term)
        query = query.filter(or_(
            func.lower(Account.platform).like(term_l),
            func.lower(Account.username).like(term_l),
            func.lower(Client.name).like(term_l),
            func.lower(Provider.name).like(term_l),
        ))

    # Estado (el manual 'Caída' predomina)
    if status == 'down':
        query = query.filter(Account.status_manual == 'CAIDA')
    elif status == 'nodate':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_(None))
    elif status == 'expired':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_not(None), Account.end_date < today)
    elif status == 'expiring':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_not(None),
                             Account.end_date >= today, Account.end_date <= soon_limit)
    elif status == 'active':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_not(None), Account.end_date > soon_limit)

    query = query.order_by(Account.end_date.is_(None),
                           Account.end_date.asc(),
                           Account.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    accounts = pagination.items

    providers = Provider.query.order_by(Provider.name).all()
    clients = Client.query.order_by(Client.name).all()

    platform_options = [
        row[0] for row in (
            db.session.query(func.trim(Account.platform))
            .filter(Account.platform.isnot(None))
            .distinct()
            .order_by(func.lower(func.trim(Account.platform)))
            .all()
        )
    ]

    return render_template(
        'accounts/accounts.html',
        accounts=accounts,
        providers=providers,
        clients=clients,
        today=today,
        soon_limit=soon_limit,
        q=q,
        status=status,
        platform_selected=platform,
        platform_options=platform_options,
        pagination=pagination
    )


@accounts_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    a = Account.query.get_or_404(id)
    if request.method == 'POST':
        a.platform = request.form.get('platform')
        a.username = request.form.get('username')
        a.password = request.form.get('password')
        a.client_id = request.form.get('client_id') or None
        a.provider_id = request.form.get('provider_id') or None
        a.start_date = parse_date_str(request.form.get('start_date'))
        a.end_date = parse_date_str(request.form.get('end_date'))
        a.time_allocated = int(request.form.get('time_allocated')) if request.form.get('time_allocated') else None
        a.notes = request.form.get('notes')
        # <<< NUEVO >>>
        a.status_manual = request.form.get('status_manual') or None

        db.session.commit()
        flash('Cuenta actualizada', 'success')
        return redirect(url_for('accounts.index'))

    providers = Provider.query.order_by(Provider.name).all()
    clients = Client.query.order_by(Client.name).all()
    return render_template('accounts/account_form.html', account=a, providers=providers, clients=clients)


@accounts_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    a = Account.query.get_or_404(id)
    db.session.delete(a)
    db.session.commit()
    flash('Cuenta eliminada', 'success')
    return redirect(url_for('accounts.index'))


@accounts_bp.route('/download-template')
@login_required
def download_template():
    bio = generate_template_bytes()
    return send_file(
        bio,
        download_name="plantilla_cuentas.xlsx",
        as_attachment=True,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )


@accounts_bp.route('/upload-excel', methods=['POST'])
@login_required
def upload_excel():
    f = request.files.get('file')
    if not f:
        flash('No se subió archivo', 'warning')
        return redirect(url_for('accounts.index'))

    path = os.path.join(current_app.config['UPLOAD_FOLDER'], f.filename)
    f.save(path)

    try:
        df = pd.read_excel(path, engine='openpyxl')
    except Exception as e:
        flash(f'Error leyendo Excel: {e}', 'danger')
        return redirect(url_for('accounts.index'))

    df.columns = [c.lower() for c in df.columns]
    required = {'platform', 'username'}
    if not required.issubset(set(df.columns)):
        flash(f'La plantilla debe contener: {required}', 'danger')
        return redirect(url_for('accounts.index'))

    inserted = 0
    for _, row in df.iterrows():
        provider = client = None
        if 'provider' in df.columns and pd.notna(row.get('provider')):
            provider_name = str(row['provider']).strip()
            provider = Provider.query.filter_by(name=provider_name).first()
            if not provider:
                provider = Provider(name=provider_name)
                db.session.add(provider)
                db.session.flush()

        if 'client' in df.columns and pd.notna(row.get('client')):
            client_name = str(row['client']).strip()
            client = Client.query.filter_by(name=client_name).first()
            if not client:
                client = Client(name=client_name, provider=provider)
                db.session.add(client)
                db.session.flush()

        a = Account(
            platform=str(row.get('platform')).strip(),
            username=str(row.get('username')).strip(),
            password=str(row.get('password')) if 'password' in df.columns else None,
            provider=provider,
            client=client,
            start_date=parse_date_cell(row.get('start_date')),
            end_date=parse_date_cell(row.get('end_date')),
            time_allocated=int(row.get('time_allocated')) if ('time_allocated' in df.columns and pd.notna(row.get('time_allocated'))) else None,
            notes=str(row.get('notes')) if 'notes' in df.columns else None
        )
        db.session.add(a)
        inserted += 1

    db.session.commit()
    flash(f'{inserted} cuentas importadas', 'success')
    return redirect(url_for('accounts.index'))


@accounts_bp.route('/export')
@login_required
def export_accounts():
    """Exporta a Excel respetando filtros (q, status, platform)."""
    today = date.today()
    soon_limit = today + timedelta(days=7)
    q        = (request.args.get('q') or "").strip()
    status   = (request.args.get('status') or 'all').strip()
    platform = (request.args.get('platform') or "").strip()

    query = Account.query.outerjoin(Client).outerjoin(Provider)

    if platform:
        query = query.filter(
            func.lower(func.trim(Account.platform)) ==
            func.lower(func.trim(func.cast(platform, db.String())))
        )

    if q:
        term = f"%{q.replace('%','').replace('_','').strip()}%"
        term_l = func.lower(term)
        query = query.filter(or_(
            func.lower(Account.platform).like(term_l),
            func.lower(Account.username).like(term_l),
            func.lower(Client.name).like(term_l),
            func.lower(Provider.name).like(term_l),
        ))

    if status == 'down':
        query = query.filter(Account.status_manual == 'CAIDA')
    elif status == 'nodate':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_(None))
    elif status == 'expired':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_not(None), Account.end_date < today)
    elif status == 'expiring':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_not(None),
                             Account.end_date >= today, Account.end_date <= soon_limit)
    elif status == 'active':
        query = query.filter(Account.status_manual.is_(None),
                             Account.end_date.is_not(None), Account.end_date > soon_limit)

    rows = []
    for a in query.order_by(Account.end_date.is_(None), Account.end_date.asc()).all():
        # Puedes incluir status_manual si quieres verlo en Excel
        rows.append({
            'platform': a.platform,
            'username': a.username,
            'password': a.password,
            'client': a.client.name if a.client else '',
            'provider': a.provider.name if a.provider else '',
            'start_date': a.start_date,
            'end_date': a.end_date,
            'status_manual': a.status_manual or '',
            'notes': a.notes
        })

    df = pd.DataFrame(rows)
    bio = BytesIO()
    with pd.ExcelWriter(bio, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Cuentas')
    bio.seek(0)
    return send_file(
        bio,
        as_attachment=True,
        download_name='cuentas_filtradas.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# --- Acciones masivas: eliminar varias cuentas ---
@accounts_bp.route('/bulk-action', methods=['POST'])
@login_required
def bulk_action():
    action = (request.form.get('action') or '').strip()
    ids = request.form.getlist('selected')  # viene de los checkboxes

    # Conservamos filtros para volver a la vista tal cual estaba
    q = request.form.get('q') or ''
    status = request.form.get('status') or 'all'
    platform = request.form.get('platform') or ''
    page = request.form.get('page') or 1

    if not ids:
        flash('No seleccionaste ninguna cuenta.', 'warning')
        return redirect(url_for('accounts.index', q=q, status=status, platform=platform, page=page))

    # Sanitizar a enteros
    try:
        ids_int = [int(x) for x in ids]
    except ValueError:
        flash('IDs inválidos.', 'danger')
        return redirect(url_for('accounts.index', q=q, status=status, platform=platform, page=page))

    if action == 'delete':
        # Elimina de forma segura
        to_delete = Account.query.filter(Account.id.in_(ids_int)).all()
        n = len(to_delete)
        for a in to_delete:
            db.session.delete(a)
        db.session.commit()
        flash(f'Se eliminaron {n} cuentas.', 'success')
    else:
        flash('Acción no soportada.', 'warning')

    return redirect(url_for('accounts.index', q=q, status=status, platform=platform, page=page))
