# app/blueprints/clients/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ...extensions import db
from ...models import Client, Provider

clients_bp = Blueprint("clients", __name__, template_folder="../../templates/clients")

@clients_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        name        = (request.form.get("name") or "").strip()
        provider_id = request.form.get("provider_id") or None
        contact     = (request.form.get("contact") or "").strip()
        notes       = (request.form.get("notes") or "").strip()

        if not name:
            flash("El nombre es obligatorio", "danger")
        else:
            c = Client(
                name=name,
                provider_id=int(provider_id) if provider_id else None,
                contact=contact or None,
                notes=notes or None,
            )
            db.session.add(c)
            db.session.commit()
            flash("Cliente creado", "success")
        return redirect(url_for("clients.index"))

    providers = Provider.query.order_by(Provider.name.asc()).all()
    clients = Client.query.order_by(Client.name.asc()).all()
    return render_template("clients/index.html", providers=providers, clients=clients)

@clients_bp.post("/<int:id>/delete")
@login_required
def delete(id):
    c = Client.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Cliente eliminado", "success")
    return redirect(url_for("clients.index"))
