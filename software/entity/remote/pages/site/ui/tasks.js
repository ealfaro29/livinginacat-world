const es = document.documentElement.lang === "es";
const tr = (spanish, english) => es ? spanish : english;
const byId = id => document.getElementById(id);
const input = byId("instructions"), mode = byId("timing"), date = byId("scheduled");
const submit = byId("submit-task"), feedback = byId("task-feedback");
const storage = "entity-task-draft-v1";
const labels = {
  queued: tr("En cola","Queued"), running: tr("En curso","Running"), done: tr("Completada","Completed"),
  failed: tr("Fallida","Failed"), cancelled: tr("Eliminada de la cola","Removed from queue"),
  interrupted: tr("Interrumpida","Interrupted"),
};
const errors = {
  past_time: tr("Elegí una fecha y hora futuras.","Choose a future date and time."),
  invalid_time: tr("Revisá la fecha y hora.","Check the date and time."),
  invalid_task: tr("Escribí entre 1 y 2000 caracteres.","Enter 1 to 2000 characters."),
  queue_changed: tr("La cola cambió. Revisá el orden actualizado.","The queue changed. Check the refreshed order."),
  request_conflict: tr("Esta solicitud ya tiene otro contenido. Editá el texto y reintentá.","This request already has different content. Edit the text and retry."),
  device_offline: tr("No se pudo llegar a Alfonsito. Tu borrador sigue aquí.","Could not reach Alfonsito. Your draft is still here."),
  sign_in: tr("Tu sesión venció. Volvé al inicio para ingresar.","Your session expired. Return to the dashboard to sign in."),
  operator_required: tr("Ingresá con la cuenta de operador.","Sign in with the operator account."),
  execution_error: tr("La ejecución se detuvo. Revisá la conexión del equipo y del proveedor.","Execution stopped. Check equipment and provider connectivity."),
  provider_declined: tr("El proveedor declinó la tarea.","The provider declined the task."),
  action_failed: tr("Alfonsito no pudo completar esa acción.","Alfonsito could not complete the action."),
  unconfirmed: tr("Alfonsito no pudo confirmar el resultado.","Alfonsito could not verify the result."),
  limit: tr("Se alcanzó el límite de tiempo o de acciones.","The time or action limit was reached."),
};
let key = crypto.randomUUID(), online = false, busy = false, stamp = "", revision = 0;
const draft = () => ({text:input.value,mode:mode.value,at:date.value,key});
function save() { try { sessionStorage.setItem(storage,JSON.stringify(draft())); } catch {} }
function load() {
  try {
    const d=JSON.parse(sessionStorage.getItem(storage));
    if (!d || typeof d.text !== "string") return;
    input.value=d.text; mode.value=d.mode==="later"?"later":"now"; date.value=d.at||""; key=d.key||key;
  } catch {}
}
function timing() {
  const later=mode.value==="later";
  byId("schedule-field").hidden=!later; date.required=later;
  submit.textContent=later?tr("Programar tarea","Schedule task"):tr("Agregar a la cola","Add to queue");
  submit.disabled=!online||busy;
}
function el(name,txt,cls) {
  const node=document.createElement(name);
  if (txt!==undefined) node.textContent=txt;
  if (cls) node.className=cls;
  return node;
}
const dateFormat = new Intl.DateTimeFormat(es?"es-CR":"en",{dateStyle:"medium",timeStyle:"short"});
function detail(row,meta) {
  const box=el("div",undefined,"queue-detail");
  box.append(el("p",row.instructions||row.title,"queue-title"));
  if (meta) box.append(el("p",meta,"queue-meta"));
  return box;
}
function resultText(value) { return value && (errors[value.slice(1)] && value.startsWith("@") ? errors[value.slice(1)] : value); }
function draw(view) {
  online=true; timing();
  byId("task-connection").textContent=view.ready?"":tr("Podés agregar tareas. Empezarán cuando el equipo esté listo.","You can add tasks. They will start when the equipment is ready.");
  const next=JSON.stringify([view.queue,view.current,view.last,view.action]);
  if(next===stamp)return;
  stamp=next;
  const focusId=document.activeElement?.dataset.queueKey;
  const waiting=byId("waiting-tasks");
  waiting.replaceChildren();
  byId("empty-queue").hidden=!!view.queue.length;
  view.queue.forEach((row,i)=>{
    const item=el("li",undefined,"queue-item");
    const time=row.run_at?dateFormat.format(row.run_at*1000):tr("Turno disponible","Next available turn");
    item.append(detail(row,(i+1)+". "+time+(row.instructions?"":tr(" · Cliente MCP"," · MCP client"))));
    const actions=el("div",undefined,"queue-actions");
    const buttons=[
      ["up","↑",tr("Subir","Move up"),view.queue[i-1]],
      ["down","↓",tr("Bajar","Move down"),view.queue[i+1]],
      ["remove",tr("Eliminar","Remove"),tr("Eliminar","Remove"),row],
    ];
    for(const [kind,symbol,label,other] of buttons){
      const button=el("button",symbol,"small");
      button.type="button"; button.disabled=!other; button.dataset.queueKey=row.id+"-"+kind;
      button.setAttribute("aria-label",label+" · "+row.title); button.title=label;
      button.addEventListener("click",()=>mutate(kind==="remove"?{action:kind,id:row.id}:{action:"move",id:row.id,neighbor:other.id,direction:kind},
        kind==="remove"?tr("Tarea eliminada.","Task removed."):tr("Orden actualizado.","Order updated.")));
      actions.append(button);
    }
    item.append(actions); waiting.append(item);
  });
  if(focusId) [...waiting.querySelectorAll("button")].find(b=>b.dataset.queueKey===focusId&&!b.disabled)?.focus({preventScroll:true});
  const current=byId("current-task");
  current.replaceChildren(view.current?detail(view.current,view.action):el("p",tr("Alfonsito está en reposo.","Alfonsito is idle."),"queue-empty"));
  const last=view.last; byId("last-section").hidden=!last;
  if(last)byId("last-task").replaceChildren(detail(last,[labels[last.state],resultText(last.result)].filter(Boolean).join(" · ")));
}
async function api(body) {
  const resp=await fetch("/entity/api/tasks",body?{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),cache:"no-store"}:{cache:"no-store"});
  let data;try{data=await resp.json();}catch{throw Error("device_offline");}
  if(!resp.ok)throw Error(data.error||"device_offline");
  return data;
}
function unavailable(e) {
  online=false; timing();
  byId("task-connection").textContent=errors[e.message]||errors.device_offline;
}
async function refresh() {
  if(busy)return;
  const ticket=++revision;
  try{const view=await api();if(ticket===revision)draw(view);}
  catch(e){if(ticket===revision)unavailable(e);}
}
async function mutate(body,notice) {
  if(busy||!online)return;
  busy=true;revision++;timing();
  const formSnapshot=JSON.stringify(draft());
  try{
    const view=await api(body);
    if(body.action==="add" && formSnapshot===JSON.stringify(draft())) {
      input.value="";mode.value="now";date.value="";key=crypto.randomUUID();save();
    }
    draw(view);feedback.textContent=notice;
  }catch(e){
    feedback.textContent=errors[e.message]||errors.device_offline;
    if(e.message==="device_offline"||e.message==="sign_in"||e instanceof TypeError)unavailable(e);
  }finally{busy=false;timing();await refresh();}
}
load(); timing();
byId("zone").textContent=Intl.DateTimeFormat().resolvedOptions().timeZone;
for(const field of [input,mode,date])field.addEventListener("input",()=>{key=crypto.randomUUID();feedback.textContent="";timing();save();});
byId("composer").addEventListener("submit",e=>{
  e.preventDefault();
  const instructions=input.value.trim();
  if(!instructions){feedback.textContent=errors.invalid_task;input.focus();return;}
  const run_at=mode.value==="later"?Math.floor(new Date(date.value).getTime()/1000):null;
  if(run_at!==null&&(!Number.isFinite(run_at)||run_at<=Date.now()/1000)){feedback.textContent=errors.past_time;date.focus();return;}
  save();mutate({action:"add",request_id:key,instructions,run_at},run_at?tr("Tarea programada.","Task scheduled."):tr("Tarea agregada.","Task added."));
});
async function poll(){await refresh();setTimeout(poll,3000);}
poll();
