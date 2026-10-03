from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector

app = Flask(__name__)

# Secret key for session
app.secret_key = "college-placement-secret-key"


# --------------------------------
# MySQL Database Connection
# --------------------------------
def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Manojshetty@13",
        database="college_placement"
    )
    return connection


# --------------------------------
# Home Page
# --------------------------------
@app.route("/")
def home():

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template(
        "index.html",
        student_count=student_count
    )


## --------------------------------
# Student Registration
# --------------------------------
@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        phone = request.form["phone"]
        department = request.form["department"]
        graduation_year = request.form["graduation_year"]
        cgpa = request.form["cgpa"]

        # Hash the password before saving
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO students
        (name, email, password, phone, department, graduation_year, cgpa)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            email,
            hashed_password,
            phone,
            department,
            graduation_year,
            cgpa
        )

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return """
        <h1>Registration Successful!</h1>
        <p>Student has been registered successfully.</p>

        <a href="/login">Go to Login</a>
        <br><br>

        <a href="/">Go to Home</a>
        """

    return render_template("register.html")
# --------------------------------
# Student Login
# --------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE email = %s",
            (email,)
        )

        student = cursor.fetchone()

        if student:

            stored_password = student["password"]

            # Check hashed password
            password_correct = check_password_hash(
                stored_password,
                password
            )

            # Support old plain-text passwords one time
            if not password_correct and stored_password == password:

                new_password = generate_password_hash(password)

                cursor.execute(
                    """
                    UPDATE students
                    SET password = %s
                    WHERE id = %s
                    """,
                    (new_password, student["id"])
                )

                connection.commit()

                password_correct = True

            if password_correct:

                session["student_id"] = student["id"]
                session["student_name"] = student["name"]

                cursor.close()
                connection.close()

                return redirect("/dashboard")

        cursor.close()
        connection.close()

        return """
        <h1>Invalid Email or Password</h1>
        <a href="/login">Try Again</a>
        """

    return render_template("login.html")

# --------------------------------
# Student Dashboard
# --------------------------------
@app.route("/dashboard")
def dashboard():

    if "student_id" not in session:
        return redirect("/login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE id = %s",
        (session["student_id"],)
    )

    student = cursor.fetchone()

    cursor.close()
    connection.close()

    if not student:
        session.clear()
        return redirect("/login")

    return render_template("dashboard.html", student=student)

# --------------------------------
# Company Registration
# --------------------------------
@app.route("/company-register", methods=["GET", "POST"])
def company_register():

    if request.method == "POST":

        company_name = request.form["company_name"]
        email = request.form["email"]
        phone = request.form["phone"]
        location = request.form["location"]
        password = request.form["password"]

        # Hash password before saving
        hashed_password = generate_password_hash(password)

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO companies
        (company_name, email, phone, location, password)
        VALUES (%s, %s, %s, %s, %s)
        """

        values = (
            company_name,
            email,
            phone,
            location,
            hashed_password
        )

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return """
        <h1>Company Registration Successful!</h1>
        <p>Company has been registered successfully.</p>

        <a href="/company-login">Go to Company Login</a>
        <br><br>

        <a href="/">Go to Home</a>
        """

    return render_template("company_register.html")
# --------------------------------
# Post Job
# --------------------------------
@app.route("/post-job", methods=["GET", "POST"])
def post_job():

    if request.method == "POST":

        company_id = request.form["company_id"]
        job_title = request.form["job_title"]
        job_description = request.form["job_description"]
        required_skills = request.form["required_skills"]
        location = request.form["location"]
        salary = request.form["salary"]
        last_date = request.form["last_date"]

        connection = get_db_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO jobs
        (company_id, job_title, job_description, required_skills, location, salary, last_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        values = (
            company_id,
            job_title,
            job_description,
            required_skills,
            location,
            salary,
            last_date
        )

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return """
        <h1>Job Posted Successfully!</h1>
        <p>The job has been added to the database.</p>
        <br>
        <a href="/post-job">Post another job</a>
        <br><br>
        <a href="/">Go to Home</a>
        """

    return render_template("post_job.html")
# --------------------------------
# View and Search Jobs
# --------------------------------
# --------------------------------
# View and Search Jobs
# --------------------------------
@app.route("/jobs")
def jobs():

    search = request.args.get("search", "").strip()

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if search:

        query = """
        SELECT
            jobs.id,
            jobs.job_title,
            jobs.job_description,
            jobs.required_skills,
            jobs.location,
            jobs.salary,
            jobs.last_date,
            jobs.min_cgpa,
            jobs.department,
            companies.company_name
        FROM jobs
        JOIN companies
            ON jobs.company_id = companies.id
        WHERE
            jobs.job_title LIKE %s
            OR jobs.required_skills LIKE %s
            OR jobs.location LIKE %s
        ORDER BY jobs.id DESC
        """

        search_value = "%" + search + "%"

        cursor.execute(
            query,
            (search_value, search_value, search_value)
        )

    else:

        query = """
        SELECT
            jobs.id,
            jobs.job_title,
            jobs.job_description,
            jobs.required_skills,
            jobs.location,
            jobs.salary,
            jobs.last_date,
            jobs.min_cgpa,
            jobs.department,
            companies.company_name
        FROM jobs
        JOIN companies
            ON jobs.company_id = companies.id
        ORDER BY jobs.id DESC
        """

        cursor.execute(query)

    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    student_cgpa = 0
    student_department = ""

    if "student_id" in session:

        connection2 = get_db_connection()
        cursor2 = connection2.cursor()

        cursor2.execute(
            "SELECT cgpa, department FROM students WHERE id = %s",
            (session["student_id"],)
        )

        result = cursor2.fetchone()

        if result:
            if result[0] is not None:
                student_cgpa = float(result[0])

            if result[1] is not None:
                student_department = result[1].strip().lower()

        cursor2.close()
        connection2.close()

    return render_template(
        "jobs.html",
        jobs=jobs,
        search=search,
        student_cgpa=student_cgpa,
        student_department=student_department
    )

# --------------------------------
# Apply for a Job
# --------------------------------
@app.route("/apply/<int:job_id>", methods=["POST"])
def apply_job(job_id):

    if "student_id" not in session:
        return redirect("/login")

    student_id = session["student_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    # Check whether student already applied
    check_query = """
    SELECT id FROM applications
    WHERE student_id = %s AND job_id = %s
    """

    cursor.execute(check_query, (student_id, job_id))
    existing_application = cursor.fetchone()

    if existing_application:
        cursor.close()
        connection.close()

        return """
        <h1>Already Applied</h1>
        <p>You have already applied for this job.</p>
        <a href="/jobs">Back to Jobs</a>
        """

    # Save application
    query = """
    INSERT INTO applications (student_id, job_id)
    VALUES (%s, %s)
    """

    cursor.execute(query, (student_id, job_id))
    connection.commit()

    cursor.close()
    connection.close()

    return """
    <h1>Application Submitted!</h1>
    <p>Your job application has been submitted successfully.</p>
    <a href="/jobs">Back to Jobs</a>
    """
# --------------------------------
# My Applications
# --------------------------------
@app.route("/my-applications")
def my_applications():

    if "student_id" not in session:
        return redirect("/login")

    student_id = session["student_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT
        applications.id,
        applications.application_date,
        applications.status,
        jobs.job_title,
        jobs.location,
        companies.company_name
    FROM applications
    JOIN jobs
        ON applications.job_id = jobs.id
    JOIN companies
        ON jobs.company_id = companies.id
    WHERE applications.student_id = %s
    ORDER BY applications.id DESC
    """

    cursor.execute(query, (student_id,))
    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "my_applications.html",
        applications=applications
    )
# --------------------------------
# Admin Dashboard
# --------------------------------
# --------------------------------
# Admin Dashboard
# --------------------------------
@app.route("/admin")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM companies")
    company_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM jobs")
    job_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM applications")
    application_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Selected'"
    )
    selected_count = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM applications WHERE status = 'Rejected'"
    )
    rejected_count = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return render_template(
        "admin_dashboard.html",
        student_count=student_count,
        company_count=company_count,
        job_count=job_count,
        application_count=application_count,
        selected_count=selected_count,
        rejected_count=rejected_count
    )
# --------------------------------
# Admin - View Students
# --------------------------------
@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM students ORDER BY id DESC")
    students = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_students.html",
        students=students
    )
# --------------------------------
# Admin - View Companies
# --------------------------------
@app.route("/admin/companies")
def admin_companies():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("SELECT * FROM companies ORDER BY id DESC")
    companies = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_companies.html",
        companies=companies
    )
# --------------------------------
# Admin - View Jobs
# --------------------------------
@app.route("/admin/jobs")
def admin_jobs():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT
        jobs.id,
        jobs.job_title,
        jobs.required_skills,
        jobs.location,
        jobs.salary,
        jobs.last_date,
        companies.company_name
    FROM jobs
    JOIN companies
        ON jobs.company_id = companies.id
    ORDER BY jobs.id DESC
    """

    cursor.execute(query)
    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_jobs.html",
        jobs=jobs
    )
# --------------------------------
# Admin - View Applications
# --------------------------------
@app.route("/admin/applications")
def admin_applications():

    if "admin_id" not in session:
        return redirect("/admin-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT
        applications.id,
        applications.application_date,
        applications.status,
        students.name AS student_name,
        students.email AS student_email,
        jobs.job_title,
        companies.company_name
    FROM applications
    JOIN students
        ON applications.student_id = students.id
    JOIN jobs
        ON applications.job_id = jobs.id
    JOIN companies
        ON jobs.company_id = companies.id
    ORDER BY applications.id DESC
    """

    cursor.execute(query)
    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "admin_applications.html",
        applications=applications
    )
# --------------------------------
# Admin - Update Application Status
# --------------------------------
@app.route(
    "/admin/application/<int:application_id>/status",
    methods=["POST"]
)
def update_application_status(application_id):

    status = request.form["status"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    UPDATE applications
    SET status = %s
    WHERE id = %s
    """

    cursor.execute(query, (status, application_id))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/admin/applications")
# --------------------------------
# Student Logout
# --------------------------------
@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
# --------------------------------
# Company Login
# --------------------------------
@app.route("/company-login", methods=["GET", "POST"])
def company_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM companies WHERE email = %s",
            (email,)
        )

        company = cursor.fetchone()

        if company:

            stored_password = company["password"]

            # Check hashed password
            password_correct = check_password_hash(
                stored_password,
                password
            )

            # Upgrade old plain-text password automatically
            if not password_correct and stored_password == password:

                new_password = generate_password_hash(password)

                cursor.execute(
                    """
                    UPDATE companies
                    SET password = %s
                    WHERE id = %s
                    """,
                    (new_password, company["id"])
                )

                connection.commit()

                password_correct = True

            if password_correct:

                session["company_id"] = company["id"]
                session["company_name"] = company["company_name"]

                cursor.close()
                connection.close()

                return redirect("/company-dashboard")

        cursor.close()
        connection.close()

        return """
        <h1>Invalid Email or Password</h1>
        <a href="/company-login">Try Again</a>
        """

    return render_template("company_login.html")


# --------------------------------
# Company Dashboard
# --------------------------------
@app.route("/company-dashboard")
def company_dashboard():

    if "company_id" not in session:
        return redirect("/company-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM companies WHERE id = %s",
        (session["company_id"],)
    )

    company = cursor.fetchone()

    cursor.close()
    connection.close()

    if not company:
        session.clear()
        return redirect("/company-login")

    return render_template(
        "company_dashboard.html",
        company=company
    )
        # --------------------------------
# Company Logout
# --------------------------------
@app.route("/company-logout")
def company_logout():

    session.pop("company_id", None)
    session.pop("company_name", None)

    return redirect("/company-login")



@app.route("/company/jobs")
def company_jobs():

    if "company_id" not in session:
        return redirect("/company-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT *
    FROM jobs
    WHERE company_id = %s
    ORDER BY id DESC
    """

    cursor.execute(query, (session["company_id"],))
    jobs = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "company_jobs.html",
        jobs=jobs
    )
# --------------------------------
# Company - My Posted Jobs
# --------------------------------
# --------------------------------
# Company - View Applicants
# --------------------------------
@app.route("/company/applications")
def company_applications():

    if "company_id" not in session:
        return redirect("/company-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
    SELECT
        applications.id,
        applications.status,
        students.name AS student_name,
        students.email AS student_email,
        students.department,
        students.cgpa,
        jobs.job_title
    FROM applications
    JOIN students
        ON applications.student_id = students.id
    JOIN jobs
        ON applications.job_id = jobs.id
    WHERE jobs.company_id = %s
    ORDER BY applications.id DESC
    """

    cursor.execute(query, (session["company_id"],))

    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "company_applications.html",
        applications=applications
    )
# --------------------------------
# Admin Login
# --------------------------------
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM admins WHERE username = %s",
            (username,)
        )

        admin = cursor.fetchone()

        if admin:

            stored_password = admin["password"]

            # Check hashed password
            password_correct = check_password_hash(
                stored_password,
                password
            )

            # Upgrade old plain-text password automatically
            if not password_correct and stored_password == password:

                new_password = generate_password_hash(password)

                cursor.execute(
                    """
                    UPDATE admins
                    SET password = %s
                    WHERE id = %s
                    """,
                    (new_password, admin["id"])
                )

                connection.commit()

                password_correct = True

            if password_correct:

                session["admin_id"] = admin["id"]
                session["admin_username"] = admin["username"]

                cursor.close()
                connection.close()

                return redirect("/admin")

        cursor.close()
        connection.close()

        return """
        <h1>Invalid Username or Password</h1>
        <a href="/admin-login">Try Again</a>
        """

    return render_template("admin_login.html")
# --------------------------------
# Admin Logout
# --------------------------------
@app.route("/admin-logout")
def admin_logout():

    session.pop("admin_id", None)
    session.pop("admin_username", None)

    return redirect("/admin-login")



# --------------------------------
# Company - Edit Job
# --------------------------------
@app.route("/company/job/<int:job_id>/edit", methods=["GET", "POST"])
def edit_company_job(job_id):

    if "company_id" not in session:
        return redirect("/company-login")

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        job_title = request.form["job_title"]
        job_description = request.form["job_description"]
        required_skills = request.form["required_skills"]
        location = request.form["location"]
        salary = request.form["salary"]
        last_date = request.form["last_date"]
        min_cgpa = request.form["min_cgpa"]
        department = request.form["department"]

        query = """
        UPDATE jobs
        SET job_title = %s,
            job_description = %s,
            required_skills = %s,
            location = %s,
            salary = %s,
            last_date = %s,
            min_cgpa = %s,
            department = %s
        WHERE id = %s AND company_id = %s
        """

        values = (
            job_title,
            job_description,
            required_skills,
            location,
            salary,
            last_date,
            min_cgpa,
            department,
            job_id,
            session["company_id"]
        )

        cursor.execute(query, values)
        connection.commit()

        cursor.close()
        connection.close()

        return redirect("/company/jobs")

    cursor.execute(
        """
        SELECT *
        FROM jobs
        WHERE id = %s AND company_id = %s
        """,
        (job_id, session["company_id"])
    )

    job = cursor.fetchone()

    cursor.close()
    connection.close()

    if not job:
        return "Job not found."

    return render_template(
        "edit_job.html",
        job=job
    )
# --------------------------------
# Company - Delete Job
# --------------------------------
# --------------------------------
# Company - Delete Job
# --------------------------------
@app.route("/company/job/<int:job_id>/delete", methods=["POST"])
def delete_company_job(job_id):

    if "company_id" not in session:
        return redirect("/company-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # First delete applications for this job
        cursor.execute(
            """
            DELETE FROM applications
            WHERE job_id = %s
            AND job_id IN (
                SELECT id
                FROM jobs
                WHERE id = %s
                AND company_id = %s
            )
            """,
            (job_id, job_id, session["company_id"])
        )

        # Then delete the job
        cursor.execute(
            """
            DELETE FROM jobs
            WHERE id = %s
            AND company_id = %s
            """,
            (job_id, session["company_id"])
        )

        connection.commit()

    except Exception as e:
        connection.rollback()
        return "Delete failed: " + str(e)

    finally:
        cursor.close()
        connection.close()

    return redirect("/company/jobs")
    if "company_id" not in session:
        return redirect("/company-login")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM jobs
        WHERE id = %s AND company_id = %s
        """,
        (job_id, session["company_id"])
    )

    connection.commit()

    cursor.close()
    connection.close()
# --------------------------------
# Company - Update Applicant Status
# --------------------------------
@app.route(
    "/company/application/<int:application_id>/status",
    methods=["POST"]
)
def company_update_application_status(application_id):

    if "company_id" not in session:
        return redirect("/company-login")

    status = request.form["status"]

    connection = get_db_connection()
    cursor = connection.cursor()

    query = """
    UPDATE applications
    SET status = %s
    WHERE id = %s
    AND job_id IN (
        SELECT id
        FROM jobs
        WHERE company_id = %s
    )
    """

    cursor.execute(
        query,
        (status, application_id, session["company_id"])
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect("/company/applications")
    return redirect("/company/jobs")

# Start Flask Application
# --------------------------------
if __name__ == "__main__":
    app.run(debug=True)