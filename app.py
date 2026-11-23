
from flask import Flask, render_template_string, request, jsonify, session
from flask_socketio import SocketIO, join_room, emit
import sqlite3
import os
import time
import uuid

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "ibrohim-parking-secret")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

DB = "parking.db"
MAX_PLAYERS = 50

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    con.execute("""
        CREATE TABLE IF NOT EXISTS players(
            id TEXT PRIMARY KEY,
            name TEXT,
            money INTEGER DEFAULT 5000000,
            bank INTEGER DEFAULT 0,
            rating INTEGER DEFAULT 0
        )
    """)
    con.commit()
    con.close()

init_db()

HTML = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>IBROHIM PARKING</title>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<style>
*{box-sizing:border-box}
body{margin:0;background:#111;color:white;font-family:Arial}
header{padding:14px;background:#171717;border-bottom:2px solid #d6aa36}
h2{color:#e8bd51;margin:0}
#game{width:100%;height:60vh;display:block}
.panel{padding:12px;background:#202020;border-radius:12px;margin:10px}
button,input{padding:12px;border:0;border-radius:8px;margin:4px}
button{background:#d9ad43;color:#111;font-weight:bold}
.controls{display:flex;justify-content:space-around;flex-wrap:wrap}
#info{color:#e8bd51}
</style>
</head>
<body>
<header>
<h2>IBROHIM PARKING</h2>
O‘zbekiston hayot simulyatori · 50 kishilik xona
</header>

<div class="panel">
<input id="name" placeholder="O‘yinchi ismi">
<button onclick="login()">O‘yinga kirish</button>
<div id="info">O‘yinchining ismini kiriting</div>
</div>

<canvas id="game"></canvas>

<div class="panel">
<b>O‘yin boshqaruvi</b>
<div class="controls">
<button onmousedown="move='left'" onmouseup="move=''">◀</button>
<button onmousedown="move='forward'" onmouseup="move=''">GAZ ▲</button>
<button onmousedown="move='back'" onmouseup="move=''">TORMOZ ▼</button>
<button onmousedown="move='right'" onmouseup="move=''">▶</button>
</div>
</div>

<div class="panel">
<b>IBROHIM PHONE</b>
<div class="controls">
<button onclick="alert('Telefon ilovasi')">📞 Telefon</button>
<button onclick="alert('Xabarlar')">💬 Xabarlar</button>
<button onclick="alert('O‘zbekiston xaritasi')">🗺️ Xarita</button>
<button onclick="alert('Virtual bank')">🏦 Bank</button>
<button onclick="alert('O‘yin marketi')">🛍️ Market</button>
<button onclick="alert('Kamera')">📷 Kamera</button>
</div>
</div>

<div class="panel">
<b>Profil va moliya</b>
<p id="money">Hamyon: 5 000 000 so‘m</p>
<p id="bank">Bank: 0 so‘m</p>
<p id="rating">Reyting: 0 / 100</p>
</div>

<div class="panel">
<b>Multiplayer</b>
<input id="room" value="uzbekistan">
<button onclick="joinGame()">Xonaga kirish</button>
<p id="players">Xona: 0 / 50</p>
<div id="online"></div>
</div>

<script>
const socket=io();
let playerId=null,move='',speed=0,angle=0;
let players={};

const canvas=document.getElementById('game');
const scene=new THREE.Scene();
scene.background=new THREE.Color(0x87b5d5);
scene.fog=new THREE.Fog(0x87b5d5,30,200);

const camera=new THREE.PerspectiveCamera(65,1,0.1,1000);
camera.position.set(0,8,14);

const renderer=new THREE.WebGLRenderer({canvas,antialias:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));

scene.add(new THREE.HemisphereLight(0xffffff,0x444444,2));
const sun=new THREE.DirectionalLight(0xffffff,2);
sun.position.set(10,20,10);
scene.add(sun);

const ground=new THREE.Mesh(
 new THREE.PlaneGeometry(500,500),
 new THREE.MeshStandardMaterial({color:0x477a43})
);
ground.rotation.x=-Math.PI/2;
scene.add(ground);

for(let i=-5;i<=5;i++){
 const road=new THREE.Mesh(
  new THREE.BoxGeometry(100,0.08,7),
  new THREE.MeshStandardMaterial({color:0x333333})
 );
 road.position.set(0,0.05,i*18);
 scene.add(road);
}

const car=new THREE.Group();
const body=new THREE.Mesh(
 new THREE.BoxGeometry(2,0.8,4),
 new THREE.MeshStandardMaterial({color:0xc49a36})
);
body.position.y=0.8;
car.add(body);
const cabin=new THREE.Mesh(
 new THREE.BoxGeometry(1.6,0.8,1.8),
 new THREE.MeshStandardMaterial({color:0x222d39})
);
cabin.position.set(0,1.5,-0.2);
car.add(cabin);
scene.add(car);

const avatar=new THREE.Group();
const head=new THREE.Mesh(
 new THREE.SphereGeometry(0.35,16,16),
 new THREE.MeshStandardMaterial({color:0xd9a078})
);
head.position.y=1.7;
avatar.add(head);
const torso=new THREE.Mesh(
 new THREE.BoxGeometry(0.7,1,0.4),
 new THREE.MeshStandardMaterial({color:0x254d99})
);
torso.position.y=0.9;
avatar.add(torso);
scene.add(avatar);
avatar.visible=false;

function resize(){
 const w=canvas.clientWidth,h=canvas.clientHeight;
 renderer.setSize(w,h,false);
 camera.aspect=w/h;
 camera.updateProjectionMatrix();
}
window.addEventListener('resize',resize);
resize();

function login(){
 const name=document.getElementById('name').value.trim();
 if(!name)return alert('Ismingizni kiriting');
 socket.emit('login',{name});
}

socket.on('logged',data=>{
 playerId=data.id;
 document.getElementById('info').innerText='Xush kelibsiz, '+data.name;
 document.getElementById('money').innerText='Hamyon: '+data.money.toLocaleString()+' so‘m';
 document.getElementById('bank').innerText='Bank: '+data.bank.toLocaleString()+' so‘m';
 document.getElementById('rating').innerText='Reyting: '+data.rating+' / 100';
});

function joinGame(){
 if(!playerId)return alert('Avval o‘yinga kiring');
 socket.emit('join_game',{room:document.getElementById('room').value});
}

socket.on('room_update',data=>{
 document.getElementById('players').innerText='Xona: '+data.count+' / 50';
 document.getElementById('online').innerText=data.names.join(', ');
});

socket.on('player_move',data=>{
 if(data.id===playerId)return;
 players[data.id]=data;
});

function animate(){
 requestAnimationFrame(animate);
 if(move==='forward')speed=Math.min(speed+0.012,0.35);
 else if(move==='back')speed=Math.max(speed-0.02,-0.15);
 else speed*=0.97;
 if(move==='left')angle+=0.035;
 if(move==='right')angle-=0.035;
 car.rotation.y=angle;
 car.position.x+=Math.sin(angle)*speed;
 car.position.z+=Math.cos(angle)*speed;
 camera.position.set(car.position.x,car.position.y+7,car.position.z+12);
 camera.lookAt(car.position);
 renderer.render(scene,camera);
 if(playerId && Math.random()<0.1){
  socket.emit('move',{x:car.position.x,z:car.position.z,angle});
 }
}
animate();
</script>
</body>
</html>
"""

@app.route("/")
def home():
    if "id" not in session:
        session["id"] = str(uuid.uuid4())
    return render_template_string(HTML)

@app.post("/api/login")
def api_login():
    return jsonify({"status":"ok"})

@socketio.on("login")
def login_user(data):
    name = str(data.get("name","O‘yinchi"))[:30]
    pid = session.get("id") or str(uuid.uuid4())
    session["id"] = pid
    con = db()
    con.execute(
        "INSERT OR IGNORE INTO players(id,name) VALUES(?,?)",
        (pid,name)
    )
    con.execute("UPDATE players SET name=? WHERE id=?",(name,pid))
    con.commit()
    p=con.execute("SELECT * FROM players WHERE id=?",(pid,)).fetchone()
    con.close()
    emit("logged",{
        "id":pid,"name":p["name"],"money":p["money"],
        "bank":p["bank"],"rating":p["rating"]
    })

@socketio.on("join_game")
def join_game(data):
    room=str(data.get("room","uzbekistan"))[:40]
    current=socketio.server.manager.rooms.get("/",{}).get(room,set())
    if len(current)>=MAX_PLAYERS and request.sid not in current:
        emit("error_message",{"message":"Xona to‘la"})
        return
    join_room(room)
    emit("room_update",{"count":len(current)+1,"names":[]},to=room)

@socketio.on("move")
def move_player(data):
    emit("player_move",{
        "id":session.get("id"),
        "x":float(data.get("x",0)),
        "z":float(data.get("z",0)),
        "angle":float(data.get("angle",0))
    },broadcast=True,include_self=False)

if __name__=="__main__":
    socketio.run(app,host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
