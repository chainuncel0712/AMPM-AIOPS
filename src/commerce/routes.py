from flask import Blueprint, jsonify, request

def create_commerce_routes(commerce_organ):
    bp = Blueprint("commerce", __name__, url_prefix="/api/commerce")
    catalog = commerce_organ.catalog

    @bp.route("/products")
    def list_products():
        ptype = request.args.get("type")
        if ptype:
            try:
                from .models import ProductType
                products = catalog.list_products(ProductType(ptype))
            except ValueError:
                return jsonify({"error": "invalid type"}), 400
        else:
            products = catalog.list_products()
        return jsonify([p.to_dict() for p in products])

    @bp.route("/products/<product_id>")
    def get_product(product_id):
        p = catalog.get_product(product_id)
        if not p:
            return jsonify({"error": "not found"}), 404
        return jsonify(p.to_dict())

    @bp.route("/checkout", methods=["POST"])
    def checkout():
        data = request.get_json()
        if not data or "buyer_id" not in data or "items" not in data:
            return jsonify({"error": "buyer_id and items required"}), 400
        from .models import CartItem
        items = [CartItem(i["product_id"], i.get("qty", 1)) for i in data["items"]]
        order = catalog.create_order(data["buyer_id"], items)
        payment = commerce_organ.stripe.create_payment_intent(
            order.total_cents, metadata={"order_id": order.id})
        return jsonify({"order": order.to_dict(), "payment": payment})

    @bp.route("/orders/<order_id>")
    def get_order(order_id):
        o = catalog.orders.get(order_id)
        if not o:
            return jsonify({"error": "not found"}), 404
        return jsonify(o.to_dict())

    return bp
