# How to start the backend

In the `backend` directory,

1. create virtual environment
$ python3 -m venv venv

2. activate python virtual environment
mac/linux: $ source venv/bin/activate
windows: $ .\venv\Scripts\activate

4. pip update
mac/linux: $ pip install --upgrade pip
windows: $ python -m pip install --upgrade pip

5. pip install dependencies
$ pip install -r requirements.txt

6. run the flask app
mac/linux: $ export FLASK_APP=queueHandler
windows: $ set FLASK_APP=queueHandler

then,
$ flask run