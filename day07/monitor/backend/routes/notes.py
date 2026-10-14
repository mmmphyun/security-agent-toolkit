from flask import Blueprint, request
from auth_helpers import api_access_error
from note_rules import read_note
from repositories import notes as note_repository

notes_bp = Blueprint("notes", __name__)


@notes_bp.before_request
def require_login():
    return api_access_error()


@notes_bp.get("/api/notes")
def list_notes():
    return {"notes": note_repository.list_notes()}


@notes_bp.get("/api/notes/<int:note_id>")
def get_note(note_id):
    note = note_repository.find_note(note_id)
    if note is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    return {"note": note}


@notes_bp.post("/api/notes")
def create_note():
    note, error = read_note(request.get_json(silent=True))
    if error:
        return {"error": error}, 400
    created = note_repository.create_note(note["title"], note["body"])
    return {"note": created}, 201


@notes_bp.put("/api/notes/<int:note_id>")
def update_note(note_id):
    note, error = read_note(request.get_json(silent=True))
    if error:
        return {"error": error}, 400
    updated = note_repository.update_note(note_id, note["title"], note["body"])
    if updated is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    return {"note": updated}


@notes_bp.delete("/api/notes/<int:note_id>")
def delete_note(note_id):
    deleted = note_repository.delete_note(note_id)
    if deleted is None:
        return {"error": "메모를 찾을 수 없습니다."}, 404
    return {"message": "메모를 삭제했습니다."}
