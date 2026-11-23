import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

export async function createWorkshop(viewer, onDraw, onContextLost) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  viewer.prepend(renderer.domElement);
  renderer.domElement.setAttribute('aria-label', 'Modelo CAD interactivo');
  renderer.domElement.addEventListener('webglcontextlost', event => {
    event.preventDefault();
    onContextLost();
  });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = .98;

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-300,300,240,-240,1,3500);
  const model = new THREE.Group();
  model.rotation.x = -Math.PI/2;
  model.position.z = 151;
  scene.add(model);
  const room = new RoomEnvironment();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environment = pmrem.fromScene(room,.04);
  scene.environment = environment.texture;
  scene.environmentIntensity = .64;
  room.dispose();
  pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xffffff,0x8d877d,1.55));
  const key = new THREE.DirectionalLight(0xfff5e7,2.1);
  key.position.set(-240,840,350);
  key.target.position.set(0,60,0);
  key.castShadow = true;
  key.shadow.mapSize.set(2048,2048);
  Object.assign(key.shadow.camera,{left:-335,right:335,top:365,bottom:-345,near:20,far:1400});
  key.shadow.normalBias=.28;
  key.shadow.bias=-.0003;
  scene.add(key,key.target);
  const fill=new THREE.DirectionalLight(0xcce1ed,1.3);
  fill.position.set(280,230,-210);
  scene.add(fill);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(2600,2600),new THREE.ShadowMaterial({opacity:.11}));
  floor.rotation.x=-Math.PI/2;
  floor.position.y=-.6;
  floor.receiveShadow=true;
  scene.add(floor);

  const controls = new OrbitControls(camera,renderer.domElement);
  controls.minZoom=.55;
  controls.maxZoom=4.5;
  controls.maxPolarAngle=Math.PI*.492;
  controls.enableDamping=false;
  const meshes=[];
  let file;
  try {
    file=await new GLTFLoader().loadAsync(new URL('./consola.glb',import.meta.url).href);
  } catch (error) {
    renderer.domElement.remove();
    controls.dispose();
    environment.dispose();
    renderer.dispose();
    throw error;
  }
  file.scene.traverse(part=>{
    if(!part.isMesh)return;
    // The public GLB stores coordinates in hundredths of a millimetre, then applies
    // a Y-up, metric root transform. Simulation distances below are expressed in mm.
    const packed=part.geometry.getAttribute('position');
    const mm=new Float32Array(packed.count*3);
    for(let i=0;i<packed.count;i++){
      mm[3*i]=packed.getX(i)/100;
      mm[3*i+1]=packed.getY(i)/100;
      mm[3*i+2]=packed.getZ(i)/100;
    }
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.BufferAttribute(mm,3));
    geometry.setIndex(part.geometry.index);
    geometry.computeVertexNormals();
    geometry.computeBoundingBox();
    const color=part.material.color;
    const mesh=new THREE.Mesh(geometry,new THREE.MeshStandardMaterial({
      color, roughness:part.material.roughness, metalness:part.material.metalness
    }));
    mesh.name=part.name;
    mesh.userData.group=part.userData.group;
    mesh.castShadow=mesh.receiveShadow=part.userData.group!=='power';
    if(part.userData.group==='power'){
      mesh.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry),new THREE.LineBasicMaterial({color:0xb67b31})));
    }
    model.add(mesh);
    meshes.push(mesh);
  });
  if(meshes.length<100)throw new Error('Faltan piezas del conjunto');

  const guides=[];
  function guide(x,y,z,w,d,h,color,kind){
    const geometry=new THREE.BoxGeometry(w,d,h);
    const item=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({color,transparent:true,opacity:.12,depthWrite:false}));
    item.add(new THREE.LineSegments(new THREE.EdgesGeometry(geometry),new THREE.LineBasicMaterial({color,transparent:true,opacity:.83})));
    item.position.set(x,y,z);
    item.userData={baseY:y,kind};
    model.add(item);
    guides.push(item);
  }
  guide(-82.5,138,96,20,250,8,0x167765,'Y');
  guide(72.5,138,96,20,250,8,0x167765,'Y');
  guide(-5,152,136.5,150,20,8,0xbd6a16,'X');
  const project=new THREE.Vector3();
  const frame=new THREE.Box3();
  let mode='outside', angle='iso', tags=[], pose={x:0,y:0,z:0,on:false};

  function render(){
    renderer.render(scene,camera);
    onDraw(tags.map(tag=>{
      const [,,xyz,name]=tag;
      project.set(...xyz);
      if(name.startsWith('Patin_')){project.y+=pose.y;if(name==='Patin_X')project.x+=pose.x;}
      if(name.startsWith('C922_')||name.startsWith('Capota_'))project.z+=pose.z;
      project.applyMatrix4(model.matrixWorld).project(camera);
      return {left:(project.x+1)*50,top:(1-project.y)*50,visible:project.z<=1&&Math.abs(project.x)<.98&&Math.abs(project.y)<.98};
    }));
  }
  function place(next){
    pose=next;
    for(const mesh of meshes){
      const g=mesh.userData.group;
      const movesX=g==='movingX'||g==='herrajesX';
      const movesY=movesX||g==='movingY'||g==='herrajesY';
      const movesZ=g==='pod'||g==='camera'||g==='herrajesOptica';
      mesh.matrixAutoUpdate=true;
      mesh.rotation.set(0,0,0);
      mesh.position.set(movesX?pose.x:0,movesY?pose.y:0,movesZ?pose.z:0);
      if(mesh.name==='S301T_palanca'&&pose.on){
        mesh.matrix.makeTranslation(48,22,29)
          .multiply(new THREE.Matrix4().makeRotationX(-32*Math.PI/180))
          .multiply(new THREE.Matrix4().makeTranslation(-48,-22,-29));
        mesh.matrixAutoUpdate=false;
      }
    }
    for(const item of guides){
      item.visible=mode==='travel';
      item.position.y=item.userData.baseY+(item.userData.kind==='X'?pose.y:0);
    }
    model.updateMatrixWorld(true);
  }
  function frameView(){
    if(!renderer.domElement.isConnected)return;
    const width=viewer.clientWidth, height=viewer.clientHeight;
    if(!width||!height)return;
    renderer.setSize(width,height,false);
    frame.makeEmpty();
    for(const mesh of meshes)if(mesh.visible)frame.union(mesh.geometry.boundingBox.clone().applyMatrix4(mesh.matrixWorld));
    const center=frame.getCenter(new THREE.Vector3());
    camera.up.set(0,angle==='top'?0:1,angle==='top'?-1:0);
    const directions={front:[.0002,.025,1],top:[.0001,1,.0001],rear:[.88,.64,-1.25]};
    const perspectives={switch:[.72,.31,1.05],electronics:[.57,1.8,1],travel:[.6,1.05,1.35]};
    const dir=new THREE.Vector3(...(directions[angle]||perspectives[mode]||[.86,.66,1.24]));
    controls.target.copy(center);
    camera.position.copy(center).addScaledVector(dir.normalize(),900);
    camera.lookAt(center);
    camera.zoom=1;
    camera.updateMatrixWorld();
    const horizontal=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,0);
    const vertical=new THREE.Vector3().setFromMatrixColumn(camera.matrixWorld,1);
    const extent=[Infinity,-Infinity,Infinity,-Infinity];
    for(const mesh of meshes)if(mesh.visible){
      const b=mesh.geometry.boundingBox;
      for(const x of [b.min.x,b.max.x])for(const y of [b.min.y,b.max.y])for(const z of [b.min.z,b.max.z]){
        project.set(x,y,z).applyMatrix4(mesh.matrixWorld).sub(center);
        const a=project.dot(horizontal),d=project.dot(vertical);
        extent[0]=Math.min(extent[0],a);extent[1]=Math.max(extent[1],a);
        extent[2]=Math.min(extent[2],d);extent[3]=Math.max(extent[3],d);
      }
    }
    const aspect=width/height;
    const half=Math.max((extent[3]-extent[2])/2,(extent[1]-extent[0])/(2*aspect))*1.16;
    const delta=horizontal.multiplyScalar((extent[1]+extent[0])/2).add(vertical.multiplyScalar((extent[3]+extent[2])/2));
    camera.position.add(delta);
    controls.target.add(delta);
    Object.assign(camera,{left:-half*aspect,right:half*aspect,top:half,bottom:-half});
    camera.updateProjectionMatrix();
    controls.update();
    render();
  }
  function filter(mesh,groups){
    const g=mesh.userData.group,n=mesh.name;
    if(!groups.includes(g))return false;
    if(mode==='electronics' && (n.startsWith('Carcasa_') || n==='USB_camara_fijo'))return false;
    if(mode==='travel' && g==='herrajesFijos' && !n.includes('Guias_Y'))return false;
    if(mode==='electronics' && g==='herrajesFijos' && !/MKS|LCD/.test(n))return false;
    return mode!=='hardware'||g.startsWith('herrajes')||/^(Carcasa|Tabique|Asiento_Y|Puente_transversal|Carro_portapunta|Portico_camara)/.test(n);
  }
  controls.addEventListener('change',render);
  const observer=new ResizeObserver(frameView);
  observer.observe(viewer);
  return {
    select(view,definition,nextPose,position){
      mode=view;tags=definition.tags;angle=position;
      for(const mesh of meshes){
        mesh.visible=filter(mesh,definition.groups);
        const g=mesh.userData.group, translucent=mode==='hardware'&&!g.startsWith('herrajes');
        mesh.material.transparent=translucent||g==='power';
        mesh.material.depthWrite=!mesh.material.transparent;
        mesh.material.opacity=translucent?.11:g==='power'?.25:1;
        mesh.material.emissive.setHex(0);
      }
      place(nextPose);frameView();
    },
    angle(next){angle=next;frameView();},
    pose(next){place(next);render();},
    mark(prefix){
      for(const mesh of meshes)mesh.material.emissive.setHex(prefix&&mesh.name.startsWith(prefix)?0x125c4e:0);
      render();
    },
    redraw:render
  };
}
