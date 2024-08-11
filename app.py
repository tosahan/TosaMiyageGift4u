from flask import *
from flask_migrate import *
from flask_security import *
from flask_sqlalchemy import *
import random
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SECRET_KEY"] = "supersecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gift_code.db"
app.config["SQLALCHEMY_BINDS"] = {
    "sake": "sqlite:///kochi_osake.db",
    "otsumami": "sqlite:///kochi_otsumami.db"
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECURITY_RESISTERABLE"] = True
app.config["SECURITY_SEND_PASSWORD_RESET_EMAIL"] = False
app.config["SECURITY_PASSWORD_SALT"] = "my_precious_salt"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
security = Security()

# # definition of Model
# class Role(db.Model, RoleMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(80), unique=True)
#     description = db.Column(db.String(255))

# class User(db.Model, RoleMixin):
#     id = db.Column(db.Integer, primary_key=True)
#     email = db.Column(db.String(255), unique=True)
#     password = db.Column(db.String(255))
#     active = db.Column(db.Boolean())
#     roles = db.relationship("Role", secondary="user_roles")

# class UserRoles(db.Model):
#     user_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
#     role_id = db.Column(db.Integer, db.ForeignKey("role.id"), primary_key=True)

# user_datastore = SQLAlchemyUserDatastore(db, User, Role)
# security.init_app(app, user_datastore)

# definition of Data Base
class Kochi_osake(db.Model):
    __bind_key__ = "sake"
    __tablename__ = "kochi_osake"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255)) # product's name
    kinds = db.Column(db.String(255), nullable=True) # kinds of sake
    price = db.Column(db.Integer) # price of product
    url = db.Column(db.String(255))

class Kochi_otsumami(db.Model):
    __bind_key__ = "otsumami"
    __tablename__ = "kochi_otsumami"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255)) # product's name
    price = db.Column(db.Integer) # price of product
    url = db.Column(db.String(255))

# ギフトコードと酒の多対多の関係を記述するための補助テーブル
# gift_sake = db.Table('gift_sake', db.Column('gift_id', db.Integer, db.ForeignLey('gift_code.id'), primary_key=True), db.Column('sake_id', db.Integer. db.ForeignKey('sake.id'), primary_key=True))

# ギフトコードとおつまみの多対多の関係を記述するための補助テーブル
# gift_otsumami = db.Table('gift_otsumami', db.Column('gift_id', db.Integer, db.ForeignLey('gift_code.id'), primary_key=True), db.Column('otsumami_id', db.Integer. db.ForeignKey('otsumami.id'), primary_key=True))

class Gift_code(db.Model):
    __tablename__ = "gift_code"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255)) # gift code
    amount = db.Column(db.Integer) # amount of purchased gift
    # sakes = db.relationship('sake', secondary=gift_sake, backref=db.backref('gifts', lazy='dynamic'))
    # otsumamies = db.relationship('otsuami', secondary=gift_otsumami, backref=db.backref('gifts', lazy='dynamic'))

# @auth.get_password
# def get_pw(username):
#     if username in users:
#         return users.get(username)
#     return None

# ホームページ
@app.route("/")
def index():
    # data = Kochi_osake.query.all()
    return render_template("index.html")

# お酒追加画面
# 管理者限定(予定)
@app.route("/add_sake", methods=["GET", "POST"])
def add_sake():
    if request.method == "POST":
        name = request.form["name"]
        kinds = request.form.get("kinds", "")
        price = request.form["price"]
        url = request.form["url"]
        new_product = Kochi_osake(name=name, kinds=kinds, price=price, url=url)
        db.session.add(new_product)
        db.session.commit()
        data = Kochi_osake.query.all()
        return render_template("add_sake.html", data=data)
    data = Kochi_osake.query.all()
    return render_template("add_sake.html", data=data)

# 酒管理画面での削除メソッド
@app.route("/del_sake/<int:id>")
def del_sake(id):
    del_data = Kochi_osake.query.filter_by(id=id).first()
    if del_data:
        db.session.delete(del_data)
        db.session.commit()
    return redirect(url_for("index"))

# おつまみ追加画面
@app.route("/add_otsumami", methods=["GET", "POST"])
def add_otsumami():
    if request.method == "POST":
        name = request.form["name"]
        price = request.form["price"]
        url = request.form["url"]
        new_product = Kochi_otsumami(name=name, price=price, url=url)
        db.session.add(new_product)
        db.session.commit()
        data = Kochi_otsumami.query.all()
        return render_template("add_otsumami.html", data=data)
    data = Kochi_otsumami.query.all()
    return render_template("add_otsumami.html", data=data)

# おつまみ管理画面での削除メソッド
@app.route("/del_otsumami/<int:id>")
def del_otsumami(id):
    del_data = Kochi_otsumami.query.filter_by(id=id).first()
    if del_data:
        db.session.delete(del_data)
        db.session.commit()
    return redirect(url_for("index"))

# ギフトカードの購入画面
@app.route("/gift_make", methods=["GET", "POST"])
def make_gift():
    if request.method == "POST":
        gift_amount = request.form.get("gift_amount")
        session["amount"] = gift_amount
        return redirect(url_for("result_purchase"))
    return render_template("make_gift.html")

# ギフトカード購入後の画面
@app.route("/result_purchase")
def result_purchase():
    gift_amount = session.get("amount")
    random_uuid = str(uuid.uuid4())
    new_gift = Gift_code(code=random_uuid, amount=gift_amount)
    db.session.add(new_gift)
    db.session.commit()
    data = Gift_code.query.all()
    return render_template("result_purchase.html", gift_amount=gift_amount, data=data, giftcode=random_uuid)

# ギフトカードの使用画面
@app.route("/use_gift", methods=["GET", "POST"])
def use_gift():
    if request.method == "POST":
        giftcode = request.form.get("giftcode")
        gift = Gift_code.query.filter_by(code=giftcode).first()
        if gift is None:
            # print("no gift")
            flash("入力されたギフトコードは見つかりません")
            return render_template("use_gift.html")
        session["amount"] = gift.amount
        # amount = gift.amount
        return redirect(url_for("choose_sakenum"))
    return render_template("use_gift.html")

# 酒の本数の決定画面
@app.route("/choose_sakenum", methods=["GET", "POST"])
def choose_sakenum():
    amount = session.get("amount")
    if request.method == "POST":
        sakenum = request.form.get("sakenum")
        jpsake = ("jpsake", request.form.get("jpsake"))
        syochu = ("syochu", request.form.get("syochu"))
        fruit = ("fruit", request.form.get("fruit"))
        ume_liq = ("ume_liq", request.form.get("ume_liq"))
        liq = ("liq", request.form.get("liq"))
        waine = ("waine", request.form.get("waine"))
        other = ("other", request.form.get("other"))
        saketuple = [jpsake, syochu, fruit, ume_liq, liq, waine, other]
        print("saketuple : ",saketuple)
        if not sakenum.isdigit() or int(sakenum) < 0:
            flash("酒の本数は0以上の整数で入力してください")
            return render_template("choose_sakenum.html", amount=amount)
        saketuple = [item for item in saketuple if item[1] is not None]
        print("saketuple : ",saketuple)
        sakelist = []
        for i in saketuple:
            sakelist.append(i[0])
        print("sakelist : ",sakelist)
        session["sakelist"] = sakelist
        session["sakenum"] = sakenum
        return redirect(url_for("gacha_home"))
    return render_template("choose_sakenum.html", amount=amount)

# ガチャのホーム画面
@app.route("/gacha_home")
def gacha_home():
    budget = session.get("amount")
    sakenum = session.get("sakenum")
    # print(f"Budget on gacha_home: {budget}, Sakenum: {sakenum}")
    return render_template("gacha_home.html", budget=budget, sakenum=sakenum)

# ガチャの実行とその結果の表示
@app.route("/gacha_result", methods=["GET", "POST"])
def gacha():
    budget = int(session.get("amount"))
    oribudget = budget
    sakenum = int(session.get("sakenum"))
    # print(f"Budget: {budget}, Sakenum: {sakenum}") # ok

    chosen_sakes = session.get("sakelist")
    print("chosen_sakes : ",chosen_sakes) # ok
    dbsake = Kochi_osake.query.all()
    sakes = [(sake.name, sake.price) for sake in dbsake if sake.kinds in chosen_sakes]
    print("sakes : ", sakes)
    dbotsumami = Kochi_otsumami.query.all()
    otsumamies = [(otsumami.name, otsumami.price) for otsumami in dbotsumami]
    # print("sakes: ", sakes)
    # print("otsumamies: ", otsumamies)
    # ok

    # 予算内で決められた本数の酒を選ぶ
    selected_sakes = []
    total_price = 0
    available_sakes = [sake for sake in sakes if sake[1] <= budget] # 予算内で買えるお酒
    while available_sakes and len(selected_sakes) < sakenum:
        sake = random.choice(available_sakes)
        sake_name, sake_price = sake
        if total_price + sake_price <= budget:
            selected_sakes.append(sake)
            total_price += sake_price
            available_sakes.remove(sake)
        else:
            available_sakes.remove(sake) # 予算を超える場合は選択肢から外す
    # if len(selected_sakes) < sakenum:
    #     flash("この予算ではお酒が購入できません", "error")
    #     return redirect(url_for("gacha_home"))

    if len(selected_sakes) < sakenum:
        if selected_sakes:
            print(f"予算内でお酒を{len(selected_sakes)}本しか選べませんでした。選択できたお酒:", selected_sakes)
            str_selected_sakes = [f"{sake[0]}" for sake in selected_sakes]
            print("str_selected_sakes : ", str_selected_sakes)
            onestr_selected_sakes = ', '.join(str_selected_sakes)
            print("onestr_selected_sakes : ", onestr_selected_sakes)
            flash(f"予算内でお酒を{len(selected_sakes)}本しか選べませんでした。<br>選択できたお酒: {onestr_selected_sakes}")
        else:
            print("この予算では選択できるお酒がありません")
            flash("この予算では選択できるお酒がありません", "error")
        return redirect(url_for("choose_sakenum"))
    else:
        spend4sake = total_price
        budget -= total_price
        print("お酒の合計購入金額 = ", spend4sake) # ok
        print("remained budget = ", budget) # ok

        # 残りの予算でおつまみを最大化する(重複あり)
        dp = [0] * (budget + 1)
        count = [[] for _ in range(budget + 1)]
        
        for otsumami in otsumamies:
            otsumami_name, otsumami_price = otsumami
            for x in range(otsumami_price, budget + 1):
                if dp[x - otsumami_price] + otsumami_price > dp[x]:
                    dp[x] = dp[x - otsumami_price] + otsumami_price
                    count[x] = count[x - otsumami_price] + [(otsumami_name, otsumami_price)]

        # 結果を表示するためのコード
        selected_otsumamies = count[budget]
        print("選んだお酒:", selected_sakes)
        print("選んだおつまみ:", selected_otsumamies)
        spend4otsumami = sum(otsumami[1] for otsumami in selected_otsumamies)
        print("おつまみの合計購入金額 = ", spend4otsumami)
        total_spend = spend4sake+spend4otsumami
        print("総購入金額 = ", total_spend)
        remain_budget = oribudget - total_spend
        print("残りの予算 = ", remain_budget)
        money = [spend4sake, spend4otsumami, total_spend, remain_budget]
        # print(budget)

        # ページに返す
        return render_template("gacha_result.html", sakes=selected_sakes, otsumamies=selected_otsumamies, money=money)

# 予算と酒の本数の入力画面(シミュレーション用)
@app.route("/simulation_setting", methods=["GET", "POST"])
def simulation_setting():
    if request.method == "POST":
        budget = request.form.get("budget")
        sakenum = request.form.get("sakenum")
        redirect_url = url_for("simulation_gachahome", budget=budget, sakenum=sakenum)
        # print(f"Redirecting to: {redirect_url}")
        return redirect(redirect_url)
    return render_template("simulation_setting.html")

# ガチャのホーム画面
@app.route("/simulation_gachahome", methods=["GET", "POST"])
def simulation_gachahome():
    budget = request.args.get("budget")
    sakenum = request.args.get("sakenum")
    # print(f"Budget on gacha_home: {budget}, Sakenum: {sakenum}")
    return render_template("simulation_gachahome.html", budget=budget, sakenum=sakenum)

# ガチャの実行とその結果の表示(シミュレーション用)
@app.route("/simulation_gacha", methods=["GET", "POST"])
def simulation_gacha():
    budget = int(request.args.get("budget", 0))
    oribudget = budget
    sakenum = int(request.args.get("sakenum", 0))
    # print(f"Budget: {budget}, Sakenum: {sakenum}") # ok

    dbsake = Kochi_osake.query.all()
    sakes = [(sake.name, sake.price) for sake in dbsake]
    dbotsumami = Kochi_otsumami.query.all()
    otsumamies = [(otsumami.name, otsumami.price) for otsumami in dbotsumami]
    # print("sakes: ", sakes)
    # print("otsumamies: ", otsumamies)
    # ok

    # 予算内で決められた本数の酒を選ぶ
    selected_sakes = []
    total_price = 0
    available_sakes = [sake for sake in sakes if sake[1] <= budget] # 予算内で買えるお酒
    while available_sakes and len(selected_sakes) < sakenum:
        sake = random.choice(available_sakes)
        sake_name, sake_price = sake
        if total_price + sake_price <= budget:
            selected_sakes.append(sake)
            total_price += sake_price
            available_sakes.remove(sake)
        else:
            available_sakes.remove(sake) # 予算を超える場合は選択肢から外す
    # if len(selected_sakes) < sakenum:
    #     flash("この予算ではお酒が購入できません", "error")
    #     return redirect(url_for("gacha_home"))

    if len(selected_sakes) < sakenum:
        if selected_sakes:
            print(f"予算内でお酒を{len(selected_sakes)}本しか選べませんでした。選択できたお酒:", selected_sakes)
            str_selected_sakes = [f"{sake[0]}" for sake in selected_sakes]
            print("str_selected_sakes : ", str_selected_sakes)
            onestr_selected_sakes = ', '.join(str_selected_sakes)
            print("onestr_selected_sakes : ", onestr_selected_sakes)
            flash(f"予算内でお酒を{len(selected_sakes)}本しか選べませんでした。<br>選択できたお酒: {onestr_selected_sakes}")
        else:
            print("この予算では選択できるお酒がありません")
            flash("この予算では選択できるお酒がありません", "error")
        return redirect(url_for("simulation_setting"))
    else:
        spend4sake = total_price
        budget -= total_price
        print("お酒の合計購入金額 = ", spend4sake) # ok
        print("remained budget = ", budget) # ok

        # 残りの予算でおつまみを最大化する(重複あり)
        dp = [0] * (budget + 1)
        count = [[] for _ in range(budget + 1)]
        
        for otsumami in otsumamies:
            otsumami_name, otsumami_price = otsumami
            for x in range(otsumami_price, budget + 1):
                if dp[x - otsumami_price] + otsumami_price > dp[x]:
                    dp[x] = dp[x - otsumami_price] + otsumami_price
                    count[x] = count[x - otsumami_price] + [(otsumami_name, otsumami_price)]

        # 結果を表示するためのコード
        selected_otsumamies = count[budget]
        print("選んだお酒:", selected_sakes)
        print("選んだおつまみ:", selected_otsumamies)
        spend4otsumami = sum(otsumami[1] for otsumami in selected_otsumamies)
        print("おつまみの合計購入金額 = ", spend4otsumami)
        total_spend = spend4sake+spend4otsumami
        print("総購入金額 = ", total_spend)
        remain_budget = oribudget - total_spend
        print("残りの予算 = ", remain_budget)
        money = [spend4sake, spend4otsumami, total_spend, remain_budget]
        # print(budget)

        # ページに返す
        return render_template("simulation_gacha.html", sakes=selected_sakes, otsumamies=selected_otsumamies, money=money)


# ランダムな商品の表示
# for debug
# @app.route("/random")
# def get_random():
#     random_sake = Kochi_osake.query.order_by(db.func.random()).first()
#     return render_template("random.html", sake=random_sake)

# @auth.login_required
# def hello():
#     return "Hello,world!"

# @app.route("/index")
# def index():
#     return "Hello, %s!" % auth.username()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
