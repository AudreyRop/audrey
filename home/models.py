from home import db, login, app
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, Numeric, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from datetime import datetime
from hashlib import md5
from sqlalchemy.exc import SQLAlchemyError
from flask import (
    jsonify, flash
)
from sqlalchemy import ForeignKey
import random
import string
import logging


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.errorhandler(SQLAlchemyError)
def handle_database_error(e):
    # Log error
    app.logger.error(f'Database error: {str(e)}')
    # user-friendly response
    return jsonify({'error': f'A database error occurred {str(e)}'}), 500


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    about_me = db.Column(db.String(120))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    conversation = db.relationship('Conversation', backref='author', lazy='dynamic')
    bank_account = db.relationship('BankAccount', uselist=False)

    def __repr__(self):
        return f'User: {self.username}'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def create_bank_account(self):
        try:
            account = BankAccount(owner=self)
            db.session.add(account)
            db.session.commit()
            flash('Bank account created successfully.')
            print(f'Bank account created successfully: {account}')
            print(f'Bank account owner: {account.user_id}')
            return account
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating bank account: {e}', 'danger')
            print(f'Error creating bank account: {e}')
            return None


class Conversation(db.Model):
    __tablename__ = 'conversation'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_input = db.Column(db.String(1000))
    bot_response = db.Column(db.String(1000))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __repr__(self):
        return f"<Conversation {self.id}>"


class BankAccount(db.Model):
    __tablename__ = 'bank_account'
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, index=True)
    account_type = db.Column(db.String(64), index=True)
    balance = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    transactions = db.relationship('Transaction', backref='bank_account', lazy='dynamic')


    def __repr__(self):
        return f"<BankAccount {self.id}>"

    @staticmethod
    def generate_account_number():
        # Generate a unique account number
        # Format: ACCT-XXXX-XXXX-XXXX (e.g., ACCT-1234-5678-9012)
        account_number = 'ACCT-'
        account_number += ''.join(random.choices(string.digits, k=4)) + '-'  # Random 4-digit group
        account_number += ''.join(random.choices(string.digits, k=4)) + '-'  # Random 4-digit group
        account_number += ''.join(random.choices(string.digits, k=4))  # Random 4-digit group
        return account_number


class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float)
    transaction_type = db.Column(db.String(64))
    account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'))

    # Define the relationship with tags
    tags = db.relationship('TransactionTag', secondary='transaction_tag_association', back_populates='transactions')

    def __repr__(self):
        return f"<Transaction {self.id}>"

    @staticmethod
    def create_transaction(account, amount, transaction_type):
        transaction = Transaction(account_id=account.id, amount=amount, transaction_type=transaction_type)
        db.session.add(transaction)


class TransactionCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(255))


class TransactionTag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(255))

    # Define a many-to-many relationship with transactions
    transactions = db.relationship('Transaction', secondary='transaction_tag_association', back_populates='tags')


transaction_tag_association = db.Table('transaction_tag_association',
                                       db.Column('transaction_id', db.Integer, db.ForeignKey('transactions.id')),
                                       db.Column('tag_id', db.Integer, db.ForeignKey('transaction_tag.id'))
                                       )


class TransactionStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True, unique=True)
    description = db.Column(db.String(255))


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20))  # e.g., 'sent', 'unread', 'read'

    def __repr__(self):
        return f'<Notification {self.id}>'
