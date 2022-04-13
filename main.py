"""Setup at app startup"""
import os
import sqlalchemy
from flask import Flask, redirect, render_template, request, url_for
from yaml import load, Loader

import pymysql

db_user = os.environ.get('CLOUD_SQL_USERNAME')
db_password = os.environ.get('CLOUD_SQL_PASSWORD')
db_name = os.environ.get('CLOUD_SQL_DATABASE_NAME')
db_connection_name = os.environ.get('CLOUD_SQL_CONNECTION_NAME')
cusrorType      = pymysql.cursors.DictCursor


def init_connection_engine():
    """ initialize database setup
    Takes in os variables from environment if on GCP
    Reads in local variables that will be ignored in public repository.
    Returns:
        pool -- a connection to GCP MySQL
    """
    if os.environ.get('GAE_ENV') == 'standard':
        # If deployed, use the local socket interface for accessing Cloud SQL
        unix_socket = '/cloudsql/{}'.format(db_connection_name)
        conn = pymysql.connect(user=db_user, password=db_password,
                              unix_socket=unix_socket, db=db_name, cursorclass=cusrorType)
    else:
        # If running locally, use the TCP connections instead
        # Set up Cloud SQL Proxy (cloud.google.com/sql/docs/mysql/sql-proxy)
        # so that your application can use 127.0.0.1:3306 to connect to your
        # Cloud SQL instance
        host = '127.0.0.1'
        conn = pymysql.connect(user=db_user, password=db_password,
                              host=host, db=db_name, cursorclass=cusrorType)

    return conn


app = Flask(__name__)
# db = init_connection_engine()


@app.route("/")
def home():
    """ Show all data"""
    todo_list =[]
    conn = init_connection_engine()
    cur = conn.cursor()
    cur.execute('Select * from todo;')
    rows = cur.fetchall()
    for row in rows:
        item = {
            "id": row['id'],
            "title": row['title'],
            "complete": row['complete']
        }
        todo_list.append(item)
    print(todo_list)
    return render_template('base.html', todo_list=todo_list)
    

@app.route("/add", methods=['POST'])
def add():
    """Adding new task"""
    title = request.form.get("title") #get from form
    conn = init_connection_engine()
    query = 'Insert Into todo (title) VALUES ("{}");'.format(title)
    cur = conn.cursor()
    cur.execute(query)
    conn.commit()
    conn.close()
    return redirect(url_for("home"))


@app.route("/delete/<int:todo_id>")
def delete(todo_id):
    """deleting created task"""
    conn = init_connection_engine()
    cur = conn.cursor()
    #print(todo_id)
    query = 'Delete From todo where id={};'.format(todo_id)
    cur.execute(query)
    conn.commit()
    conn.close()
    
    return redirect(url_for("home"))

@app.route("/update/<todo_id>")
def update(todo_id):
    """updating the created task"""
    #print(todo_id)
    unix_socket = '/cloudsql/{}'.format(db_connection_name)
    conn = pymysql.connect(user=db_user, password=db_password,
                              unix_socket=unix_socket, db=db_name, cursorclass=cusrorType)
    cur = conn.cursor()
    status = cur.execute('select complete from todo where id = {};'.format(todo_id))
    print(status)
    if status == 0:
        #print("Status is non completed and setting to complete")
        query = 'Update todo set complete = "{}" where id = {};'.format(1, todo_id)
        cur.execute(query)
        conn.commit()
        
    else:
        #print("status is completed and setting to non complete")
        query = 'Update todo set complete = "{}" where id = {};'.format(0, todo_id)
        cur.execute(query)
        conn.commit()
        
    conn.close()

    return redirect(url_for("home"))


if __name__ == '__main__':
    # db.create_all()

    app.run(host='127.0.0.1', port=8080, debug=True)
