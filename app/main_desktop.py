from server_neu import app, init_db, load_questions_from_json


if __name__ == "__main__":
    with app.app_context():
        init_db()
        load_questions_from_json()
    app.run(host="0.0.0.0", port=5000, debug=True)
