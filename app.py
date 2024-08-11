from flask import *
# from flask_httpauth import *
from flask_sqlalchemy import *
import random
import uuid

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///gift_code.db"
app.config["SQLALCHEMY_BINDS"] = {
    "sake": "sqlite:///kochi_osake.db",
    "otsumami": "sqlite:///kochi_otsumami.db"
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# auth = HTTPBasicAuth()

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

class Gift_code(db.Model):
    __tablename__ = "gift_code"
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(255)) # gift code
    amount = db.Column(db.Integer) # amount of purchased gift
    # sakes = db.relationship('sake', secondary=gift_sake, backref=db.backref('gifts', lazy='dynamic'))
    # otsumamies = db.relationship('otsuami', secondary=gift_otsumami, backref=db.backref('gifts', lazy='dynamic'))


@app.route('/', methods=["GET", "POST"])
def home():
    return render_template('home.html')

@app.route('/simulator', methods=["GET", "POST"])
def simulator():
    return render_template('simulator.html')


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

# （ギフトをもらった時）酒の本数の決定画面
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
        return redirect(url_for("result_gacha"))
    return render_template("choose_sakenum.html", amount=amount)

# ガチャのホーム画面
@app.route("/gacha_home")
def gacha_home():
    budget = session.get("amount")
    sakenum = session.get("sakenum")
    # print(f"Budget on gacha_home: {budget}, Sakenum: {sakenum}")
    return render_template("gacha_home.html", budget=budget, sakenum=sakenum)

# ガチャの実行とその結果の表示（本番用）
@app.route("/result_gacha", methods=["GET", "POST"])
def result_gacha():
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
        return render_template("result_gacha.html", sakes=selected_sakes, otsumamies=selected_otsumamies, money=money)


# ガチャの実行とその結果の表示(シミュレーション用)
@app.route("/result", methods=["GET", "POST"])
def result():
    budget = int(request.args.get("budget", 0))
    oribudget = budget
    sakenum = int(request.args.get("sakenum", 0))
    jpsake = ("jpsake", request.args.get("jpsake"))
    syochu = ("syochu", request.args.get("syochu"))
    fruit = ("fruit", request.args.get("fruit"))
    ume_liq = ("ume_liq", request.args.get("ume_liq"))
    liq = ("liq", request.args.get("liq"))
    waine = ("waine", request.args.get("waine"))
    other = ("other", request.args.get("other"))
    saketuple = [jpsake, syochu, fruit, ume_liq, liq, waine, other]
    saketuple = [item for item in saketuple if item[1] is not None]
    chosen_sakes = []
    for i in saketuple:
        chosen_sakes.append(i[0])
    # print("jpsake is ", jpsake)
    print("chosen_sakes : ",chosen_sakes) # ok
    dbsake = Kochi_osake.query.all()
    sakes = [(sake.name, sake.price) for sake in dbsake if sake.kinds in chosen_sakes]
    print("sakes : ", sakes)
    dbotsumami = Kochi_otsumami.query.all()
    otsumamies = [(otsumami.name, otsumami.price) for otsumami in dbotsumami]


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

        # # 残りの予算でおつまみを最大化する(重複あり)
        # dp = [0] * (budget + 1)
        # count = [[] for _ in range(budget + 1)]
        
        # for otsumami in otsumamies:
        #     otsumami_name, otsumami_price = otsumami
        #     for x in range(otsumami_price, budget + 1):
        #         if dp[x - otsumami_price] + otsumami_price > dp[x]:
        #             dp[x] = dp[x - otsumami_price] + otsumami_price
        #             count[x] = count[x - otsumami_price] + [(otsumami_name, otsumami_price)]

        # ランダムに選んで，できる限り取り切る
        selected_otsumamies = []
        min_price = 100000000000
        for otsumami in otsumamies: # おみやげ内の最小の金額を調べる
            price = otsumami[1]
            if price < min_price:
                min_price = price
        print("min_price : ",min_price)
        while True:
            print("budget : ",budget)
            otsumami = random.choice(otsumamies)
            amount = otsumami[1]
            if budget >= amount:
                budget -= amount
                selected_otsumamies.append(otsumami)
                if budget < min_price:
                    break
        print("selected_otsumamies : ", selected_otsumamies)

        # 結果を表示するためのコード
        # selected_otsumamies = count[budget]
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
        return render_template("result_gacha.html", sakes=selected_sakes, otsumamies=selected_otsumamies, money=money)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)