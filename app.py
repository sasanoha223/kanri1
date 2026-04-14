from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "secret-key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# -----------------
# ユーザー
# -----------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))

# -----------------
# 商品
# -----------------
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    stock = db.Column(db.Integer)
    category = db.Column(db.String(50))
    user_id = db.Column(db.Integer)

# -----------------
# ログイン確認
# -----------------
def is_logged_in():
    return session.get("user_id")

# -----------------
# ユーザー登録（重複チェックあり）
# -----------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        # 重複チェック
        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return render_template(
                "register.html",
                error="その名前はもう使用されています"
            )

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        return redirect('/login')

    return render_template('register.html')

# -----------------
# ログイン
# -----------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            return redirect('/')
        else:
            return "ログイン失敗"

    return render_template('login.html')

# -----------------
# ログアウト
# -----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# -----------------
# トップ（ユーザー別）
# -----------------
@app.route('/')
def index():
    if not is_logged_in():
        return redirect('/login')

    products = Product.query.filter_by(user_id=session["user_id"]).all()

    return render_template(
        'index.html',
        products=products,
        username=session.get("username", "不明ユーザー")
    )

# -----------------
# 商品追加
# -----------------
@app.route('/add', methods=['GET', 'POST'])
def add():
    if not is_logged_in():
        return redirect('/login')

    if request.method == 'POST':
        product = Product(
            name=request.form['name'],
            stock=int(request.form['stock']),
            category=request.form['category'],
            user_id=session["user_id"]
        )

        db.session.add(product)
        db.session.commit()

        return redirect('/')

    return render_template('add.html')

# -----------------
# 在庫更新
# -----------------
@app.route('/update/<int:id>/<change>')
def update(id, change):
    if not is_logged_in():
        return jsonify({"success": False})

    product = Product.query.get(id)

    if product and product.user_id == session["user_id"]:
        product.stock += int(change)

        if product.stock < 0:
            product.stock = 0

        db.session.commit()

        return jsonify({"success": True, "stock": product.stock})

    return jsonify({"success": False})

# -----------------
# 削除
# -----------------
@app.route('/delete/<int:id>')
def delete(id):
    if not is_logged_in():
        return redirect('/login')

    product = Product.query.get(id)

    if product and product.user_id == session["user_id"]:
        db.session.delete(product)
        db.session.commit()

    return redirect('/')

# -----------------
# 起動
# -----------------
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)