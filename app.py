from html import escape
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
)
from sqlalchemy import create_engine, text

BASE_DIR = Path(__file__).resolve().parent  # resolve()相対パスを絶対パスに変換します。

load_dotenv(BASE_DIR / ".env")


def create_app(test_config=None):  # 测试设置未被传递时的默认值。
    app = Flask(__name__, template_folder=str(BASE_DIR), static_folder=None)
    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        DATABASE_URL=os.getenv("DATABASE_URL"),
    )
    if test_config:
        app.config.update(test_config)

    app.extensions["db_engine"] = create_engine(
        app.config["DATABASE_URL"], pool_pre_ping=True
    )

    def current_email():
        return session.get("email", "")

    def require_login():
        if not current_email():
            return "ログインしてください。", 401
        return None

    @app.get("/")
    def index():
        return redirect("/login.html")

    @app.post("/register")
    def register():
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("password_confirm", "")

        # print(email, password, confirmation)
        if not email or not password or not confirmation:
            return "すべての項目をご記入ください。", 400
        if password != confirmation:
            return "パスワードが一致しません。", 400  # 返回元组
        engine = app.extensions["db_engine"]
        with engine.connect() as conn:  # 建立普通连接，需手动处理事务
            exists = conn.execute(
                text("SELECT 1 FROM user1 WHERE email=:email"),
                {"email": email},
            ).first()
        if exists:
            return "ユーザーが既に存在します。", 409
        with engine.begin() as conn:  # 自动管理提交/回滚（推荐用于写操作）
            conn.execute(
                text(
                    "INSERT INTO user1 (email,password,updateTime) "
                    "VALUES (:email,:password,CURRENT_TIMESTAMP)"
                ),
                {"email": email, "password": password},
            )
        return 'ユーザー登録が完了しました。<a href="/login.html">登録画面へ戻す</a>'

    @app.post("/login")
    def login():
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        with app.extensions["db_engine"].connect() as conn:
            found = conn.execute(
                text("SELECT 1 FROM user1 WHERE email=:email AND password=:password"),
                {"email": email, "password": password},
            ).first()
        if not found:
            return "メールアドレスまたはパスワードが間違っています。", 401
        session["email"] = email
        return "ログインに成功しました。" + '<a href="/mypage">トップページに戻る</a>'

    @app.post("/logout")
    def logout():
        session.clear()
        return redirect("/login.html")

    @app.get("/my.html")
    @app.get("/mypage")
    def my_page():
        denied = require_login()
        if denied:
            return redirect("/login.html")
        with app.extensions["db_engine"].connect() as conn:
            row = (
                conn.execute(
                    text("SELECT email, password FROM user1 WHERE email=:email"),
                    {"email": current_email()},
                )
                .mappings()
                .first()
            )
        if not row:
            session.clear()
            return redirect("/login.html")
        return render_template(
            "my.html", email=row["email"], password=row["password"], message=""
        )

    @app.post("/mychange")
    def update_profile():
        denied = require_login()
        if denied:
            return denied
        new_email = request.form.get("new_email", "").strip()
        password = request.form.get("new_password", "")
        confirmation = request.form.get("new_pwdconfirm", "")
        if not new_email or not password:
            message = "メールアドレスとパスワードが空にできません。"
        elif password != confirmation:
            message = "パスワードが一致しません。"
        else:
            try:
                with app.extensions["db_engine"].begin() as conn:
                    conn.execute(
                        text(
                            "UPDATE user1 SET email=:new_email, password=:password WHERE email=:old_email"
                        ),
                        {
                            "new_email": new_email,
                            "password": password,
                            "old_email": current_email(),
                        },
                    )
                session["email"] = new_email
                message = "ユーザー情報が正常に更新されました。"
            except Exception:
                message = "ユーザー情報の更新に失敗しました。"
        return render_template(
            "my.html",
            email=new_email or current_email(),
            password=password,
            message=message,
        )

    @app.post("/searchfriend")
    def search_user():
        email = request.form.get("email", "").strip()
        if not email:
            return "メールアドレスを入力してください。", 400
        with app.extensions["db_engine"].connect() as conn:
            found = conn.execute(
                text("SELECT 1 FROM user1 WHERE email=:email"), {
                    "email": email}
            ).first()
        if not found:
            return "メールアドレス又はユーザーが存在しません。", 404
        safe_email = escape(email)
        return f"<span id='to'>{safe_email}</span><button onclick='add_friend()'>友達になる</button>"

    @app.post("/add_friend")
    def add_friend():
        denied = require_login()
        if denied:
            return denied
        sender = current_email()
        recipient = request.form.get("to", "").strip()
        if not recipient:
            return "追加する友達を選択してください", 400
        if sender == recipient:
            return "自分を友達にすることはできません", 400
        engine = app.extensions["db_engine"]
        with engine.connect() as conn:  # 无事务管理
            user_exists = conn.execute(
                text("SELECT 1 FROM user1 WHERE email=:email"), {
                    "email": recipient}
            ).first()
            exists = conn.execute(
                text("""SELECT 1 FROM friend1
                    WHERE (addfrom=:sender AND accepto=:recipient)
                       OR (addfrom=:recipient AND accepto=:sender)"""),
                {"sender": sender, "recipient": recipient},
            ).first()
        if not user_exists:
            return "ユーザーが存在しません。", 404
        if exists:
            return "このユーザーがすでに友達になっています。", 409
        with engine.begin() as conn:  # 有事务管理
            conn.execute(
                text("""INSERT INTO friend1 (addfrom, accepto, status, updateTime)
                    VALUES (:sender, :recipient, 1, CURRENT_TIMESTAMP)"""),
                {"sender": sender, "recipient": recipient},
            )
        return '友達が正常に追加されました。<a href="friends.html">友達一覧を見る</a>'

    @app.post("/friends")
    def friends():
        denied = require_login()
        if denied:
            return denied
        email = current_email()
        with app.extensions["db_engine"].connect() as conn:
            rows = (
                conn.execute(
                    text(
                        """SELECT accepto AS friend FROM friend1 WHERE addfrom=:email
                    UNION ALL SELECT addfrom AS friend FROM friend1 WHERE accepto=:email"""
                    ),
                    {"email": email},
                )
                .mappings()
                .all()
            )
        return "".join(
            f"<a href='message.html?email={escape(row['friend'], quote=True)}'>{escape(row['friend'])}</a><br>"
            for row in rows
        )

    @app.post("/sendmessage")
    def send_message():
        denied = require_login()
        if denied:
            return denied
        content = request.form.get("content", "")
        recipient = request.form.get("to", "").strip()
        if not content or not recipient:
            return "メッセージ内容は空にできません。", 400
        with app.extensions["db_engine"].begin() as conn:
            conn.execute(
                text(
                    """INSERT INTO message1 (messagefrom, messageto, content, updateTime)
                    VALUES (:sender, :recipient, :content, CURRENT_TIMESTAMP)"""
                ),
                {"sender": current_email(), "recipient": recipient,
                 "content": content},
            )
        return "メッセージが送信されました。"

    @app.post("/getMessage")
    def get_messages():
        denied = require_login()
        if denied:
            return denied
        sender = current_email()
        recipient = request.form.get("to", "").strip()
        if not recipient:
            return "", 400
        with app.extensions["db_engine"].connect() as conn:
            rows = (
                conn.execute(
                    text("""SELECT content, messagefrom, updateTime FROM message1
                    WHERE (messagefrom=:sender AND messageto=:recipient)
                       OR (messagefrom=:recipient AND messageto=:sender)
                    ORDER BY updateTime ASC"""),
                    {"sender": sender, "recipient": recipient},
                )
                .mappings()
                .all()
            )
        parts = []
        for row in rows:
            css_class = "mine" if row["messagefrom"] == sender else "other"
            parts.append(
                f"<div class='message {css_class}'><div class='bubble'>"
                f"<div>{escape(str(row['content']))}</div>"
                f"<span>{escape(str(row['messagefrom']))}<br>{escape(str(row['updateTime']))}</span>"
                "</div></div>"
            )
        return "".join(parts)

    @app.post("/addfriend")
    def add_post():
        denied = require_login()
        if denied:
            return denied
        content = request.form.get("content", "")
        if not content:
            return "公開内容は空にできません。", 400
        with app.extensions["db_engine"].begin() as conn:
            conn.execute(
                text("""INSERT INTO friendgroup1 (pengfrom, pengcontent, sendtime)
                    VALUES (:sender, :content, CURRENT_TIMESTAMP)"""),
                {"sender": current_email(), "content": content},
            )
        return '公開されました。<a href="peng.html">友達グループの公開内容に一覧</a>'

    @app.post("/friendgroup")
    def posts():
        denied = require_login()
        if denied:
            return denied
        email = current_email()
        with app.extensions["db_engine"].connect() as conn:
            rows = (
                conn.execute(
                    text("""SELECT p.pengcontent, p.pengfrom FROM friendgroup1 p
                    WHERE p.pengfrom=:email OR p.pengfrom IN (
                        SELECT accepto FROM friend1 WHERE addfrom=:email
                        UNION SELECT addfrom FROM friend1 WHERE accepto=:email
                    ) ORDER BY p.sendtime ASC"""),
                    {"email": email},
                )
                .mappings()
                .all()
            )
        return "".join(
            f"{escape(str(row['pengcontent']))} ({escape(str(row['pengfrom']))})<br><hr>"
            for row in rows
        )

    @app.get("/session_welcome")
    # 中文：获取会话状态视图函数
    # 日本語：セッション状態を返すビュー関数
    def session_status():
        email = current_email()
        return jsonify(loggedIn=bool(email), email=email)

    @app.get("/<path:filename>")
    def frontend_file(filename):
        return send_from_directory(BASE_DIR, filename)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")), debug=False)
