from flask import Flask, render_template_string, request, jsonify, session
import sqlite3, os
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.environ.get("SHOP_SECRET_KEY", "change-this-before-deploy")
DB = Path(__file__).with_name("ibrohim_parking.db")

def connect():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

with connect() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS players(
      username TEXT PRIMARY KEY, cash INTEGER NOT NULL DEFAULT 5000000,
      bank INTEGER NOT NULL DEFAULT 0, rating INTEGER NOT NULL DEFAULT 0);
    CREATE TABLE IF NOT EXISTS loans(
      id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, total INTEGER,
      remaining INTEGER, monthly INTEGER, months INTEGER);
    CREATE TABLE IF NOT EXISTS listings(
      id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT,
      category TEXT, buy_price INTEGER, sale_price INTEGER);
    CREATE TABLE IF NOT EXISTS rentals(
      id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, title TEXT,
      category TEXT, monthly_price INTEGER, months INTEGER);
    """)

def profile(name):
    with connect() as c:
        p = c.execute("SELECT * FROM players WHERE username=?", (name,)).fetchone()
        return {
          "username": p["username"], "cash": p["cash"], "bank": p["bank"], "rating": p["rating"],
          "loans": [dict(x) for x in c.execute("SELECT * FROM loans WHERE username=?", (name,))],
          "listings": [dict(x) for x in c.execute("SELECT * FROM listings WHERE username=?", (name,))],
          "rentals": [dict(x) for x in c.execute("SELECT * FROM rentals WHERE username=?", (name,))]
        }

PAGE = r"""
<!doctype html><html lang="uz"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IBROHIM PARKING</title><style>
*{box-sizing:border-box}body{margin:0;background:#0d121a;color:#f4f5f7;font-family:Arial}header{padding:16px;background:#172231;border-bottom:2px solid #c99a42;display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}.gold{color:#f3c35e;font-weight:bold}.wrap{max-width:1000px;margin:auto;padding:14px}.card{background:#172231;border:1px solid #3a4b60;border-radius:14px;padding:15px;margin:10px 0}h2{font-size:19px;color:#f3c35e;margin:0 0 12px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px}.stat{font-size:22px;font-weight:bold;color:#f3c35e}nav{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}button{border:0;border-radius:9px;padding:11px 13px;background:#c99a42;color:#161616;font-weight:bold;margin:3px;cursor:pointer}button.alt{background:#35465c;color:white}input,select{display:block;width:100%;padding:11px;border-radius:8px;background:#0d1724;color:white;border:1px solid #52647b;margin:6px 0 12px}.tab{display:none}.tab.on{display:block}.muted{color:#aeb9c8;font-size:13px}.phone{max-width:340px;margin:auto;background:#0e1a2a;border:7px solid #444;border-radius:28px;padding:18px;min-height:350px}.apps{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.app{background:#2a3c52;border-radius:12px;padding:15px 5px;text-align:center}.app b{display:block;font-size:25px}.row{display:flex;justify-content:space-between;border-bottom:1px solid #405066;padding:8px 0;gap:8px}
</style></head><body><header><div><div class="gold">IBROHIM PARKING</div><small>O‘zbekiston hayot simulyatori — funksional MVP</small></div><div id="headBalance">Mehmon</div></header><main class="wrap">
<div class="card" id="login"><h2>O‘yinga kirish</h2><p class="muted">Yangi o‘yinchi 5 000 000 so‘m va 0 reyting bilan boshlaydi.</p><input id="name" placeholder="O‘yinchi nomi" maxlength="24"><button onclick="login()">Kirish / ro‘yxatdan o‘tish</button></div>
<div id="app" style="display:none">
<div class="grid"><div class="card">Hamyon<div class="stat" id="cash">5 000 000</div><small>so‘m</small></div><div class="card">Bank<div class="stat" id="bank">0</div><small>so‘m</small></div><div class="card">Reyting<div class="stat" id="rating">0 / 100</div></div></div>
<nav><button onclick="tab('phone')">Telefon</button><button onclick="tab('banktab')">Bank</button><button onclick="tab('credit')">Kredit</button><button onclick="tab('market')">Savdo</button><button onclick="tab('rent')">Ijara</button><button onclick="tab('profile')">Profil</button></nav>
<section id="phone" class="tab on card"><h2>O‘yin ichidagi smartfon</h2><div class="phone"><b>IBROHIM PHONE</b><p class="muted">09:41 · Batareya 100%</p><div class="apps"><div class="app" onclick="alert('Ichki qo‘ng‘iroq funksiyasi keyingi bosqichda ulanadi')"><b>📞</b>Telefon</div><div class="app" onclick="alert('O‘yin ichidagi chat keyingi bosqichda ulanadi')"><b>💬</b>Xabarlar</div><div class="app" onclick="alert('O‘zbekiston xaritasi keyingi bosqichda ulanadi')"><b>🗺️</b>Xarita</div><div class="app" onclick="tab('banktab')"><b>🏦</b>Bank</div><div class="app" onclick="tab('market')"><b>🛍️</b>Market</div><div class="app" onclick="alert('Kamera funksiyasi keyingi bosqichda ulanadi')"><b>📷</b>Kamera</div></div><p class="muted">Ilovalar o‘yin ichidagi simulyatsiyadir.</p></div></section>
<section id="banktab" class="tab card"><h2>Virtual bank va karta</h2><p class="muted">Faqat o‘yin ichidagi pul. Haqiqiy bank tizimiga ulanmagan.</p><button onclick="bankop('in')">Hamyondan bankka 100 000</button><button class="alt" onclick="bankop('out')">Bankdan hamyonga 100 000</button><p id="bankmsg"></p></section>
<section id="credit" class="tab card"><h2>Virtual kredit</h2><label>Kredit miqdori (100 ming – 10 mln so‘m)</label><input id="amount" type="number" min="100000" max="10000000" value="500000"><label>Muddati</label><select id="months"><option value="3">3 oy</option><option value="6">6 oy</option><option value="12">12 oy</option></select><button onclick="loan()">Kredit olish (sinov)</button><div id="loanmsg"></div><h3>Kreditlarim</h3><div id="loans"></div></section>
<section id="market" class="tab card"><h2>O‘yinchilar bozori</h2><p class="muted">Sotuv narxi xarid narxidan qat’iy arzon bo‘lishi kerak.</p><label>Buyum nomi</label><input id="item" placeholder="Masalan, Redmi telefon"><label>Toifa</label><select id="category"><option>Telefon</option><option>Avtomobil</option><option>Jihoz</option><option>Boshqa</option></select><label>Sotib olgan narx</label><input id="buyprice" type="number" value="1000000"><label>Sotuv narxi</label><input id="saleprice" type="number" value="900000"><button onclick="listing()">Sotuvga qo‘yish</button><div id="marketmsg"></div><h3>E’lonlarim</h3><div id="listings"></div></section>
<section id="rent" class="tab card"><h2>Uy, mashina yoki biznesni ijaraga berish</h2><label>Mulk nomi</label><input id="renttitle" placeholder="Masalan, Qo‘qonda 2 xonali uy"><label>Toifa</label><select id="rentcat"><option>Uy</option><option>Avtomobil</option><option>Do‘kon</option><option>Kafe</option></select><label>Oylik ijara narxi (so‘m)</label><input id="rentprice" type="number" value="1500000"><label>Muddat (oy)</label><input id="rentmonths" type="number" min="1" max="24" value="1"><button onclick="rental()">Ijara e’loni yaratish</button><div id="rentmsg"></div><h3>E’lonlarim</h3><div id="rentals"></div></section>
<section id="profile" class="tab card"><h2>Profil</h2><div id="profiledata"></div><p class="muted">Bu hozircha bank, kredit, savdo va ijara funksiyalari ishlaydigan boshlang‘ich web prototip. To‘liq 3D ochiq dunyo, Qo‘qon xaritasi va multiplayer keyingi bosqichlarda quriladi.</p></section>
</div></main><script>
let me=null;const f=n=>Number(n).toLocaleString('uz-UZ');async function post(url,data){let r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});let j=await r.json();if(!r.ok)throw Error(j.error||'Xatolik');return j}
function tab(id){document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));document.getElementById(id).classList.add('on')}
async function login(){try{me=await post('/login',{name:document.getElementById('name').value});document.getElementById('login').style.display='none';document.getElementById('app').style.display='block';draw()}catch(e){alert(e.message)}}
async function reload(){me=await (await fetch('/profile')).json();draw()}
function draw(){cash.textContent=f(me.cash);bank.textContent=f(me.bank);rating.textContent=me.rating+' / 100';headBalance.textContent=me.username+' · '+f(me.cash)+' so‘m';loans.innerHTML=me.loans.map(x=>`<div class="row">Qoldiq: ${f(x.remaining)} so‘m <button onclick="pay(${x.id})">To‘lash</button></div>`).join('')||'Kredit yo‘q';listings.innerHTML=me.listings.map(x=>`<div class="row">${x.title} · ${f(x.sale_price)} so‘m</div>`).join('')||'E’lon yo‘q';rentals.innerHTML=me.rentals.map(x=>`<div class="row">${x.title} · ${f(x.monthly_price)} so‘m/oy</div>`).join('')||'E’lon yo‘q';profiledata.innerHTML=`<div class="row">O‘yinchi <b>${me.username}</b></div><div class="row">Reyting <b>${me.rating}/100</b></div><div class="row">Hamyon <b>${f(me.cash)} so‘m</b></div>`}
async function bankop(action){try{me=await post('/bank',{action});draw();bankmsg.textContent='Bank amaliyoti bajarildi.'}catch(e){bankmsg.textContent=e.message}}
async function loan(){try{me=await post('/loan',{amount:+amount.value,months:+months.value});draw();loanmsg.textContent='Virtual kredit berildi. 10% o‘yin ichidagi ustama qo‘shildi.'}catch(e){loanmsg.textContent=e.message}}
async function pay(id){try{me=await post('/pay',{id});draw()}catch(e){alert(e.message)}}
async function listing(){try{me=await post('/listing',{title:item.value,category:category.value,buy:+buyprice.value,sale:+saleprice.value});draw();marketmsg.textContent='E’lon yaratildi.'}catch(e){marketmsg.textContent=e.message}}
async function rental(){try{me=await post('/rental',{title:renttitle.value,category:rentcat.value,price:+rentprice.value,months:+rentmonths.value});draw();rentmsg.textContent='Ijara e’loni yaratildi.'}catch(e){rentmsg.textContent=e.message}}
</script></body></html>
"""

@app.route("/")
def home():
    return render_template_string(PAGE)

@app.post("/login")
def login():
    name = str(request.json.get("name", "")).strip()[:24]
    if len(name) < 2:
        return jsonify(error="O‘yinchi nomi kamida 2 ta belgidan iborat bo‘lsin."), 400
    with connect() as c:
        c.execute("INSERT OR IGNORE INTO players(username) VALUES(?)", (name,))
    session["username"] = name
    return jsonify(profile(name))

@app.get("/profile")
def get_profile():
    name = session.get("username")
    if not name: return jsonify(error="Avval kiring."), 401
    return jsonify(profile(name))

@app.post("/bank")
def bank_op():
    name = session.get("username")
    if not name: return jsonify(error="Avval kiring."), 401
    action = request.json.get("action")
    with connect() as c:
        p = c.execute("SELECT cash,bank FROM players WHERE username=?", (name,)).fetchone()
        if action == "in":
            if p["cash"] < 100000: return jsonify(error="Hamyonda mablag‘ yetarli emas."), 400
            c.execute("UPDATE players SET cash=cash-100000,bank=bank+100000 WHERE username=?", (name,))
        elif action == "out":
            if p["bank"] < 100000: return jsonify(error="Bank hisobida mablag‘ yetarli emas."), 400
            c.execute("UPDATE players SET cash=cash+100000,bank=bank-100000 WHERE username=?", (name,))
        else: return jsonify(error="Noto‘g‘ri amal."), 400
    return jsonify(profile(name))

@app.post("/loan")
def take_loan():
    name = session.get("username")
    if not name: return jsonify(error="Avval kiring."), 401
    amount, months = int(request.json.get("amount", 0)), int(request.json.get("months", 0))
    if amount < 100000 or amount > 10000000 or months not in (3, 6, 12):
        return jsonify(error="Kredit miqdori yoki muddati noto‘g‘ri."), 400
    total = amount + amount // 10
    monthly = (total + months - 1) // months
    with connect() as c:
        c.execute("UPDATE players SET cash=cash+? WHERE username=?", (amount, name))
        c.execute("INSERT INTO loans(username,total,remaining,monthly,months) VALUES(?,?,?,?,?)", (name,total,total,monthly,months))
    return jsonify(profile(name))

@app.post("/pay")
def pay():
    name = session.get("username")
    if not name: return jsonify(error="Avval kiring."), 401
    loan_id = int(request.json.get("id", 0))
    with connect() as c:
        l = c.execute("SELECT * FROM loans WHERE id=? AND username=?", (loan_id,name)).fetchone()
        p = c.execute("SELECT cash FROM players WHERE username=?", (name,)).fetchone()
        if not l: return jsonify(error="Kredit topilmadi."), 404
        amount = min(l["monthly"], l["remaining"])
        if p["cash"] < amount: return jsonify(error="Hamyonda to‘lov uchun pul yetarli emas."), 400
        c.execute("UPDATE players SET cash=cash-? WHERE username=?", (amount,name))
        c.execute("UPDATE loans SET remaining=remaining-? WHERE id=?", (amount,loan_id))
    return jsonify(profile(name))

@app.post("/listing")
def listing():
    name = session.get("username")
    if not name: return jsonify(error="Avval kiring."), 401
    d = request.json
    title = str(d.get("title","")).strip()[:70]
    buy, sale = int(d.get("buy",0)), int(d.get("sale",0))
    if not title or buy < 2 or sale < 1 or sale >= buy:
        return jsonify(error="Sotuv narxi xarid narxidan qat’iy arzon bo‘lishi shart."), 400
    with connect() as c:
        c.execute("INSERT INTO listings(username,title,category,buy_price,sale_price) VALUES(?,?,?,?,?)",
                  (name,title,str(d.get("category","Buyum"))[:30],buy,sale))
    return jsonify(profile(name))

@app.post("/rental")
def rental():
    name = session.get("username")
    if not name: return jsonify(error="Avval kiring."), 401
    d=request.json; title=str(d.get("title","")).strip()[:70]
    price, months = int(d.get("price",0)), int(d.get("months",0))
    if not title or price < 1 or months < 1 or months > 24:
        return jsonify(error="Ijara ma’lumotlarini tekshiring."), 400
    with connect() as c:
        c.execute("INSERT INTO rentals(username,title,category,monthly_price,months) VALUES(?,?,?,?,?)",
                  (name,title,str(d.get("category","Mulk"))[:30],price,months))
    return jsonify(profile(name))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
