# app/blueprints/providers/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from ...extensions import db
from ...models import Provider

providers_bp = Blueprint("providers", __name__, template_folder="../../templates/providers")

@providers_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        name    = (request.form.get("name") or "").strip()
        contact = (request.form.get("contact") or "").strip()
        notes   = (request.form.get("notes") or "").strip()

        if not name:
            flash("El nombre es obligatorio", "danger")
        else:
            p = Provider(name=name, contact=contact or None, notes=notes or None)
            db.session.add(p)
            db.session.commit()
            flash("Proveedor creado", "success")
        return redirect(url_for("providers.index"))

    providers = Provider.query.order_by(Provider.name.asc()).all()
    return render_template("providers/index.html", providers=providers)

@providers_bp.post("/<int:id>/delete")
@login_required
def delete(id):
    p = Provider.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash("Proveedor eliminado", "success")
    return redirect(url_for("providers.index"))
