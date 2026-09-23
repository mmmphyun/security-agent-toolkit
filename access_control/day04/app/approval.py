# 접근 관리 서버: 요청을 접수하고 승인·반려를 처리한다.
import os
import sqlite3
from flask import Flask, request

app = Flask(__name__)
app.json.ensure_ascii = False
DB_FILE = os.environ.get("DB_FILE", "/app/db/company.db")


def connect_db():
    con = sqlite3.connect(DB_FILE)
    con.execute("PRAGMA foreign_keys = ON")
    return con


@app.post("/requests")
def create_access_request():
    body = request.get_json(silent=True) or {}
    requester_id = body.get("requester_id", "").strip()
    contract_id = body.get("contract_id", "").strip()
    reason = body.get("reason", "").strip()

    if not requester_id or not contract_id or not reason:
        return {"result": "ERROR", "reason": "REQUIRED_FIELDS"}, 400

    with connect_db() as con:
        user = con.execute("""
            SELECT employed
            FROM users
            WHERE user_id = ?
        """, (requester_id,)).fetchone()
        if user is None:
            return {"result": "ERROR", "reason": "UNKNOWN_USER"}, 404
        if user[0] != 1:
            return {"result": "ERROR", "reason": "NOT_EMPLOYED"}, 403

        contract = con.execute("""
            SELECT 1
            FROM contracts
            WHERE contract_id = ?
        """, (contract_id,)).fetchone()
        if contract is None:
            return {"result": "ERROR", "reason": "UNKNOWN_CONTRACT"}, 404

        pending = con.execute("""
            SELECT request_id
            FROM access_requests
            WHERE requester_id = ?
            AND contract_id = ?
            AND status = 'PENDING'
        """, (requester_id, contract_id)).fetchone()
        if pending is not None:
            return {
                "result": "ERROR",
                "reason": "ALREADY_PENDING",
                "request_id": pending[0],
            }, 409

        cursor = con.execute("""
            INSERT INTO access_requests (
                requester_id,
                contract_id,
                reason,
                status
            )
            VALUES (?, ?, ?, 'PENDING')
        """, (requester_id, contract_id, reason))
        request_id = cursor.lastrowid

    return {
        "result": "CREATED",
        "request_id": request_id,
        "status": "PENDING",
    }, 201


@app.get("/requests/<int:request_id>")
def get_access_request(request_id):
    with connect_db() as con:
        row = con.execute("""
            SELECT request_id, requester_id, contract_id,
                   reason, status, requested_at
            FROM access_requests
            WHERE request_id = ?
        """, (request_id,)).fetchone()
    if row is None:
        return {"result": "ERROR", "reason": "UNKNOWN_REQUEST"}, 404
    return {
        "request_id": row[0],
        "requester_id": row[1],
        "contract_id": row[2],
        "reason": row[3],
        "status": row[4],
        "requested_at": row[5],
    }, 200


import sys

DATA_DIR = os.environ.get("DATA_DIR", "/app/data")
sys.path.append(DATA_DIR)
from decide_access_request import decide_access_request


@app.post("/decisions")
def create_access_decision():
    body = request.get_json(silent=True) or {}
    request_id = body.get("request_id")
    approver_id = body.get("approver_id", "").strip()
    decision = body.get("decision", "").strip().upper()
    note = body.get("note", "").strip()

    if not request_id or not approver_id or not note:
        return {"result": "ERROR", "reason": "REQUIRED_FIELDS"}, 400
    if decision not in ("APPROVED", "REJECTED"):
        return {"result": "ERROR", "reason": "UNKNOWN_DECISION"}, 400

    result = decide_access_request(
        request_id,
        approver_id,
        decision,
        note,
    )
    status_codes = {
        "NO_APPROVAL_PERMISSION": 403,
        "SELF_APPROVAL_NOT_ALLOWED": 403,
        "UNKNOWN_REQUEST": 404,
        "ALREADY_DECIDED": 409,
    }
    if result != "RECORDED":
        return {"result": "ERROR", "reason": result}, status_codes[result]

    return {
        "result": "RECORDED",
        "request_id": request_id,
        "status": decision,
    }, 200


from revoke_access import revoke_assignment, revoke_request

REVOKE_STATUS_CODES = {
    "NO_REVOKE_PERMISSION": 403,
    "UNKNOWN_REQUEST": 404,
    "UNKNOWN_ASSIGNMENT": 404,
    "NOT_APPROVED": 409,
}


@app.post("/revocations/requests")
def revoke_access_request():
    body = request.get_json(silent=True) or {}
    request_id = body.get("request_id")
    actor_id = body.get("actor_id", "").strip()
    reason = body.get("reason", "").strip()

    if not request_id or not actor_id or not reason:
        return {"result": "ERROR", "reason": "REQUIRED_FIELDS"}, 400

    result = revoke_request(request_id, actor_id, reason)
    if result != "RECORDED":
        return {"result": "ERROR", "reason": result}, REVOKE_STATUS_CODES[result]
    return {
        "result": "RECORDED",
        "request_id": request_id,
        "status": "REVOKED",
    }, 200


@app.post("/revocations/assignments")
def revoke_access_assignment():
    body = request.get_json(silent=True) or {}
    user_id = body.get("user_id", "").strip()
    customer = body.get("customer", "").strip()
    actor_id = body.get("actor_id", "").strip()
    reason = body.get("reason", "").strip()

    if not user_id or not customer or not actor_id or not reason:
        return {"result": "ERROR", "reason": "REQUIRED_FIELDS"}, 400

    result = revoke_assignment(user_id, customer, actor_id, reason)
    if result != "RECORDED":
        return {"result": "ERROR", "reason": result}, REVOKE_STATUS_CODES[result]
    return {
        "result": "RECORDED",
        "user_id": user_id,
        "customer": customer,
    }, 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)