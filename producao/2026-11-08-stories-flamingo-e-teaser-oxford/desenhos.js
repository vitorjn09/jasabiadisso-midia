// desenhos parados no estilo Pedra do Mar (os mesmos traços dos Reels), para stories
const PINK='#EF8FA8', DEEP='#E06F8E';
const mixc=(a,b,k)=>{const h=x=>[1,3,5].map(i=>parseInt(x.slice(i,i+2),16));const A=h(a),B=h(b);return '#'+A.map((v,i)=>Math.round(v+(B[i]-v)*k).toString(16).padStart(2,'0')).join('');};
// flamingo do Reel "flamingo-rosa-comida" (centro do corpo em 0,0)
function flamingo(o={}){
  const c=o.col||PINK, d=mixc(c,'#2A3B3A',0.22), lk=o.look??[0.3,0];
  const neck='M95,-40 C190,-120 150,-200 70,-250 C0,-295 10,-360 50,-385'; const hx=50, hy=-400; const knee=o.legUp??1;
  const lerp=(a,b,k)=>a+(b-a)*k;
  return `<path d="M-20,80 L-20,430" stroke="#2A3B3A" stroke-width="22" stroke-linecap="round"/><path d="M-20,80 L-20,430" stroke="${d}" stroke-width="12" stroke-linecap="round"/>
   <path d="M-46,432 L6,432" stroke="#2A3B3A" stroke-width="14" stroke-linecap="round"/>
   <path d="M20,80 L${lerp(20,70,knee)},${lerp(430,240,knee)} L${lerp(20,-10,knee)},${lerp(430,330,knee)}" fill="none" stroke="#2A3B3A" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>
   <path d="M20,80 L${lerp(20,70,knee)},${lerp(430,240,knee)} L${lerp(20,-10,knee)},${lerp(430,330,knee)}" fill="none" stroke="${d}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>
   <path d="${neck}" fill="none" stroke="#2A3B3A" stroke-width="58" stroke-linecap="round"/><path d="${neck}" fill="none" stroke="${c}" stroke-width="42" stroke-linecap="round"/>
   <path d="M-190,-10 C-170,-90 40,-120 130,-40 C170,10 120,90 20,95 C-90,100 -200,70 -190,-10Z" fill="${c}" class="st"/>
   <path d="M-210,-20 L-250,-50 L-230,0 L-260,10 L-200,30Z" fill="${d}" class="st" stroke-width="7"/>
   <path d="M-120,-30 C-60,-70 40,-60 70,0 C20,40 -80,40 -120,-30Z" fill="${d}" class="st" stroke-width="7"/>
   <circle cx="${hx}" cy="${hy}" r="50" fill="${c}" class="st"/>
   <path d="M${hx+38},${hy-20} L${hx+108},${hy-4} Q${hx+124},${hy+34} ${hx+92},${hy+62} L${hx+70},${hy+30} Q${hx+60},${hy+12} ${hx+40},${hy+14}Z" fill="#F3EFE7" class="st" stroke-width="7"/>
   <path d="M${hx+100},${hy+18} Q${hx+118},${hy+40} ${hx+92},${hy+62} L${hx+80},${hy+44}Z" fill="#2A3B3A"/>
   ${o.wink?`<path d="M${hx-14},${hy-8} q14,-14 28,0" fill="none" stroke="#2A3B3A" stroke-width="7" stroke-linecap="round"/>`:`<ellipse cx="${hx}" cy="${hy-8}" rx="16" ry="19" fill="#fff" class="st" stroke-width="6"/><circle cx="${hx+lk[0]*7}" cy="${hy-6+lk[1]*7}" r="8" fill="#2A3B3A"/><circle cx="${hx+lk[0]*7+3}" cy="${hy-10+lk[1]*7}" r="3" fill="#fff"/>`}
   <ellipse cx="${hx-18}" cy="${hy+22}" rx="14" ry="8" fill="${DEEP}" opacity=".5"/>`;
}
function eyes(x1,x2,y,r=18){ return [x1,x2].map(x=>`<ellipse cx="${x}" cy="${y}" rx="${r}" ry="${r*1.2}" fill="#fff" class="st" stroke-width="6"/><circle cx="${x+3}" cy="${y+4}" r="${r*0.5}" fill="#2A3B3A"/><circle cx="${x+7}" cy="${y-2}" r="${r*0.18}" fill="#fff"/>`).join(''); }
// torre de universidade antiga (pedra) com carinha; base em y=0
function torre(){ return `<rect x="-150" y="-380" width="300" height="380" fill="#E8C98E" class="st"/>
  <path d="M-150,-380 L-150,-430 L-110,-430 L-110,-400 L-60,-400 L-60,-430 L-20,-430 L-20,-400 L20,-400 L20,-430 L60,-430 L60,-400 L110,-400 L110,-430 L150,-430 L150,-380Z" fill="#E8C98E" class="st"/>
  <path d="M-80,-430 L0,-560 L80,-430Z" fill="#4F8079" class="st"/><path d="M0,-560 L0,-610" stroke="#2A3B3A" stroke-width="8" stroke-linecap="round"/><path d="M0,-610 L44,-596 L0,-582Z" fill="#D9B26F" class="st" stroke-width="5"/>
  <path d="M-50,0 L-50,-90 A50,50 0 0 1 50,-90 L50,0Z" fill="#2A3B3A"/>
  <path d="M-110,-300 l40,0 M40,-310 l60,0 M-120,-180 l50,0 M60,-150 l50,0" stroke="#2A3B3A" stroke-width="5" opacity=".35" stroke-linecap="round"/>
  ${eyes(-50,50,-250,26)}<path d="M-30,-185 q30,22 60,0" fill="none" stroke="#2A3B3A" stroke-width="8" stroke-linecap="round"/>
  <ellipse cx="-95" cy="-200" rx="22" ry="12" fill="#C8695A" opacity=".35"/><ellipse cx="95" cy="-200" rx="22" ry="12" fill="#C8695A" opacity=".35"/>`; }
// pirâmide em degraus (templo) com carinha; base em y=0
function templo(){ let s=''; const L=[[280,90],[220,90],[160,90],[100,80]]; let y=0;
  L.forEach(([w,h])=>{ s+=`<rect x="${-w}" y="${y-h}" width="${2*w}" height="${h}" fill="#C9A06A" class="st"/>`; y-=h; });
  s+=`<rect x="-60" y="${y-90}" width="120" height="90" fill="#E8C98E" class="st"/><rect x="-24" y="${y-60}" width="48" height="60" fill="#2A3B3A"/>`;
  s+=`<path d="M-40,0 L-40,${-350} L40,${-350} L40,0" fill="#B48A58" class="st" stroke-width="7"/>`;
  for(let i=1;i<9;i++) s+=`<path d="M-40,${-i*39} l80,0" stroke="#2A3B3A" stroke-width="5"/>`;
  s+=eyes(-170,-100,-130,20)+`<path d="M-160,-80 q25,18 50,0" fill="none" stroke="#2A3B3A" stroke-width="7" stroke-linecap="round"/>`;
  return s; }
// coala com carinha (centro da cabeça em 0,0)
function coala(){ return `<circle cx="-170" cy="-120" r="110" fill="#9AA19E" class="st"/><circle cx="-170" cy="-120" r="60" fill="#E3E9E5"/>
  <circle cx="170" cy="-120" r="110" fill="#9AA19E" class="st"/><circle cx="170" cy="-120" r="60" fill="#E3E9E5"/>
  <ellipse rx="230" ry="200" fill="#B4BAB7" class="st"/>
  ${eyes(-85,85,-30,24)}
  <ellipse cx="0" cy="50" rx="60" ry="80" fill="#2A3B3A"/><ellipse cx="-18" cy="20" rx="14" ry="20" fill="#fff" opacity=".35"/>
  <path d="M-30,150 q30,20 60,0" fill="none" stroke="#2A3B3A" stroke-width="8" stroke-linecap="round"/>
  <ellipse cx="-150" cy="70" rx="28" ry="14" fill="#C8695A" opacity=".3"/><ellipse cx="150" cy="70" rx="28" ry="14" fill="#C8695A" opacity=".3"/>`; }
// impressão digital (espirais), centro 0,0
function digital(o={}){ const col=o.col||'#2A3B3A'; let s=''; for(let i=1;i<9;i++){ const r=i*22; s+=`<path d="M${-r},10 C${-r},${-r*1.3} ${r},${-r*1.3} ${r},10 C${r},${r*0.9} ${-r*0.4},${r} ${-r*0.6},${r*0.6}" fill="none" stroke="${col}" stroke-width="7" stroke-linecap="round"/>`; } return s; }
// ilha da cidade no lago (Tenochtitlan), centro 0,0
function ilha(){ let casas=''; [[-150,-20],[-70,-40],[20,-30],[110,-25],[-110,30],[-20,25],[80,30]].forEach(([x,y])=>{ casas+=`<rect x="${x-30}" y="${y-40}" width="60" height="50" fill="#F3EFE7" class="st" stroke-width="5"/><path d="M${x-34},${y-40} L${x},${y-70} L${x+34},${y-40}Z" fill="#C8695A" class="st" stroke-width="5"/>`; });
  return `<ellipse rx="420" ry="230" fill="#BFD6D6" class="st"/>
   <path d="M-360,-120 q30,-12 60,0 M250,140 q30,-12 60,0 M-300,150 q30,-12 60,0 M300,-130 q30,-12 60,0" fill="none" stroke="#4F8079" stroke-width="7" stroke-linecap="round"/>
   <ellipse cx="0" cy="10" rx="250" ry="120" fill="#C9A66B" class="st"/>
   <path d="M250,10 L410,10" stroke="#B48A58" stroke-width="22"/><path d="M250,10 L410,10" stroke="#2A3B3A" stroke-width="4" stroke-dasharray="14 10"/>
   ${casas}<g transform="translate(0,-60) scale(.28)">${templo()}</g>`; }
document.querySelectorAll('svg [data-d]').forEach(g=>{ const f=g.dataset.d; const o=g.dataset.o?JSON.parse(g.dataset.o):{}; g.innerHTML=window[f](o); });
