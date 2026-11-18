from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import Email, EqualTo, InputRequired, Length, Regexp


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            InputRequired(),
            Length(min=3, max=30),
            Regexp(r"^[A-Za-z0-9_.-]+$", message="Use letters, numbers, dots, dashes, or underscores."),
        ],
    )
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=12, max=128)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[InputRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[InputRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[InputRequired(), Length(max=128)])
    remember_me = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class ProfileForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            InputRequired(),
            Length(min=3, max=30),
            Regexp(r"^[A-Za-z0-9_.-]+$", message="Use letters, numbers, dots, dashes, or underscores."),
        ],
    )
    submit = SubmitField("Save changes")
