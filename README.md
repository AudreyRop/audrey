#Flask chatbot App

## Features

- User Registration and authentication
- Profile popovers
- chatbot
- chat hhistory

## Tools Used
- Tensorflow
- nltk
- scikit-learn
- Flask framework
- Python for programming
- Flask-Bootstrap
- Flask-WTF
- Flask-SQLAlchemy
- Flask-Login
- Flask-Migrate
- Flask-Moment
- Email validator
- Python-dotenv
- Ajax requests


You can use the following credentials to test the deployed application:
* Username: admin
* Password: 12341234

## Testing the Application Locally

1. Clone this repository:

    ```python
    $ git clone git@github.com:GitauHarrison/flask-popovers.git
    ```
<br>

2. Change into the directory:

    ```python
    $ cd flask-popovers
    ```
<br>

3. Create and activate a virtual environment:

    ```python
    $ virtualenv venv
    $ source venv/bin/activate

    # Alternatively, you can use virtualenvwrapper
    $ mkvirtualenv venv
    ```
4. Install dependencies:
    
    ```python
    (venv)$ pip install -r requirements.txt
    ```
<br>

5. Add environment variables as seen in the `.env-template`:
    
    ```python
    (venv)$ cp .env-template .env
    ```

    * You can get a random value for your `SECRET_KEY` by running `python -c "import os; print os.urandom(24)"` in your terminal.
<br>

5. Run the application:

    ```python
    (venv)$ flask run
    ```
<br>

6. Open the application in your favourte browser by copying and pasting the link below:
   * http://localhost:5000
<br>

7. Feel free to create a new user and see the popovers in action. You can do so by [registering a user](http://127.0.0.1:5000/register) then [logging in](http://127.0.0.1:5000/login).

# audrey
