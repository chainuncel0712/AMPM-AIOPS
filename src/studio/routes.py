from flask import Blueprint, jsonify, request

def create_studio_routes(studio_organ):
    bp = Blueprint("studio", __name__, url_prefix="/api/studio")

    @bp.route("/tenants", methods=["GET", "POST"])
    def handle_tenants():
        if request.method == "POST":
            data = request.get_json() or {}
            if "name" not in data or "owner_id" not in data:
                return jsonify({"error": "name and owner_id required"}), 400
            result = studio_organ.onboard_tenant(
                data["name"], data["owner_id"], data.get("tier", "basic"))
            return jsonify(result), 201
        return jsonify([t.to_dict() for t in studio_organ.tenants.list_tenants()])

    @bp.route("/tenants/<tenant_id>")
    def get_tenant(tenant_id):
        t = studio_organ.tenants.get_tenant(tenant_id)
        if not t:
            return jsonify({"error": "not found"}), 404
        ws_list = studio_organ.workspaces.list_by_tenant(tenant_id)
        return jsonify({"tenant": t.to_dict(),
                        "workspaces": [w.to_dict() for w in ws_list]})

    @bp.route("/keys/<tenant_id>", methods=["POST"])
    def create_key(tenant_id):
        data = request.get_json() or {}
        k = studio_organ.api_keys.create_key(tenant_id, data.get("label", ""))
        return jsonify({"key": k.key, "key_hash": k.key_hash, "label": k.label})

    @bp.route("/keys/<key_hash>", methods=["DELETE"])
    def revoke_key(key_hash):
        if studio_organ.api_keys.revoke(key_hash):
            return jsonify({"status": "revoked"})
        return jsonify({"error": "not found"}), 404

    return bp
