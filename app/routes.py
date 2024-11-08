from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .forms import RegistrationForm, LoginForm
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from .models import db, Feedback
from .etl import etl
import logging
logging.basicConfig(level=logging.INFO)

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        new_user = User(username=form.username.data, password=hashed_password, role=form.role.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))
    return render_template('register.html', form=form)
@auth.route('/',methods=['POST','GET'])
def home():
    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('auth.dashboard'))
        else:
            flash('Please check your login details and try again.')
    return render_template('login.html', form=form)

@auth.route('/dashboard')
@login_required
def dashboard():
    # Passing the current user to the template, so you can access 'current_user.role'
    return render_template('dashboard.html', current_user=current_user)

# Inside auth Blueprint file, e.g., auth.py
@auth.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'administrator':
        return redirect(url_for('dashboard'))  # Redirect if user is not an admin
    
    users = User.query.all()  # Fetch all users from the database
    return render_template('manage_users.html', users=users)

@auth.route('/upload_data', methods=['POST', 'GET'])
@login_required
def upload_data():
    if current_user.role != 'administrator':
        return redirect(url_for('dashboard'))


    df = pd.DataFrame()
    
    if request.method == 'POST':
        csv_file = request.files.get("csv_file")
        xlsx_file = request.files.get("xlsx_file")
        json_file = request.files.get("json_file")
        html_file = request.files.get("html_file")
        txt_file = request.files.get("txt_file")

        if not any([csv_file, xlsx_file, json_file, html_file, txt_file]):
            return "Please upload at least one file."

        try:
            # Load each file into a DataFrame if present
            df_xlsx = pd.read_excel(xlsx_file) if xlsx_file else pd.DataFrame()
            df_csv = pd.read_csv(csv_file) if csv_file else pd.DataFrame()
            df_json = pd.read_json(json_file) if json_file else pd.DataFrame()
            df_txt = pd.read_csv(txt_file, delimiter="\t") if txt_file else pd.DataFrame()
            df_html = pd.read_html(html_file) if html_file else pd.DataFrame()
            df = pd.concat([df_csv, df_json, df_html, df_xlsx, df_txt], ignore_index=True)
            logging.info("Data loaded successfully.")

            etl.etl(df)
        except Exception as e:
            logging.error(f"Error loading data: {e}")
            return "An error occurred while loading the data."
        
        return redirect(url_for('auth.dashboard'))
    
    return render_template('upload_data.html', df=df)




@auth.route('/view_data')
@login_required
def view_data():

    try:
        feedback_records = Feedback.query.all()
        if not feedback_records:
            return render_template('dashboard.html', error="No data available to display.")
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return render_template('dashboard.html', error="Error fetching data.")

    # Prepare data for plotting
    data = {
        "Date": [record.date for record in feedback_records],
        "Source": [record.source for record in feedback_records],
        "Feedback Text": [record.feedback_text for record in feedback_records],
        "Sentiment Score": [record.sentiment_score for record in feedback_records],
        "Product/Service Category": [record.product_service_category for record in feedback_records],
        "Rating": [record.rating for record in feedback_records],
        "Feedback Length": [record.feedback_length for record in feedback_records],
        "Sentiment Category": [record.sentiment_category for record in feedback_records],
        "Sentiment Numeric": [record.sentiment_numeric for record in feedback_records]
    }
    df = pd.DataFrame(data)

    def create_plot(plot_func):
        buffer = BytesIO()
        plot_func()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        plt.close()
        return img_base64

    plots = {}

    # Administrator has access to all charts
    if current_user.role == 'administrator':
        plots['sentiment_by_source'] = create_plot(
            lambda: sns.countplot(x="Source", hue="Sentiment Score", data=df).set_title("Sentiment by Source")
        )
        plots['rating_distribution'] = create_plot(
            lambda: sns.histplot(df["Rating"], bins=5).set_title("Rating Distribution")
        )
        plots['feedback_length'] = create_plot(
            lambda: sns.boxplot(x="Source", y="Feedback Length", data=df).set_title("Feedback Length by Source")
        )
        plots['feedback_by_category'] = create_plot(
            lambda: sns.countplot(x="Product/Service Category", data=df).set_title("Feedback by Product/Service Category")
        )
        plots['sentiment_numeric_trend'] = create_plot(
            lambda: sns.lineplot(x="Date", y="Sentiment Numeric", data=df).set_title("Sentiment Trend Over Time")
        )
        plots['sentiment_rating_relation'] = create_plot(
            lambda: sns.scatterplot(x="Rating", y="Sentiment Numeric", data=df).set_title("Sentiment vs. Rating")
        )
        plots['feedback_word_count'] = create_plot(
            lambda: sns.histplot(df["Feedback Length"], bins=10).set_title("Distribution of Feedback Length")
        )

    # Developer has access to a subset of charts
    elif current_user.role == 'developer':
        plots['sentiment_by_source'] = create_plot(
            lambda: sns.countplot(x="Source", hue="Sentiment Score", data=df).set_title("Sentiment by Source")
        )
        plots['feedback_by_category'] = create_plot(
            lambda: sns.countplot(x="Product/Service Category", data=df).set_title("Feedback by Product/Service Category")
        )
        plots['sentiment_numeric_trend'] = create_plot(
            lambda: sns.lineplot(x="Date", y="Sentiment Numeric", data=df).set_title("Sentiment Trend Over Time")
        )
        plots['sentiment_rating_relation'] = create_plot(
            lambda: sns.scatterplot(x="Rating", y="Sentiment Numeric", data=df).set_title("Sentiment vs. Rating")
        )

    # Customer has limited access to essential charts
    elif current_user.role == 'customer':
        plots['sentiment_by_source'] = create_plot(
            lambda: sns.countplot(x="Source", hue="Sentiment Score", data=df).set_title("Sentiment by Source")
        )
        plots['feedback_by_category'] = create_plot(
            lambda: sns.countplot(x="Product/Service Category", data=df).set_title("Feedback by Product/Service Category")
        )
        plots['sentiment_numeric_trend'] = create_plot(
            lambda: sns.lineplot(x="Date", y="Sentiment Numeric", data=df).set_title("Sentiment Trend Over Time")
        )

    return render_template('view_data.html', plots=plots, user_role=current_user.role)


@auth.route('/administrator')
@login_required
def admin():
    if not current_user.has_permission('administrator'):
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.dashboard'))
    return "Admin Dashboard"

# Logout route
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth.login'))


@auth.route('/change_role/<int:user_id>', methods=['POST'])
def change_role(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to change user roles.')
        return redirect(url_for('auth.manage_users'))

    user = User.query.get(user_id)
    if user:
        new_role = request.form.get('role')  # if role comes from a form submission
        user.role = new_role
        try:
            db.session.commit()
            flash(f"User role updated to {new_role} successfully.")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the role. Please try again.")
            print(e)
    else:
        flash('User not found.')

    return redirect(url_for('auth.manage_users'))



@auth.route('/delete_user/<int:user_id>', methods=['GET'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully!', 'success')
    else:
        flash('User not found!', 'danger')
    return redirect(url_for('auth.manage_users'))