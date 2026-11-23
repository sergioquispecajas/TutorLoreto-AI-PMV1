/* TutorLoreto AI · Biblioteca local y tutor en línea (extensión aditiva). */
'use strict';
(() => {
  const vistas = ['biblioteca','biblioteca-asignatura','biblioteca-tema','tutor-online'];
  vistas.forEach(v => VISTAS.add(v));
  const estado = {grado:1, curso:null, tema:null, chat:[], enviando:false};
  const $b = id => document.getElementById(id);
  const seguro = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  async function api(url, options={}) {
    let response;
    try { response = await fetch(url, {cache:'no-store', ...options}); }
    catch { throw new Error('No hay conexión con el servidor. Si estás en el colegio, comprueba la red local.'); }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'No se pudo completar la solicitud.');
    return data;
  }
  function insertarPantallas() {
    const main = document.querySelector('#contenido');
    if (!main || $b('vista-biblioteca')) return;
    main.insertAdjacentHTML('beforeend', `
      <section class="vista tl-extra" id="vista-biblioteca" data-vista="biblioteca" hidden aria-labelledby="tl-biblioteca-titulo">
        <header class="cabecera cabecera-simple"><button class="flecha-volver" type="button" data-ir="inicio" aria-label="Volver">←</button><div><span class="eyebrow">APRENDE A TU RITMO</span><h1 id="tl-biblioteca-titulo">Biblioteca educativa</h1></div></header>
        <div class="contenido-pantalla">
          <p class="texto-ayuda">Explora contenidos organizados para tu grado. Los textos se guardan en el servidor escolar y se pueden consultar sin Internet.</p>
          <label class="tl-label" for="tl-grado">Mi grado de secundaria</label>
          <select id="tl-grado" class="tl-select"><option value="1">1.º de secundaria</option><option value="2">2.º de secundaria</option><option value="3">3.º de secundaria</option><option value="4">4.º de secundaria</option><option value="5">5.º de secundaria</option></select>
          <div class="tl-section-heading"><h2>Elige una asignatura</h2><span>11 áreas</span></div>
          <div id="tl-cursos" class="tl-courses" aria-live="polite"><p class="texto-ayuda">Cargando biblioteca local…</p></div>
          <p id="tl-biblioteca-error" class="tl-error" role="alert" hidden></p>
          <div class="tl-offline-note">🌿 <span>Biblioteca local: los contenidos de texto no requieren conexión externa.</span></div>
        </div>
      </section>
      <section class="vista tl-extra" id="vista-biblioteca-asignatura" data-vista="biblioteca-asignatura" hidden aria-labelledby="tl-curso-titulo">
        <header class="cabecera cabecera-simple"><button class="flecha-volver" type="button" data-ir="biblioteca" aria-label="Volver a biblioteca">←</button><div><span class="eyebrow">BIBLIOTECA · ASIGNATURA</span><h1 id="tl-curso-titulo">Asignatura</h1></div></header>
        <div class="contenido-pantalla"><p id="tl-curso-descripcion" class="texto-ayuda"></p><div id="tl-temas" class="tl-topic-list"></div><p id="tl-curso-error" class="tl-error" role="alert" hidden></p></div>
      </section>
      <section class="vista tl-extra" id="vista-biblioteca-tema" data-vista="biblioteca-tema" hidden aria-labelledby="tl-tema-titulo">
        <header class="cabecera cabecera-simple"><button class="flecha-volver" type="button" data-ir="biblioteca-asignatura" aria-label="Volver a temas">←</button><div><span class="eyebrow">MATERIAL DE ESTUDIO</span><h1 id="tl-tema-titulo">Tema</h1></div></header>
        <div class="contenido-pantalla">
          <div class="tl-topic-meta" id="tl-tema-meta"></div>
          <article class="tl-lesson"><h2>¿Qué aprenderás?</h2><p id="tl-tema-resumen"></p><h2>Ejemplo para comprender</h2><p id="tl-tema-ejemplo"></p></article>
          <section class="tl-video-panel"><div class="tl-video-icon">▶</div><div><h2>Videos explicativos</h2><p>Encuentra explicaciones audiovisuales relacionadas con este tema.</p></div><a id="tl-video-link" class="btn btn-primario btn-ancho" href="#" target="_blank" rel="noopener noreferrer">Buscar videos en YouTube ↗</a><div id="tl-video-results" class="tl-video-results" aria-live="polite"></div><small>Los videos necesitan Internet y los resultados pertenecen a YouTube. Revisa el contenido con orientación de tu docente.</small></section>
          <div class="tl-offline-note">📘 La explicación y el ejemplo de esta pantalla están disponibles desde el servidor escolar sin Internet.</div>
          <button class="btn btn-secundario btn-ancho" type="button" data-ir="biblioteca-asignatura">Volver a los temas</button>
        </div>
      </section>
      <section class="vista tl-extra" id="vista-tutor-online" data-vista="tutor-online" hidden aria-labelledby="tl-chat-titulo">
        <header class="cabecera cabecera-simple"><button class="flecha-volver" type="button" data-ir="inicio" aria-label="Volver">←</button><div><span class="eyebrow">MODALIDAD COMPLEMENTARIA · INTERNET</span><h1 id="tl-chat-titulo">Tutor en línea</h1></div></header>
        <div class="contenido-pantalla">
          <div class="tl-online-info"><strong>¿Tienes conexión a Internet?</strong><p>Conversa con un modelo de IA en la nube para ampliar tus explicaciones. Esta función es opcional; el tutor local sigue disponible sin Internet.</p><button class="btn btn-secundario btn-ancho" type="button" data-ir="consulta">← Usar tutor local sin Internet</button></div>
          <div class="tl-chat-settings"><label class="tl-label" for="tl-chat-grado">Grado</label><select id="tl-chat-grado" class="tl-select"><option value="1">1.º</option><option value="2">2.º</option><option value="3">3.º</option><option value="4">4.º</option><option value="5">5.º</option></select><label class="tl-label" for="tl-chat-asignatura">Asignatura</label><select id="tl-chat-asignatura" class="tl-select"><option>General</option><option>Matemática</option><option>Comunicación</option><option>Ciencia y Tecnología</option><option>Ciencias Sociales</option><option>Inglés</option></select></div>
          <div id="tl-chat-mensajes" class="tl-chat-messages" aria-live="polite"><div class="tl-chat-bubble assistant">¡Hola! Soy tu tutor en línea. ¿Qué tema te gustaría comprender hoy?</div></div>
          <form id="tl-chat-form" class="tl-chat-form"><label class="sr-only" for="tl-chat-input">Escribe tu pregunta</label><textarea id="tl-chat-input" rows="2" maxlength="4000" placeholder="Escribe tu pregunta…" required></textarea><button class="btn btn-primario" type="submit" id="tl-chat-enviar">Enviar ↑</button></form>
          <p id="tl-chat-estado" class="tl-chat-status" role="status" aria-live="polite"></p>
          <p class="tl-privacy-note">No compartas tu nombre completo, DNI, dirección, contraseñas ni información privada. El uso de IA en la nube puede tener costos y depende del proveedor configurado por el colegio.</p>
        </div>
      </section>`);
  }
  function ponerError(id, message) { const el=$b(id); if(el){el.textContent=message;el.hidden=!message;} }
  async function cargarBiblioteca() {
    const caja=$b('tl-cursos'); caja.innerHTML='<p class="texto-ayuda">Cargando asignaturas…</p>';
    ponerError('tl-biblioteca-error','');
    try {
      const data=await api('/api/biblioteca?grado='+estado.grado);
      caja.replaceChildren();
      data.asignaturas.forEach(curso=>{
        const button=document.createElement('button');button.type='button';button.className='tl-course-card';
        button.innerHTML='<span class="tl-course-icon">'+seguro(curso.icono)+'</span><span><strong>'+seguro(curso.nombre)+'</strong><small>'+curso.cantidad_temas+' tema(s) para este grado</small></span><span class="tl-course-arrow">→</span>';
        button.addEventListener('click',()=>abrirAsignatura(curso));caja.append(button);
      });
      if(!data.asignaturas.length)caja.textContent='Todavía no hay contenidos para este grado.';
    } catch(e){caja.replaceChildren();ponerError('tl-biblioteca-error',e.message);}
  }
  async function abrirAsignatura(curso) {
    estado.curso=curso; $b('tl-curso-titulo').textContent=curso.nombre;
    $b('tl-curso-descripcion').textContent='Selecciona un tema de '+curso.nombre+' para estudiar.';
    ir('biblioteca-asignatura');
    const caja=$b('tl-temas');caja.innerHTML='<p class="texto-ayuda">Cargando temas…</p>';ponerError('tl-curso-error','');
    try{
      const data=await api('/api/biblioteca/'+encodeURIComponent(curso.slug)+'?grado='+estado.grado);
      caja.replaceChildren();
      data.temas.forEach(tema=>{
        const button=document.createElement('button');button.type='button';button.className='tl-topic-card';
        button.innerHTML='<span class="tl-topic-unit">'+seguro(tema.unidad)+'</span><strong>'+seguro(tema.titulo)+'</strong><small>Ver explicación y recursos →</small>';
        button.addEventListener('click',()=>abrirTema(tema));caja.append(button);
      });
      if(!data.temas.length)caja.textContent='No hay temas cargados para este grado.';
    }catch(e){caja.replaceChildren();ponerError('tl-curso-error',e.message);}
  }
  async function abrirTema(tema) {
    estado.tema=tema; ir('biblioteca-tema');
    try{
      const data=await api('/api/biblioteca/'+encodeURIComponent(estado.curso.slug)+'/'+encodeURIComponent(tema.slug)+'?grado='+estado.grado);
      $b('tl-tema-titulo').textContent=data.tema.titulo;
      $b('tl-tema-meta').textContent=data.asignatura+' · '+data.grado+'.º de secundaria · '+data.tema.unidad;
      $b('tl-tema-resumen').textContent=data.tema.resumen;
      $b('tl-tema-ejemplo').textContent=data.tema.ejemplo;
      const link=$b('tl-video-link');link.href=data.video_url; cargarVideos(tema.slug);
    }catch(e){$b('tl-tema-resumen').textContent=e.message;}
  }
  async function cargarVideos(temaSlug) {
    const caja=$b('tl-video-results');caja.replaceChildren();
    try {
      const data=await api('/api/biblioteca/'+encodeURIComponent(estado.curso.slug)+'/'+encodeURIComponent(temaSlug)+'/videos?grado='+estado.grado);
      if(data.videos && data.videos.length) {
        data.videos.forEach(video=>{
          const card=document.createElement('article');card.className='tl-video-card';
          const frame=document.createElement('iframe');
          frame.src='https://www.youtube-nocookie.com/embed/'+video.id;
          frame.title=video.titulo;frame.loading='lazy';frame.referrerPolicy='strict-origin-when-cross-origin';
          frame.allow='accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
          frame.allowFullscreen=true;card.append(frame);
          const title=document.createElement('strong');title.textContent=video.titulo;card.append(title);
          const channel=document.createElement('small');channel.textContent=video.canal;card.append(channel);
          caja.append(card);
        });
      } else {
        const note=document.createElement('p');note.className='tl-video-fallback';
        note.textContent=data.detalle || 'Puedes buscar videos relacionados en YouTube.';
        caja.append(note);
      }
    } catch(e) {
      const note=document.createElement('p');note.className='tl-video-fallback';
      note.textContent='No se pudieron cargar videos automáticamente. Usa el enlace de búsqueda de YouTube.';
      caja.append(note);
    }
  }
  function agregarMensaje(role, text) {
    const bubble=document.createElement('div');bubble.className='tl-chat-bubble '+role;bubble.textContent=text;
    $b('tl-chat-mensajes').append(bubble);bubble.scrollIntoView({block:'nearest'});
  }
  async function enviarChat(evento) {
    evento.preventDefault();if(estado.enviando)return;
    const input=$b('tl-chat-input'), mensaje=input.value.trim();if(!mensaje)return;
    estado.enviando=true;$b('tl-chat-enviar').disabled=true;agregarMensaje('user',mensaje);input.value='';
    const historial=estado.chat.slice(-8);estado.chat.push({role:'user',content:mensaje});
    $b('tl-chat-estado').textContent='El tutor está preparando una explicación…';
    try{
      const data=await api('/api/tutor-online/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({
        mensaje,grado:Number($b('tl-chat-grado').value),asignatura:$b('tl-chat-asignatura').value,historial
      })});
      agregarMensaje('assistant',data.respuesta);estado.chat.push({role:'assistant',content:data.respuesta});
      $b('tl-chat-estado').textContent='Respuesta generada por IA en línea.';
    }catch(e){$b('tl-chat-estado').textContent=e.message;agregarMensaje('assistant','No pude responder en este momento. Puedes volver al tutor local desde el botón superior.');}
    finally{estado.enviando=false;$b('tl-chat-enviar').disabled=false;input.focus();}
  }
  function agregarAccesosInicio() {
    const grid=document.querySelector('#vista-inicio .accesos-grid');
    if(!grid || $b('tl-home-learning'))return;
    const section=document.createElement('section');section.id='tl-home-learning';section.className='tl-home-section';
    section.innerHTML='<div class="tl-home-title"><div><span class="eyebrow">RECURSOS PARA APRENDER</span><h2>Explora y pregunta</h2></div><span class="tl-home-badge">LOCAL + ONLINE</span></div><p>Estudia sin Internet y aprovecha recursos en línea cuando tengas conexión.</p><div class="tl-home-grid"><button type="button" class="tl-home-card" data-ir="biblioteca"><span>📚</span><strong>Biblioteca educativa</strong><small>Asignaturas, grados y temas</small></button><button type="button" class="tl-home-card" data-ir="tutor-online"><span>☁️</span><strong>Tutor en línea</strong><small>Chat con IA por Internet</small></button></div>';
    grid.insertAdjacentElement('afterend',section);
  }
  function prepararVista(vista) {
    if(vista==='biblioteca')cargarBiblioteca();
    if(vista==='tutor-online')estado.chat.length===0 && comprobarTutorOnline();
  }
  async function comprobarTutorOnline(){
    try{const data=await api('/api/tutor-online/estado');$b('tl-chat-estado').textContent=data.disponible?'Servicio en línea configurado.':'El servicio aún no está configurado por el administrador.';}
    catch(e){$b('tl-chat-estado').textContent=e.message;}
  }
  insertarPantallas();agregarAccesosInicio();
  $b('tl-grado').addEventListener('change',()=>{estado.grado=Number($b('tl-grado').value);cargarBiblioteca();});
  $b('tl-chat-form').addEventListener('submit',enviarChat);
  document.addEventListener('click',event=>{
    const btn=event.target.closest('[data-ir]');
    if(btn && vistas.includes(btn.dataset.ir)) prepararVista(btn.dataset.ir);
    if(btn && btn.dataset.ir==='biblioteca-asignatura' && estado.curso) abrirAsignatura(estado.curso);
  });
  const originalIr=ir;
  // El router original sigue controlando todas las vistas PMV1/PMV2/PMV3.
  window.addEventListener('popstate',()=>{if(vistas.includes(stateVistaActual()))prepararVista(stateVistaActual());});
  function stateVistaActual(){return document.querySelector('[data-vista]:not([hidden])')?.dataset.vista||'';}
  void originalIr;
})();