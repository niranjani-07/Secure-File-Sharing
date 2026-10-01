import os
import hashlib

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file
)

from werkzeug.utils import secure_filename

from config import Config
from models import (
    db,
    User,
    File,
    FileShare,
    ActivityLog
)
from security import hash_password, verify_password
from encryption import encrypt_file, decrypt_data


# ==========================================================
# FLASK APPLICATION
# ==========================================================

app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)

db.init_app(app)


# ==========================================================
# ALLOWED FILE TYPES
# ==========================================================

ALLOWED_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "txt",
    "jpg",
    "jpeg",
    "png",
    "zip"
}


def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


# ==========================================================
# ACTIVITY LOG HELPER
# ==========================================================

def log_activity(
    user_id,
    action,
    file_id=None,
    details=None
):

    activity = ActivityLog(
        user_id=user_id,
        file_id=file_id,
        action=action,
        details=details
    )

    db.session.add(activity)


# ==========================================================
# DATABASE INITIALIZATION
# ==========================================================

with app.app_context():
    db.create_all()


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(
            url_for("dashboard")
        )

    return redirect(
        url_for("login")
    )


# ==========================================================
# REGISTER
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not email or not password:

            flash(
                "All fields are required."
            )

            return redirect(
                url_for("register")
            )

        existing_user = User.query.filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing_user:

            flash(
                "Username or email already exists."
            )

            return redirect(
                url_for("register")
            )

        new_user = User(
            username=username,
            email=email,
            password=hash_password(password)
        )

        db.session.add(new_user)
        db.session.commit()

        flash(
            "Registration successful. Please login."
        )

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            username=username
        ).first()

        if user and verify_password(
            user.password,
            password
        ):

            session.clear()

            session["user_id"] = user.id
            session["username"] = user.username

            # Log login
            log_activity(
                user.id,
                "LOGIN",
                details="User logged in successfully"
            )

            db.session.commit()

            return redirect(
                url_for("dashboard")
            )

        flash(
            "Invalid username or password."
        )

    return render_template(
        "login.html"
    )


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():

    if "user_id" in session:

        user_id = session["user_id"]

        log_activity(
            user_id,
            "LOGOUT",
            details="User logged out"
        )

        db.session.commit()

    session.clear()

    flash(
        "You have been logged out."
    )

    return redirect(
        url_for("login")
    )


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    files = File.query.filter_by(
        owner_id=user_id
    ).order_by(
        File.uploaded_at.desc()
    ).all()

    return render_template(
        "dashboard.html",
        files=files
    )


# ==========================================================
# UPLOAD FILE
# ==========================================================

@app.route("/upload", methods=["GET", "POST"])
def upload():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    if request.method == "POST":

        uploaded_file = request.files.get(
            "file"
        )

        if (
            not uploaded_file
            or uploaded_file.filename == ""
        ):

            flash(
                "Please select a file."
            )

            return redirect(
                url_for("upload")
            )

        original_filename = secure_filename(
            uploaded_file.filename
        )

        if not original_filename:

            flash(
                "Invalid filename."
            )

            return redirect(
                url_for("upload")
            )

        # File type validation
        if not allowed_file(
            original_filename
        ):

            flash(
                "File type not allowed. "
                "Allowed: PDF, DOC, DOCX, TXT, "
                "JPG, JPEG, PNG, ZIP."
            )

            return redirect(
                url_for("upload")
            )

        file_data = uploaded_file.read()

        if not file_data:

            flash(
                "The selected file is empty."
            )

            return redirect(
                url_for("upload")
            )

        # SHA-256 hash
        file_hash = hashlib.sha256(
            file_data
        ).hexdigest()

        # Random encrypted filename
        stored_filename = (
            hashlib.sha256(
                os.urandom(32)
            ).hexdigest()
            + ".enc"
        )

        stored_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            stored_filename
        )

        temp_path = os.path.join(
            app.config["UPLOAD_FOLDER"],
            "temp_" + stored_filename
        )

        # Temporary original file
        with open(
            temp_path,
            "wb"
        ) as temp_file:

            temp_file.write(
                file_data
            )

        # Encrypt
        try:

            encrypt_file(
                temp_path,
                stored_path
            )

        except Exception:

            flash(
                "File encryption failed."
            )

            return redirect(
                url_for("upload")
            )

        finally:

            if os.path.exists(
                temp_path
            ):

                os.remove(
                    temp_path
                )

        # Database record
        new_file = File(
            filename=original_filename,
            stored_filename=stored_filename,
            owner_id=session["user_id"],
            file_hash=file_hash
        )

        db.session.add(new_file)
        db.session.flush()

        # Log upload
        log_activity(
            session["user_id"],
            "UPLOAD",
            file_id=new_file.id,
            details=f"Uploaded file: {original_filename}"
        )

        db.session.commit()

        flash(
            "File uploaded and encrypted successfully."
        )

        return redirect(
            url_for("dashboard")
        )

    return render_template(
        "upload.html"
    )


# ==========================================================
# SHARE FILE
# ==========================================================

@app.route("/share", methods=["GET", "POST"])
def share():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    owned_files = File.query.filter_by(
        owner_id=user_id
    ).order_by(
        File.uploaded_at.desc()
    ).all()

    if request.method == "POST":

        file_id = request.form.get(
            "file_id"
        )

        username = request.form.get(
            "username",
            ""
        ).strip()

        permission = request.form.get(
            "permission",
            "read"
        )

        file = File.query.filter_by(
            id=file_id,
            owner_id=user_id
        ).first()

        if not file:

            flash(
                "File not found."
            )

            return redirect(
                url_for("share")
            )

        recipient = User.query.filter_by(
            username=username
        ).first()

        if not recipient:

            flash(
                "User not found."
            )

            return redirect(
                url_for("share")
            )

        if recipient.id == user_id:

            flash(
                "You cannot share a file with yourself."
            )

            return redirect(
                url_for("share")
            )

        if permission not in [
            "read",
            "download"
        ]:

            permission = "read"

        existing_share = FileShare.query.filter_by(
            file_id=file.id,
            shared_with=recipient.id
        ).first()

        if existing_share:

            existing_share.permission = permission

        else:

            new_share = FileShare(
                file_id=file.id,
                shared_with=recipient.id,
                permission=permission
            )

            db.session.add(
                new_share
            )

        # Log share action
        log_activity(
            user_id,
            "SHARE",
            file_id=file.id,
            details=(
                f"Shared '{file.filename}' "
                f"with user '{recipient.username}'"
            )
        )

        db.session.commit()

        flash(
            "File shared successfully."
        )

        return redirect(
            url_for("share")
        )

    return render_template(
        "share.html",
        files=owned_files
    )


# ==========================================================
# SHARED WITH ME
# ==========================================================

@app.route("/shared-files")
def shared_files():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    shared = FileShare.query.filter_by(
        shared_with=session["user_id"]
    ).order_by(
        FileShare.created_at.desc()
    ).all()

    return render_template(
        "shared_files.html",
        shared_files=shared
    )


# ==========================================================
# DOWNLOAD FILE
# ==========================================================

@app.route("/download/<int:file_id>")
def download(file_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    # Check owner
    file = File.query.filter_by(
        id=file_id,
        owner_id=user_id
    ).first()

    if file:

        permission = "owner"

    else:

        # Check shared permission
        share = FileShare.query.filter_by(
            file_id=file_id,
            shared_with=user_id
        ).first()

        if not share:

            flash(
                "You do not have permission to access this file."
            )

            return redirect(
                url_for("dashboard")
            )

        file = File.query.get(
            file_id
        )

        permission = share.permission

    if not file:

        flash(
            "File not found."
        )

        return redirect(
            url_for("dashboard")
        )

    stored_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.stored_filename
    )

    if not os.path.exists(
        stored_path
    ):

        flash(
            "Stored file not found."
        )

        return redirect(
            url_for("dashboard")
        )

    # Read encrypted file
    try:

        with open(
            stored_path,
            "rb"
        ) as encrypted_file:

            encrypted_data = encrypted_file.read()

        # Decrypt
        decrypted_data = decrypt_data(
            encrypted_data
        )

    except Exception:

        flash(
            "Unable to decrypt file."
        )

        return redirect(
            url_for("dashboard")
        )

    # Integrity verification
    current_hash = hashlib.sha256(
        decrypted_data
    ).hexdigest()

    if current_hash != file.file_hash:

        flash(
            "File integrity verification failed."
        )

        return redirect(
            url_for("dashboard")
        )

    # Log download
    log_activity(
        user_id,
        "DOWNLOAD",
        file_id=file.id,
        details=f"Downloaded file: {file.filename}"
    )

    db.session.commit()

    # Send original file
    from io import BytesIO

    return send_file(
        BytesIO(decrypted_data),
        as_attachment=True,
        download_name=file.filename
    )


# ==========================================================
# DELETE FILE
# ==========================================================

@app.route(
    "/delete/<int:file_id>",
    methods=["POST"]
)
def delete_file(file_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    user_id = session["user_id"]

    file = File.query.filter_by(
        id=file_id,
        owner_id=user_id
    ).first()

    if not file:

        flash(
            "You do not have permission to delete this file."
        )

        return redirect(
            url_for("dashboard")
        )

    # Save filename before deleting
    deleted_filename = file.filename

    stored_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        file.stored_filename
    )

    # Remove encrypted storage file
    if os.path.exists(
        stored_path
    ):

        os.remove(
            stored_path
        )

    # Delete database record
    db.session.delete(file)

    # Delete action must not use file_id
    # because the File record is being deleted.
    log_activity(
        user_id,
        "DELETE",
        file_id=None,
        details=f"Deleted file: {deleted_filename}"
    )

    db.session.commit()

    flash(
        "File deleted successfully."
    )

    return redirect(
        url_for("dashboard")
    )


# ==========================================================
# ACTIVITY LOG
# ==========================================================

@app.route("/activity")
def activity():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    activities = ActivityLog.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        ActivityLog.created_at.desc()
    ).all()

    return render_template(
        "activity.html",
        activities=activities
    )


# ==========================================================
# FILE SIZE ERROR
# ==========================================================

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum allowed size is 50 MB."
    )

    return redirect(
        url_for("upload")
    )


# ==========================================================
# GENERAL SERVER ERROR
# ==========================================================

@app.errorhandler(500)
def internal_server_error(error):

    db.session.rollback()

    flash(
        "An internal server error occurred."
    )

    return redirect(
        url_for("dashboard")
    )


# ==========================================================
# RUN APPLICATION
# ==========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )