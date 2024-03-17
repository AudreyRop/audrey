from home.models import User, Conversation, BankAccount, Transaction, SQLAlchemyError


bank_account = BankAccount.query.filter_by(user_id=user.id).first()
if bank_account:
    print(f"Bank Account Details:\nAccount Number: {bank_account.account_number}\nBalance: {bank_account.balance}\nAccount Type: {bank_account.account_type}")
else:
    print("Bank account not found for the user.")