// Simule un élève sur plusieurs jours pour vérifier le moteur de révision (aucune dépendance).
const fs=require('fs'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../src/tables-en-tete.src.html'),'utf8');
const eng=src.split('/*ENGINE_START*/')[1].split('/*ENGINE_END*/')[0];
const TE=new Function(eng+';return TE;')();
let seed=42;const rnd=()=>(seed=(seed*1103515245+12345)%2147483648)/2147483648;
const S=TE.defaults();
// élève : connaît bien les tables 2, 5, 10 ; mal 6, 7, 8 ; moyen le reste
const know={};for(const k of TE.factKeys(S)){const[a,b]=TE.parseF(k);const hard=[6,7,8].includes(a)||[6,7,8].includes(b);const easy=[2,5,10].includes(a)||[2,5,10].includes(b);know[k]=easy?.95:hard?.25:.6}
const prodKnow=p=>Math.min(...TE.sols(S,p).map(([a,b])=>know['f'+a+'x'+b]))*.9;
let T=20000,errors=0;
for(let day=0;day<10;day++,T++){
 const s=TE.newSession(S,null);const counts={};let guard=0,rev=0;
 while(!TE.finished(s)){
  if(++guard>200){errors++;console.log('BOUCLE INFINIE');break}
  const k=TE.pick(S,s,T,rnd);s.last=k;counts[k]=(counts[k]||0)+1;if(k[0]==='r')rev++;
  const pk=k[0]==='f'?know[k]:prodKnow(+k.slice(1));
  let out,t;
  if(rnd()<pk){out='ok';t=pk>.8?2+rnd()*2:4+rnd()*8}else if(rnd()<.4){out='ok2';t=9}else{out='fail';t=0}
  TE.grade(S,s,k,out,t,T);
  if(k[0]==='f'&&out!=='ok')know[k]=Math.min(.97,know[k]+.12); else if(k[0]==='f')know[k]=Math.min(.97,know[k]+.04);
 }
 const rep=Object.entries(counts).filter(([,n])=>n>1).map(([k,n])=>k+'×'+n);
 const lv=[0,0,0,0,0,0,0,0];for(const k of TE.factKeys(S)){const l=TE.peek(S,k).l;lv[l+1]++}
 console.log(`J${day+1} : ${s.i} questions, ${s.firstOk} justes du 1er coup, à l’envers ${rev}, répétées [${rep.join(' ')}]`);
 console.log(`     niveaux (nouv,0..6) ${lv.join(' ')}  XP ${S.xp}  niveau ${TE.levelOf(S.xp)}  badges ${S.badges.join(',')}`);
}
// focus sur la table de 7
const s=TE.newSession(S,7);while(!TE.finished(s)){const k=TE.pick(S,s,T,rnd);s.last=k;if(!k.includes('7'))errors++;TE.grade(S,s,k,'ok',3,T)}
console.log('Séance table de 7 :',s.i,'questions, hors table :',errors);
console.log('Indices :',[[7,8],[6,9],[5,7],[2,8],[3,10],[7,7]].map(([a,b])=>TE.hint(a,b)).join(' | '));
if(errors)process.exit(1);

// ---------- Cash, carré, duo ----------
{
 let bad=0;const S2=TE.defaults();S2.settings.mode='mix';
 for(const k of [...TE.factKeys(S2),...TE.revKeys(S2)]){
  for(let r=0;r<20;r++){
   const o=TE.choices(S2,k,rnd);
   const labels=new Set(o.map(x=>x.label));
   if(o.length!==4||labels.size!==4||o.filter(x=>x.ok).length!==1){bad++;console.log('CHOIX INVALIDES',k,o);break}
   if(k[0]==='r'){const p=+k.slice(1);for(const x of o){const[a,b]=x.label.split(' × ').map(Number);if((a*b===p)!==x.ok){bad++;console.log('CHOIX INVERSÉ FAUX',k,o)}}}
   const d=TE.duoOf(o,o.find(x=>!x.ok),rnd);if(d.length!==2||d.filter(x=>x.ok).length!==1)bad++;
  }
 }
 // carré et duo justes : ni niveau ni date ne bougent ; une erreur fait baisser d’un niveau
 const s=TE.newSession(S2,null,'calm');const k='f7x8';const c=TE.card(S2,k);c.l=3;c.due=T+5;
 TE.gradeChoice(S2,s,k,'carre',0,T);TE.gradeChoice(S2,s,k,'duo',0,T);
 if(c.l!==3||c.due!==T+5){bad++;console.log('carré/duo ont modifié la carte',c)}
 TE.gradeChoice(S2,s,k,'miss',0,T);if(c.l!==2||c.due!==T){bad++;console.log('erreur mal comptée',c)}
 TE.gradeChoice(S2,s,'f2x3','cash',2,T);if(TE.peek(S2,'f2x3').l!==3){bad++;console.log('cash ne compte pas comme une vraie réponse')}
 // rythme des défis en mode mixte
 const m=TE.newSession(S2,null,'mix');const turns=[];for(let i=0;i<30;i++){if(TE.ccdTurn(m,rnd))turns.push(i);m.i++}
 const gaps=turns.slice(1).map((x,i)=>x-turns[i]);
 if(turns[0]<4||turns[0]>5||gaps.some(g=>g<5||g>6)){bad++;console.log('rythme des défis',turns)}
 const cl=TE.newSession(S2,null,'classic');for(let i=0;i<20;i++){if(TE.ccdTurn(cl,rnd))bad++;cl.i++}
 console.log('Cash, carré, duo :',bad?bad+' problème(s)':'OK','— défis aux questions',turns.map(x=>x+1).join(', '));
 console.log('Exemple 7 × 8 :',TE.choices(S2,'f7x8',rnd).map(x=>x.label+(x.ok?'✓':'')).join(' | '),'· 24 :',TE.choices(S2,'r24',rnd).map(x=>x.label+(x.ok?'✓':'')).join(' | '));
 if(bad)process.exit(1);
}
