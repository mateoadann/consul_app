from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PushSubscription

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/subscribe", methods=["POST"])
@login_required
def subscribe():
    """Register a push subscription for the current user."""
    data = request.get_json()
    if not data or not all(k in data for k in ("endpoint", "keys")):
        return jsonify({"error": "Invalid subscription data"}), 400

    endpoint = data["endpoint"]
    keys = data["keys"]
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")

    if not p256dh or not auth:
        return jsonify({"error": "Missing keys (p256dh, auth)"}), 400

    # Upsert: update existing or create new
    sub = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if sub:
        sub.user_id = current_user.id
        sub.p256dh = p256dh
        sub.auth = auth
    else:
        sub = PushSubscription(
            user_id=current_user.id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
        )
        db.session.add(sub)

    db.session.commit()
    return jsonify({"ok": True}), 201


@notifications_bp.route("/unsubscribe", methods=["DELETE"])
@login_required
def unsubscribe():
    """Remove a push subscription for the current user."""
    data = request.get_json()
    if not data or "endpoint" not in data:
        return jsonify({"error": "Missing endpoint"}), 400

    sub = PushSubscription.query.filter_by(
        endpoint=data["endpoint"],
        user_id=current_user.id,
    ).first()

    if sub:
        db.session.delete(sub)
        db.session.commit()

    return jsonify({"ok": True}), 200
