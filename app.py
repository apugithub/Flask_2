import os
import datetime
import hashlib
from flask import Flask, session, url_for, redirect, render_template, request, abort, flash
from database import list_users, verify, delete_user_from_db, add_user, user_db_all_fields
from database import read_note_from_db, write_note_into_db, delete_note_from_db, match_user_id_with_note_id
from database import image_upload_record, list_images_for_user, match_user_id_with_image_uid, delete_image_from_db
from werkzeug.utils import secure_filename
from phonenumber_search import number_lookup
import goals_stat as gs
from excel_to_html import excel_to_html
import paths


app = Flask(__name__)
app.config.from_object('config')


@app.errorhandler(401)
def FUN_401(error):
    return render_template("page_401.html"), 401


@app.errorhandler(403)
def FUN_403(error):
    return render_template("page_403.html"), 403


@app.errorhandler(404)
def FUN_404(error):
    return render_template("page_404.html"), 404


@app.errorhandler(405)
def FUN_405(error):
    return render_template("page_405.html"), 405


@app.errorhandler(413)
def FUN_413(error):
    return render_template("page_413.html"), 413


# Here from main routes starts
@app.route("/")
def FUN_root():
    return render_template("index.html")
    

@app.route("/welcome")
def welcome():
    return render_template("welcome.html")
    

@app.route("/public/")
def FUN_public():
    return render_template("public_page.html")


@app.route("/private/")
def FUN_private():
    if "current_user" in session.keys():
        notes_list = read_note_from_db(session['current_user'])
        notes_table = zip([x[0] for x in notes_list],\
                          [x[1] for x in notes_list],\
                          [x[2] for x in notes_list],\
                          ["/delete_note/" + x[0] for x in notes_list])

        images_list = list_images_for_user(session['current_user'])
        images_table = zip([x[0] for x in images_list],\
                          [x[1] for x in images_list],\
                          [x[2] for x in images_list],\
                          ["/delete_image/" + x[0] for x in images_list])

        return render_template("private_page.html", notes = notes_table, images = images_table)
    else:
        return abort(401)


@app.route("/admin/")
def FUN_admin():
    if session.get("current_user", None) == "ADMIN":
        user_list = list_users()
        all_fields = user_db_all_fields()      # Added this to access all fields of user db,
        # here all_fields[0] is same as user_list
        user_table = zip(range(1, len(user_list)+1),\
                        user_list,\
                        [x + y for x,y in zip(["/delete_user/"] * len(user_list), user_list)], all_fields[2])
        return render_template("admin.html", users = user_table)
    else:
        return abort(401)


@app.route("/write_note", methods = ["POST"])
def FUN_write_note():
    text_to_write = request.form.get("text_note_to_take")
    write_note_into_db(session['current_user'], text_to_write)
    return redirect(url_for("FUN_private"))


@app.route("/delete_note/<note_id>", methods = ["GET"])
def FUN_delete_note(note_id):
    if session.get("current_user", None) == match_user_id_with_note_id(note_id): # Ensure the current user is NOT operating on other users' note.
        delete_note_from_db(note_id)
    else:
        return abort(401)
    return(redirect(url_for("FUN_private")))


# Reference: http://flask.pocoo.org/docs/0.12/patterns/fileuploads/
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload_image", methods = ['POST'])
def FUN_upload_image():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', category='danger')
            return redirect(url_for("FUN_private"))
        file = request.files['file']
        # if user does not select file, browser also submit a empty part without filename
        if file.filename == '':
            flash('No selected file', category='danger')
            return redirect(url_for("FUN_private"))
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_time = str(datetime.datetime.now())
            image_uid = hashlib.sha1((upload_time + filename).encode()).hexdigest()
            # Save the image into UPLOAD_FOLDER
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_uid + "-" + filename))
            # Record this uploading in database
            image_upload_record(image_uid, session['current_user'], filename, upload_time)
            return redirect(url_for("FUN_private"))

    return redirect(url_for("FUN_private"))


@app.route("/delete_image/<image_uid>", methods = ["GET"])
def FUN_delete_image(image_uid):
    if session.get("current_user", None) == match_user_id_with_image_uid(image_uid): # Ensure the current user is NOT operating on other users' note.
        # delete the corresponding record in database
        delete_image_from_db(image_uid)
        # delete the corresponding image file from image pool
        image_to_delete_from_pool = [y for y in [x for x in os.listdir(app.config['UPLOAD_FOLDER'])] if y.split("-", 1)[0] == image_uid][0]
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete_from_pool))
    else:
        return abort(401)
    return redirect(url_for("FUN_private"))


@app.route("/login", methods = ["POST"])
def FUN_login():
    id_submitted = request.form.get("id").upper()
    if (id_submitted in list_users()) and verify(id_submitted, request.form.get("pw")):
        session['current_user'] = id_submitted
        flash('You are successfully logged in !!', category='SUCCESS')
        return redirect(url_for("welcome"))
    
    else:
        # return(redirect(url_for("FUN_root")))
        return render_template("index.html", wrong_id_pass=True)


@app.route("/logout/")
def FUN_logout():
    session.pop("current_user", None)
    return redirect(url_for("FUN_root"))


@app.route("/delete_user/<id>/", methods = ['GET'])
def FUN_delete_user(id):
    if session.get("current_user", None) == "ADMIN":
        if id == "ADMIN": # ADMIN account can't be deleted.
            return abort(403)

        # [1] Delete this user's images in image pool
        images_to_remove = [x[0] for x in list_images_for_user(id)]
        for f in images_to_remove:
            image_to_delete_from_pool = [y for y in [x for x in os.listdir(app.config['UPLOAD_FOLDER'])] if y.split("-", 1)[0] == f][0]
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_to_delete_from_pool))
        # [2] Delele the records in database files
        delete_user_from_db(id)
        return redirect(url_for("FUN_admin"))
    else:
        return abort(401)


@app.route("/add_user", methods = ["POST"])
def FUN_add_user():
    if session.get("current_user", None) == "ADMIN": # only Admin should be able to add user.
        # before we add the user, we need to ensure this doesn't exist in database.
        # We also need to ensure the id is valid.
        if request.form.get('id').upper() in list_users():
            user_list = list_users()
            all_fields = user_db_all_fields()
            user_table = zip(range(1, len(user_list)+1),\
                            user_list,\
                            [x + y for x,y in zip(["/delete_user/"] * len(user_list), user_list)], all_fields[2])
            return render_template("admin.html", id_to_add_is_duplicated = True, users = user_table)
        if " " in request.form.get('id') or "'" in request.form.get('id') or not request.form.get('id'):   # 3rd condition I have added..for not adding empty string
            user_list = list_users()
            all_fields = user_db_all_fields()
            user_table = zip(range(1, len(user_list)+1),\
                            user_list,\
                            [x + y for x,y in zip(["/delete_user/"] * len(user_list), user_list)], all_fields[2])
            return render_template("admin.html", id_to_add_is_invalid = True, users = user_table)
        else:
            add_user(request.form.get('id'), request.form.get('pw'))
            return redirect(url_for("FUN_admin"))
    else:
        return abort(401)


@app.route('/phonenumber', methods=["GET", "POST"])
def phonenumber():
    if request.method == 'POST':
        number = request.form['Name']
        return render_template('phonenumber_result.html', result=number_lookup(number))
    else:  # GET request
        return render_template('phonenumber.html')


@app.route('/header', methods=["GET", "POST"])
def header():
    return render_template('header.html', ret_equity=gs.ret_equity, ret_debt=gs.ret_debt,
                           ch1_mar_equity=gs.ch1_mar_equity, ch1_mar_debt=gs.ch1_mar_debt,
                           ant_equity=gs.ant_equity, ant_debt=gs.ant_debt)


@app.route('/goal_details/<category>', methods=["GET", "POST"])
def goal_details(category):
    goal_file = paths.blue_bird_mf + 'Simple-financial-planning-sheet.xlsm'
    if category == 'ret':
        excel_to_html(goal_file, sheet_name='Ret-Allocation')
    elif category == 'ch1_mar':
        excel_to_html(goal_file, sheet_name='CH1-Mar')
    elif category == 'ch1_edu':
        excel_to_html(goal_file, sheet_name='CH1-Edu')
    elif category == 'ant':
        excel_to_html(goal_file, sheet_name='Antarctica')
    return render_template('TEMP.html')


# Main execution
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1")

# Ref 1 (login required): https://github.com/kevinhynes/goodbookbadbook/blob/master/application.py
# Ref 2: https://pythonbasics.org/flask-template-data/
# Ref 3: https://www.w3schools.com/css/css_rwd_templates.asp
