const select=document.getElementById("asignatura");
const result=document.getElementById("resultado");
async function cargar(){
  try{
    const r=await fetch("/api/asignaturas");
    if(!r.ok) throw Error("No se pudo cargar asignaturas");
    const items=await r.json();
    select.innerHTML='<option value="">Seleccionar asignatura</option>';
    items.forEach(x=>{const o=document.createElement("option");o.value=x.id;o.textContent=x.nombre;select.append(o)});
  }catch(e){result.textContent="Error: "+e.message}
}
document.getElementById("enviar").addEventListener("click",async()=>{
  result.textContent="Procesando...";
  try{
    const r=await fetch("/api/consultas",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({asignatura_id:Number(select.value),pregunta:document.getElementById("pregunta").value})});
    const data=await r.json();
    if(!r.ok)throw Error(typeof data.detail==="string"?data.detail:"Revisa los datos");
    result.textContent=`Consulta registrada con ID ${data.id}. Estado: ${data.estado}.`;
  }catch(e){result.textContent="No se pudo registrar: "+e.message}
});
cargar();