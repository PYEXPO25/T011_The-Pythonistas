from flask import Flask, request, redirect, url_for, session, render_template_string

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Secret key for session management

# Dummy user credentials
USER_CREDENTIALS = {"admin": "password123"}

# Login Page
@app.route("/", methods=["GET", "POST"])
def login():
    login_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); text-align: center; width: 300px; }
            input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px; }
            button { width: 100%; padding: 10px; background-color: #007bff; border: none; color: white; font-size: 16px; cursor: pointer; border-radius: 5px; }
            button:hover { background-color: #0056b3; }
            .error { color: red; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Login</h2>
            {% if error %} <p class="error">{{ error }}</p> {% endif %}
            <form method="POST">
                <label for="username">Username</label>
                <input type="text" name="username" required>
                <label for="password">Password</label>
                <input type="password" name="password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    """

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template_string(login_html, error="Invalid username or password")

    return render_template_string(login_html)

# Dashboard Page
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    dashboard_html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; background-color: #f8f9fa; display: flex; justify-content: center; align-items: center; height: 100vh; }
            .container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1); text-align: center; width: 300px; }
            a { display: inline-block; padding: 10px 20px; margin-top: 20px; background-color: #dc3545; color: white; text-decoration: none; border-radius: 5px; }
            a:hover { background-color: #c82333; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Welcome, {{ username }}!</h2>
            <a href="{{ url_for('logout') }}">Logout</a>
        </div>
    </body>
    </html>
    """
    return render_template_string(dashboard_html, username=session["user"])

# Logout Route
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
