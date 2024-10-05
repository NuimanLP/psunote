import flask

import models
import forms


app = flask.Flask(__name__)
app.config["SECRET_KEY"] = "This is secret key"
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = "postgresql://coe:CoEpasswd@localhost:5432/coedb"

models.init_app(app)


@app.route("/")
def index():
    db = models.db
    notes = db.session.execute(
        db.select(models.Note).order_by(models.Note.title)
    ).scalars()
    return flask.render_template(
        "index.html",
        notes=notes,
    )


@app.route("/notes/create", methods=["GET", "POST"])
def notes_create():
    form = forms.NoteForm()
    if not form.validate_on_submit():
        print("error", form.errors)
        return flask.render_template(
            "notes-create.html",
            form=form,
        )
    note = models.Note()
    form.populate_obj(note)
    note.tags = []

    db = models.db
    for tag_name in form.tags.data:
        tag = (
            db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
            .scalars()
            .first()
        )

        if not tag:
            tag = models.Tag(name=tag_name)
            db.session.add(tag)

        note.tags.append(tag)

    db.session.add(note)
    db.session.commit()

    return flask.redirect(flask.url_for("index"))


@app.route("/tags/<tag_name>")
def tags_view(tag_name):
    db = models.db
    tag = (
        db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
        .scalars()
        .first()
    )
    if tag is None:
        flask.abort(404)

    notes = db.session.execute(
        db.select(models.Note).where(models.Note.tags.any(id=tag.id))
    ).scalars()

    return flask.render_template(
        "tags-view.html",
        tag_name=tag_name,
        notes=notes,
    )


@app.route('/notes/<int:note_id>/edit', methods=['GET', 'POST'])
def edit_note(note_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalar_one_or_none()
    if note is None:
        flask.abort(404)

    form = forms.NoteForm(obj=note)

    if form.validate_on_submit():
        note.title = form.title.data
        note.description = form.description.data
        note.tags = []

        for tag_name in form.tags.data:
            if isinstance(tag_name, models.Tag):
                tag_name = tag_name.name

            tag = (
                db.session.execute(db.select(models.Tag).where(models.Tag.name == tag_name))
                .scalars()
                .first()
            )

            if not tag:
                tag = models.Tag(name=tag_name)
                db.session.add(tag)

            note.tags.append(tag)

        db.session.commit()
        flask.flash('Note updated successfully!', 'success')
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('notes-create.html', form=form, note=note)


@app.route('/tags/<int:tag_id>/edit', methods=['GET', 'POST'])
def edit_tag(tag_id):
    db = models.db
    tag = db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id)).scalar_one_or_none()
    if tag is None:
        flask.abort(404)

    form = forms.TagForm(obj=tag)

    if form.validate_on_submit():
        tag.name = form.name.data
        db.session.commit()
        flask.flash('Tag updated successfully!', 'success')
        return flask.redirect(flask.url_for('index'))

    return flask.render_template('tags-edit.html', form=form, tag=tag)


@app.route('/notes/<int:note_id>/delete', methods=['POST'])
def delete_note(note_id):
    db = models.db
    note = db.session.execute(db.select(models.Note).where(models.Note.id == note_id)).scalar_one_or_none()
    if note is None:
        flask.abort(404)

    db.session.delete(note)
    db.session.commit()
    flask.flash('Note deleted successfully!', 'success')
    return flask.redirect(flask.url_for('index'))


@app.route('/tags/<int:tag_id>/delete', methods=['POST'])
def delete_tag(tag_id):
    db = models.db
    tag = db.session.execute(db.select(models.Tag).where(models.Tag.id == tag_id)).scalar_one_or_none()
    if tag is None:
        flask.abort(404)

    db.session.delete(tag)
    db.session.commit()
    flask.flash('Tag deleted successfully!', 'success')
    return flask.redirect(flask.url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)