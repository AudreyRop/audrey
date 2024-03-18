import json
import os
import logging
import random
import nltk
import pickle
import string
import numpy as np
import tensorflow as tf
from home import app, db, login, cache
from flask import render_template, url_for, redirect, request, flash, jsonify, send_file, make_response
from flask_login import current_user, login_required, login_user, logout_user
from tensorflow.keras.preprocessing.sequence import pad_sequences
from home.forms import LoginForm, RegistrationForm, EditProfileForm, ChatBotForm
from home.models import User, Conversation, BankAccount, Transaction, SQLAlchemyError
from datetime import datetime
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from config import tokenizer_file_path, label_encoder_file_path, model_file_path
import csv
import io
import openpyxl
from io import BytesIO

nltk.download('vader_lexicon', quiet=True)
nltk.download('stopwords', quiet=True)
stop_words = set(stopwords.words('english'))

try:
    # Load tokenizer, label encoder, and model
    with open(tokenizer_file_path, 'rb') as token_file:
        # with open('home/tokenizer(1).pkl', 'rb') as token_file:
        tokenizer = pickle.load(token_file)
    with open(label_encoder_file_path, 'rb') as label_file:
        # with open('home/label_encoder(1).pkl', 'rb') as label_file:
        le = pickle.load(label_file)

    if os.path.exists(model_file_path):
        with open(model_file_path, 'rb') as trained_model:
            model = tf.keras.models.load_model(model_file_path)
    else:
        print(f"Error: Model file '{model_file_path}' not found.")
        logging.error(f"Model file '{model_file_path}' not found")
        raise FileNotFoundError(f"Error: Model file '{model_file_path}' not found.")

except FileNotFoundError as e:
    print(e)
    logging.error(e)
except Exception as e:
    print(f"Error during initialization: {e}")
    logging.error(f"Error during initialization: {e}")

try:
    with open('home/mwalimu_sacco.json') as content:
        data1 = json.load(content)
    # data = open('mwalimu_sacco2.json', 'r')

except json.JSONDecodeError as e:
    print(f"JSON decoding error: {e}")
    print(f"Error on line {e.lineno}, column {e.colno}: {e.msg}")
    logging.error(f"JSON decoding error: {e}")
    logging.error(f"Error on line {e.lineno}, column {e.colno}: {e.msg}")
    raise ValueError(f"JSON decoding error: {e}") from None
except FileNotFoundError as e:
    print(e)
    logging.error(e)
except Exception as e:
    print(f"Error during initialization: {e}")
    logging.error(f"Error during initialization: {e}")

data = data1
responses = {}
for intent in data["intents"]:
    responses[intent['tag']] = intent['responses']

# Combine all responses into a single string
all_responses_combined = ' '.join([' '.join(response) for response in responses.values()])

# Split the combine responses into individual words
dataset_words = all_responses_combined.split()

tag_keywords = {
    "loan_inquiry": ["loan", "apply", "requirements", "interest rates", "options", "types"],
    "greeting": ["hello", "hi", "howdy", "hey", "how are you"],
}


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()


def preprocess_input(user_input):
    # Tokenize the input text
    tokens = word_tokenize(user_input)
    # Remove punctuation and stop words
    stop_words = set(stopwords.words('english'))
    processed_text = ' '.join(
        [word.lower() for word in tokens if word.lower() not in stop_words and word.lower() not in string.punctuation])

    return processed_text


@app.route('/', methods=['GET', 'POST'])
@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    form = ChatBotForm()

    try:
        # Handle form submission
        if form.validate_on_submit():
            user_input = form.user_input.data
            processed_input = preprocess_input(user_input)
            input_sequence = tokenizer.texts_to_sequences([processed_input])
            padded_input = pad_sequences(input_sequence, maxlen=model.input_shape[1])
            predictions = model.predict(padded_input)
            predicted_class = np.argmax(predictions)
            predicted_tag = le.inverse_transform([predicted_class])[0]
            # Check if the predicted tag is 'loan_inquiry'
            if predicted_tag == 'loan_inquiry':
                # Handle loan inquiry specific response
                response = random.choice(responses.get(predicted_tag, ['Sorry, I don\'t understand.']))
                response += f"""<br/><br/>Here are some of the loans we offer\
                <br/>
                <hr/>
                <br>
                <a href="https://www.imarishasacco.co.ke/fosa-loans/"">1. FOSA Loan</a>\
                <br/><br>
                <a href="https://www.imarishasacco.co.ke/micro-credit-loans/">2. Micro Credit Loans</a>\
                <br/><br>
                <a href="https://www.imarishasacco.co.ke/bosa-loans/">3. BOSA Loans</a>\
                """
            elif predicted_tag == 'account_types':
                # Handle loan inquiry specific response
                response = random.choice(responses.get(predicted_tag, ['Sorry, I don\'t understand.']))
                response += f"""<br/><br/>Here are some of the loans we offer\
                <br/>
                <hr/>
                <br>
                <a href="https://www.imarishasacco.co.ke/savings-and-services/"">a) Savings Accounts</a>\
                """
            else:
                response = random.choice(responses.get(predicted_tag, ['Sorry, I don\'t understand.']))

            # Handle user clicking on links
            if 'type=FOSA' in user_input:
                response = "Here is the information about FOSA Loan."
            # Handle account-related queries
            if 'balance' in user_input.lower():
                balance = current_user.bank_account.balance
                response = f'Your current account balance is {balance}'
                flash(f'User input contains balance query: {user_input}')
            elif 'transaction history' in user_input.lower():
                # Retrieve transaction history from the database
                transactions = current_user.bank_account.transactions.all()
                print(f'User input contains transaction history query: {user_input}')

                if transactions:
                    response = 'Here is your transaction history:\n'
                    for transaction in transactions:
                        response += f'{transaction.timestamp}: {transaction.amount} - {transaction.transaction_type}\n'
                        response += (f'Download your bank account details: <a '
                                     f'href="/download/transaction_history_info">Transaction history Details</a>')
                        response += f'Download your bank account details to excel: <a href="/download/transaction_history_info_excel">Transaction history Details</a>'
                else:
                    response = 'No transactions found.'
            elif 'bank account info' in user_input.lower() and (
                    'details' in user_input.lower() or 'info' in user_input.lower()):
                bank_account = current_user.bank_account
                if bank_account:
                    response = f'Your bank account details:\nAccount Number: {bank_account.account_number}\nAccount Type: {bank_account.account_type}\nBalance: {bank_account.balance}.\n\n'
                    # download link for the bank account details
                    response += f'Download your bank account details: <a href="/download/bank_account_info">Bank Account Details</a>'
                    response += f'Download your bank account details to excel: <a href="/download/bank_account_info_excel">Bank Account Details</a>'
                else:
                    response = 'You do not have a bank account associated with your account.'
                flash(f'User input contains bank account details query: {user_input}')

            # Save conversation to the database
            try:
                conversation = Conversation(user_input=processed_input, bot_response=response, author=current_user)
                db.session.add(conversation)
                db.session.commit()
                flash('Your conversation has been saved.')
            except SQLAlchemyError as e:
                db.session.rollback()
                logging.error(f'Error saving user conversation: {str(e)}')
                flash('An error occurred while saving the conversation. Please try again.', 'danger')

            # Return response based on request type
            if request.is_json:
                return jsonify({'user_input': user_input, 'response': response})
            else:
                return render_template('chatting.html', form=form, user_input=user_input, response=response)

        # Handle GET requests
        elif request.method == 'GET':
            return render_template('chatting.html', form=form)

        # Handle invalid form submission
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid form submission'}), 400
            else:
                flash('Invalid form submission', 'danger')
                return render_template('chatting.html', form=form)
    except Exception as e:
        flash('An unexpected error occurred. Please try again later.', 'danger')
        logging.error(f'Unexpected error: {str(e)}')
        return render_template('chatting.html', form=form)


def update_models_on_login(user):
    try:
        # Update user's last seen timestamp
        user.last_seen = datetime.utcnow()
        db.session.commit()
        flash('User last seen timestamp updated successfully.')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating last seen timestamp: {str(e)}', 'danger')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Update models here when the user logs in
        update_models_on_login(current_user)
        return redirect(url_for('chatbot'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))

        login_user(user, remember=form.remember_me.data)

        # Update models here when the user logs in
        update_models_on_login(user)

        flash(f'Welcome {user.username}')
        return redirect(url_for('chatbot'))

    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))


# Deposit Simulation
def simulate_deposits(user, num_transactions=10):
    for _ in range(num_transactions):
        amount = round(random.uniform(100, 1000), 2)  # Random deposit amount
        transaction_type = 'deposit'
        Transaction.create_transaction(user.bank_account, amount, transaction_type)
        # Update bank account balance
        user.bank_account.balance += amount
        db.session.commit()


# Recurring Transactions Simulation
def simulate_recurring_transactions(user, num_transactions=5):
    for _ in range(num_transactions):
        transaction_type = random.choice(['utility_bill', 'subscription'])
        amount = round(random.uniform(50, 200), 2)  # Random transaction amount
        Transaction.create_transaction(user.bank_account, amount, transaction_type)
        # Update bank account balance
        if transaction_type == 'withdrawal':
            user.bank_account.balance -= amount
        else:
            user.bank_account.balance += amount
        db.session.commit()


# Interest Accrual Simulation
def simulate_interest_accrual(user, rate=0.02):
    # Calculate interest based on the account balance and interest rate
    interest = round(user.bank_account.balance * rate, 2)
    Transaction.create_transaction(user.bank_account, interest, 'interest_accrual')
    # Update bank account balance
    user.bank_account.balance += interest
    db.session.commit()


# Fee Deductions Simulation
def simulate_fee_deductions(user, num_transactions=3):
    for _ in range(num_transactions):
        amount = round(random.uniform(5, 20), 2)  # Random fee amount
        transaction_type = 'fee'
        Transaction.create_transaction(user.bank_account, -amount, transaction_type)
        # Update bank account balance
        user.bank_account.balance -= amount
        db.session.commit()


# Budget Management Simulation
def simulate_budget_management(user):
    categories = ['groceries', 'dining_out', 'entertainment']
    for _ in range(20):
        category = random.choice(categories)
        amount = round(random.uniform(10, 100), 2)  # Random transaction amount
        Transaction.create_transaction(user.bank_account, -amount, category)
        # Update bank account balance
        user.bank_account.balance -= amount
        db.session.commit()


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('chatbot'))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Check if the username already exists
            existing_user = User.query.filter_by(username=form.username.data).first()
            if existing_user:
                flash('Username already exists. Please choose a different one.', 'danger')
                return redirect(url_for('register'))

            # Check if the email already exists
            existing_email = User.query.filter_by(email=form.email.data).first()
            if existing_email:
                flash('Email address is already registered. Please use a different one.', 'danger')
                return redirect(url_for('register'))

            # Create the new user
            user = User(username=form.username.data, email=form.email.data)
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            # Create a bank account for the new user
            account_number = BankAccount.generate_account_number()
            bank_account = BankAccount(account_number=account_number, user_id=user.id)
            db.session.add(bank_account)
            db.session.commit()

            # Check if bank account has been created successfully
            if bank_account.id:
                flash('Bank account created successfully')
                flash(
                    f'Bank account created successfully for user: {user.username}. Account number: {bank_account.account_number}')

                print(
                    f'Bank account created successfully for user: {user.username}. Account number: {bank_account.account_number}')
                # Query and print bank account details
                bank_account = BankAccount.query.filter_by(user_id=user.id).first()
                if bank_account:
                    print(
                        f"Bank Account Details:\nAccount Number: {bank_account.account_number}\nBalance: {bank_account.balance}\nAccount Type: {bank_account.account_type}")
                else:
                    print("Bank account not found for the user.")
            else:
                flash('Failed to create bank account', 'danger')
                print(f'Failed to create bank account for user: {user.username}')

            flash('Congratulations! Please log in to continue')

            # Simulate transactions for the new user
            simulate_deposits(user)
            simulate_recurring_transactions(user)
            simulate_interest_accrual(user)
            simulate_fee_deductions(user)
            simulate_budget_management(user)

            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            logging.error(f'Error creating bank account for user: {str(e)}')
            flash('An error occurred during registration. Please try again later.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html', title='Register', form=form)


# Cache the results of conversation queries
@cache.cached(timeout=300)  # Cache for 5 minutes (adjust as needed)
def get_conversations(user_id):
    user = User.query.get(user_id)
    return user.conversation.order_by(Conversation.timestamp.desc()).all()


# Invalidate the cache whenever new conversations are added or updated
def invalidate_conversation_cache(user_id):
    cache.delete_memoized(get_conversations, user_id)


# Implement lazy loading combined with pagination
@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    conversation_pagination = user.conversation.order_by(Conversation.timestamp.desc()).paginate(
        page=page, per_page=app.config['CONVERSATIONS_PER_PAGE'], error_out=False)

    # Fetch conversations for the current page
    conversations = conversation_pagination.items
    print(conversations)
    next_url = url_for('user', username=username, page=conversation_pagination.next_num) \
        if conversation_pagination.has_next else None
    prev_url = url_for('chatbot', username=username, page=conversation_pagination.prev_num) \
        if conversation_pagination.has_prev else None

    return render_template(
        'user.html',
        title='Conversation History',
        username=username,
        user=user,
        next_url=next_url,
        prev_url=prev_url,
        conversations=conversations
    )


@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('user', username=current_user.username))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template(
        'edit_profile.html',
        title='Edit Profile',
        form=form
    )


@app.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template(
        'user_popup.html',
        user=user)


@app.route('/download/bank_account_info', methods=['GET'])
@login_required
def download_bank_account_info():
    try:
        # Generate a CSV file with bank account details
        bank_account = current_user.bank_account
        if bank_account:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Account Number', 'Account Type', 'Balance'])
            writer.writerow([bank_account.account_number, bank_account.account_type, bank_account.balance])
            output.seek(0)

            # Create a response with the CSV file as an attachment
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = 'attachment; filename=bank_account_info.csv'
            response.headers['Content-type'] = 'text/csv'
            return response
        else:
            flash('You do not have a bank account associated with your account.', 'danger')
            return redirect(url_for('chatbot'))
    except Exception as e:
        flash('An error occurred while downloading bank account information.', 'danger')
        return redirect(url_for('chatbot'))


@app.route('/download/bank_account_info_excel', methods=['GET'])
@login_required
def download_bank_account_info_excel():
    try:
        # Generate an Excel file with bank account details
        bank_account = current_user.bank_account
        if bank_account:
            # Create a new Excel workbook
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.title = 'Bank Account Info'

            # Add headers
            sheet.append(['Account Number', 'Account Type', 'Balance'])

            # Add data
            sheet.append([bank_account.account_number, bank_account.account_type, bank_account.balance])

            # Save the workbook to a BytesIO object
            excel_file = BytesIO()
            wb.save(excel_file)
            excel_file.seek(0)

            # Return the Excel file as an attachment
            return send_file(excel_file, as_attachment=True, download_name='bank_account_info.xlsx',
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            flash('You do not have a bank account associated with your account.', 'danger')
            return redirect(url_for('chatbot'))
    except Exception as e:
        flash('An error occurred while downloading bank account information.', 'danger')
        return redirect(url_for('chatbot'))


@app.route('/download/transaction_history_info', methods=['GET'])
@login_required
def download_transaction_history_info_csv():
    try:
        # Generate a CSV file with transaction history details
        transactions = current_user.bank_account.transactions.all()
        if transactions:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Transaction Timestamp', 'Transaction Amount', 'Transaction Type'])

            for transaction in transactions:
                timestamp_str = transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([timestamp_str, transaction.amount, transaction.transaction_type])

            output.seek(0)

            # Create a response with the CSV file as an attachment
            response = make_response(output.getvalue())
            response.headers['Content-Disposition'] = 'attachment; filename=transaction_history_info.csv'
            response.headers['Content-Type'] = 'text/csv'
            return response
        else:
            flash('You do not have any transactions associated with your account.', 'danger')
            return redirect(url_for('chatbot'))
    except Exception as e:
        flash('An error occurred while downloading transaction history information.', 'danger')
        return redirect(url_for('chatbot'))


@app.route('/download/transaction_history_info_excel', methods=['GET'])
@login_required
def download_transaction_history_info_excel():
    try:
        # Generate an Excel file with transaction history details
        transactions = current_user.bank_account.transactions.all()
        if transactions:
            # Create a new Excel workbook
            wb = openpyxl.Workbook()
            sheet = wb.active
            sheet.title = 'Transaction History'

            # Add headers
            sheet.append(['Transaction Timestamp', 'Transaction Amount', 'Transaction Type'])

            # Add data
            for transaction in transactions:
                timestamp_str = transaction.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                sheet.append([timestamp_str, transaction.amount, transaction.transaction_type])

            # Save the workbook to a BytesIO object
            excel_file = BytesIO()
            wb.save(excel_file)
            excel_file.seek(0)

            # Return the Excel file as an attachment
            return send_file(excel_file, as_attachment=True, download_name='transaction_history_info.xlsx',
                             mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        else:
            flash('You do not have any transactions associated with your account.', 'danger')
            return redirect(url_for('chatbot'))
    except Exception as e:
        flash('An error occurred while downloading transaction history information.', 'danger')
        return redirect(url_for('chatbot'))


# Flask Route to handle download of FOSA Loan PDF
@app.route('/download/fosa_loan_pdf')
@login_required
def download_fosa_loan_pdf():
    # Path to the PDF file
    pdf_path = 'BOSA_LOAN_FORMS.pdf'

    # Return the PDF file as a response
    return send_file(pdf_path, as_attachment=True)


# Flask Route to handle download of FOSA Loan PDF
@app.route('/download/bosa_loan_pdf')
@login_required
def download_bosa_loan_pdf():
    # Path to the PDF file
    pdf_path = 'BOSA_LOAN_FORMS.pdf'

    # Return the PDF file as a response
    return send_file(pdf_path, as_attachment=True)
