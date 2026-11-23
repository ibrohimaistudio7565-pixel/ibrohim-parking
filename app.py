
from flask import Flask, render_template_string

app = Flask(__name__)

HTML = r"""
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IBROHIM PARKING</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#10151c;color:white;font-family:Arial}
header{padding:15px;text-align:center;background:#171f2b}
h1{color:#f5c542;margin:5px}
#game{width:100%;height:65vh;display:block}
.controls{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:12px}
button{padding:18px 5px;border:0;border-radius:12px;
background:#e5b832;color:#111;font-weight:bold;font-size:17px}
.info{text-align:center;padding:8px}
</style>
</head>
<body>
<header>
<h1>IBROHIM PARKING</h1>
<div>3D PARKING SIMULATOR</div>
</header>

<div class="info">
<span id="mission">Vazifa: Mashinani parkovka joyiga olib boring</span>
</div>

<div id="game"></div>

<div class="controls">
<button id="left">⬅ CHAP</button>
<button id="gas">GAZ ⬆</button>
<button id="right">O‘NG ➡</button>
<button id="brake">TORMOZ</button>
<button id="reverse">ORQAGA</button>
<button id="camera">KAMERA</button>
</div>

<script src="https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js"></script>
<script>
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x91bce0);

const camera = new THREE.PerspectiveCamera(
65, window.innerWidth/(window.innerHeight*0.65), 0.1, 1000
);

const renderer = new THREE.WebGLRenderer({antialias:true});
renderer.setSize(window.innerWidth, window.innerHeight*0.65);
renderer.shadowMap.enabled = true;
document.getElementById("game").appendChild(renderer.domElement);

scene.add(new THREE.HemisphereLight(0xffffff,0x555555,2));

const sun = new THREE.DirectionalLight(0xffffff,2);
sun.position.set(10,20,10);
scene.add(sun);

const ground = new THREE.Mesh(
new THREE.PlaneGeometry(300,300),
new THREE.MeshStandardMaterial({color:0x555b60})
);
ground.rotation.x=-Math.PI/2;
scene.add(ground);

const road = new THREE.Mesh(
new THREE.PlaneGeometry(18,200),
new THREE.MeshStandardMaterial({color:0x292d32})
);
road.rotation.x=-Math.PI/2;
road.position.y=0.02;
scene.add(road);

// Yo'l chiziqlari
for(let z=-90;z<100;z+=12){
const line=new THREE.Mesh(
new THREE.BoxGeometry(0.25,0.04,6),
new THREE.MeshStandardMaterial({color:0xffffff})
);
line.position.set(0,0.06,z);
scene.add(line);
}

// Shahar binolari
for(let i=0;i<35;i++){
const h=8+Math.random()*25;
const b=new THREE.Mesh(
new THREE.BoxGeometry(8,h,8),
new THREE.MeshStandardMaterial({
color:new THREE.Color().setHSL(0.55,0.15,0.25+Math.random()*0.3)
})
);
b.position.set(
(i%2===0? -22:22),
h/2,
Math.floor(i/2)*-13
);
scene.add(b);
}

// Mashina
const car=new THREE.Group();

const body=new THREE.Mesh(
new THREE.BoxGeometry(2.2,0.8,4),
new THREE.MeshStandardMaterial({color:0xd82929,metalness:0.4,roughness:0.3})
);
body.position.y=0.9;
car.add(body);

const top=new THREE.Mesh(
new THREE.BoxGeometry(1.7,0.7,2),
new THREE.MeshStandardMaterial({color:0x222d3b})
);
top.position.set(0,1.55,-0.2);
car.add(top);

for(const x of [-1.15,1.15]){
for(const z of [-1.3,1.3]){
const wheel=new THREE.Mesh(
new THREE.CylinderGeometry(0.42,0.42,0.3,20),
new THREE.MeshStandardMaterial({color:0x111111})
);
wheel.rotation.z=Math.PI/2;
wheel.position.set(x,0.45,z);
car.add(wheel);
}
}
scene.add(car);

// Parkovka joyi
const parking=new THREE.Mesh(
new THREE.PlaneGeometry(5,8),
new THREE.MeshStandardMaterial({color:0x238b45})
);
parking.rotation.x=-Math.PI/2;
parking.position.set(0,0.04,-35);
scene.add(parking);

let speed=0, steer=0, cameraMode=0;
let gas=false, reverse=false, braking=false;
let missionDone=false;

function hold(id,callback){
const el=document.getElementById(id);
el.addEventListener("pointerdown",e=>{
e.preventDefault(); callback(true);
});
["pointerup","pointerleave","pointercancel"].forEach(event=>{
el.addEventListener(event,()=>callback(false));
});
}
hold("gas",v=>gas=v);
hold("reverse",v=>reverse=v);
hold("brake",v=>braking=v);
hold("left",v=>steer=v?-1:0);
hold("right",v=>steer=v?1:0);

document.getElementById("camera").onclick=()=>{
cameraMode=(cameraMode+1)%2;
};

function animate(){
requestAnimationFrame(animate);

if(gas) speed=Math.min(speed+0.012,0.45);
if(reverse) speed=Math.max(speed-0.012,-0.25);
if(braking) speed*=0.90;
if(!gas&&!reverse&&!braking) speed*=0.985;

car.rotation.y-=steer*speed*0.045;
car.position.x+=Math.sin(car.rotation.y)*speed;
car.position.z+=Math.cos(car.rotation.y)*speed;

car.position.x=Math.max(-7,Math.min(7,car.position.x));
car.position.z=Math.max(-100,Math.min(100,car.position.z));

if(cameraMode===0){
camera.position.set(
car.position.x+Math.sin(car.rotation.y)*9,
car.position.y+6,
car.position.z+Math.cos(car.rotation.y)*9
);
camera.lookAt(car.position);
}else{
camera.position.set(car.position.x,18,car.position.z+0.1);
camera.lookAt(car.position);
}

if(!missionDone &&
Math.abs(car.position.x)<2.2 &&
car.position.z < -32 && car.position.z > -39 &&
Math.abs(speed)<0.08){
missionDone=true;
document.getElementById("mission").innerText=
"BARAKALLA! PARKOVKA BAJARILDI!";
}

renderer.render(scene,camera);
}
animate();

window.addEventListener("resize",()=>{
camera.aspect=window.innerWidth/(window.innerHeight*0.65);
camera.updateProjectionMatrix();
renderer.setSize(window.innerWidth,window.innerHeight*0.65);
});
</script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/health")
def health():
    return {"status": "ok", "app": "IBROHIM PARKING"}

if __name__ == "__main__":
    import os
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
  
