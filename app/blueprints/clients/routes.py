from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import clients_bp
from ...extensions import db
from ...models import Client, Provider

@clients_bp.route('/', methods=['GET','POST'])
@login_required
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        provider_id = request.form.get('provider_id') or None
        c = Client(name=name,
                   provider_id=provider_id,
                   contact=request.form.get('contact'),
                   notes=request.form.get('notes'))
        db.session.add(c); db.session.commit()
        flash('Cliente creado', 'success')
        return redirect(url_for('clients.index'))
    providers = Provider.query.order_by(Provider.name).all()
    clients = Client.query.order_by(Client.name).all()
    return render_template('clients/clients.html', clients=clients, providers=providers)

@clients_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    c = Client.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash('Cliente eliminado', 'success')
    return redirect(url_for('clients.index'))
