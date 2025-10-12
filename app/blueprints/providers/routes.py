from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from . import providers_bp
from ...extensions import db
from ...models import Provider

@providers_bp.route('/', methods=['GET','POST'])
@login_required
def index():
    if request.method == 'POST':
        name = request.form.get('name')
        if name:
            p = Provider(name=name,
                         contact=request.form.get('contact'),
                         notes=request.form.get('notes'))
            db.session.add(p)
            db.session.commit()
            flash('Proveedor creado', 'success')
            return redirect(url_for('providers.index'))
    items = Provider.query.order_by(Provider.name).all()
    return render_template('providers/providers.html', providers=items)

@providers_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    p = Provider.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash('Proveedor eliminado', 'success')
    return redirect(url_for('providers.index'))
