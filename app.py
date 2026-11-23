"""Customer Support Bot (Day 7 Challenge: risk review).

A small Flask app. A customer sends a message, the LLM decides on a reply
and an action, and the app carries out the action.
"""
import json
import logging
import os
import time
import uuid
from dotenv import load_dotenv
from flask import Flask, jsonify, request

from llm import call_llm

load_dotenv()

app = Flask(__name__)

API_KEY = os.environ.get("LLM_API_KEY", "")

logging.basicConfig(filename="logs/app.log", level=logging.INFO)

ORDERS = {
    "10231": {"status": "Shipped", "amount": 1299},
    "10232": {"status": "Delivered", "amount": 499},
    "10233": {"status": "Processing", "amount": 2499},
}
CUSTOMERS = {
    "ravi.kumar@example.com": {"name": "Ravi Kumar", "phone": "+91 98480 12345", "active": True},
    "priya.s@example.com": {"name": "Priya Sharma", "phone": "+91 99890 67890", "active": True},
}
REFUNDS = []
MODEL_NAME = "fake-llm"
PRICE_PER_TOKEN_INR = 0.0005  # made-up price for practice
PENDING_APPROVALS = []

# Actions the AI is allowed to ask for. Risky ones need a human to approve first.
ALLOWED_ACTIONS = {"get_order_status", "issue_refund", "delete_customer_account"}
NEEDS_HUMAN_APPROVAL = {"delete_customer_account"}


# ---------- Tools the LLM can use ----------

def get_order_status(order_id):
    order = ORDERS.get(order_id)
    return order["status"] if order else "Order not found"


def issue_refund(order_id, amount):
    REFUNDS.append({"order_id": order_id, "amount": amount})
    return f"Refunded Rs {amount} for order {order_id}"


def delete_customer_account(customer_email):
    CUSTOMERS.pop(customer_email, None)
    return f"Deleted account {customer_email}"


TOOLS = {
    "get_order_status": get_order_status,
    "issue_refund": issue_refund,
    "delete_customer_account": delete_customer_account,
}


# ---------- Chat endpoint ----------

@app.post("/chat")
def chat():
    data = request.get_json(silent=True) or {}
    email = data.get("customer_email", "")
    message = data.get("message", "")
    customer = CUSTOMERS.get(email, {})

    prompt = (
        "You are a helpful support agent. Reply in JSON with reply, action and args.\n"
        f"Customer name: {customer.get('name')}\n"
        f"Customer email: {email}\n"
        f"Customer phone: {customer.get('phone')}\n"
        f"Customer message: {message}"
    )
    

    request_id = uuid.uuid4().hex[:8]

    start = time.perf_counter()
    text, usage = call_llm(prompt, API_KEY)
    latency_ms = round((time.perf_counter() - start) * 1000)
    cost_inr = round((usage["input_tokens"] + usage["output_tokens"]) * PRICE_PER_TOKEN_INR, 2)
    logging.info(
        "request_id=%s model=%s latency_ms=%s input_tokens=%s output_tokens=%s cost_inr=%s",
        request_id, MODEL_NAME, latency_ms, usage["input_tokens"], usage["output_tokens"], cost_inr,
    )
    result = json.loads(text)

    action = result.get("action")
    action_result = None
    if action:
        args = result.get("args", {})
        if args.get("customer_email") == "from_request":
            args["customer_email"] = email
        if action not in ALLOWED_ACTIONS:
            action_result = "Action not allowed"
        elif action in NEEDS_HUMAN_APPROVAL:
            PENDING_APPROVALS.append({"action": action, "args": args})
            action_result = "Sent to a human agent for approval"
        else:
            action_result = TOOLS[action](**args)

    
    return jsonify({"reply": result["reply"], "action_result": action_result})


if __name__ == "__main__":
    app.run(debug=True)
