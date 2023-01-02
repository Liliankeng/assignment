from flask import Flask, render_template, request, redirect
from pymysql import connections
import os
import boto3
from config import *
import pymysql

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('AddEmp.html')

@app.route("/addemp", methods=['GET', 'POST'])
def addemp():
    return render_template('AddEmp.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Upload image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


@app.route("/getEmp", methods=['GET'])
def getEmp():
    return render_template('GetEmp.html')

@app.route("/getEmp/fetchdata", methods=['POST'])
def fetchdata():

    if (request.form['submit'] == "submit"):
        emp_id = request.form['emp_id']

        select_sql = "SELECT * FROM employee where emp_id = %s"

        cursor = db_conn.cursor()

        try:
            cursor.execute(select_sql, (emp_id))

            if cursor.rowcount == 1:
                data = cursor.fetchall()
                cursor.close()

                return render_template('GetEmp.html', employee = data[0])
            
            else:
                print("Fail to get employee.")

        except Exception as e:
            print(str(e))

        finally:
            cursor.close()

    print("Fail to access the page")
    return  redirect("/getEmp")


@app.route("/edit", methods=['GET'])
def edit_employee():
    return render_template('EditEmp.html')
                               
@app.route('/getEmp/fetchdata/edit/<id>', methods = ['GET'])
def get_employee(id):
    conn = db_conn
    cur = conn.cursor(pymysql.cursors.DictCursor)
  
    cur.execute('SELECT * FROM employee WHERE emp_id = %s', (id))
    data = cur.fetchall()
    cur.close()
    print(data[0])
    return render_template('EditEmp.html', employee = data[0])

@app.route('/update/<id>', methods=['POST'])
def update_employee(id):
    conn = db_conn
    cur = conn.cursor(pymysql.cursors.DictCursor)
    if request.method == 'POST':
        firstName = request.form['first_name']
        lastName = request.form['last_name']
        pri_skill = request.form['pri_skill']
        location = request.form['location']

        cur.execute("""
            UPDATE employee
            SET first_name = %s,
                last_name = %s,
                pri_skill = %s,
                location = %s
            WHERE emp_id = %s
        """, (firstName, lastName, pri_skill, location, id))

        conn.commit()
        return redirect('/getEmp')                             
                     

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
