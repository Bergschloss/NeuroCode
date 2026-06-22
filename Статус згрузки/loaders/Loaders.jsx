/* 10 long animated loading-screen variants for Neurocode Studio
   Wide format (~1000×220) — poster monochrome / grey aesthetic */

const bg   = '#a8a8a8';
const ink  = '#000';
const ink2 = '#2a2a2a';
const ink3 = '#5a5a5a';
const ink4 = '#7a7a7a';
const white = '#fff';
const tMono = 'Space Mono, monospace';
const tDisplay = 'Inter, Helvetica, Arial, sans-serif';

/* ============================================================
   Shell: registration corners, top/bottom mono labels, progress
   ============================================================ */

const Shell = ({ idx, name, children, percent = 'auto', stage = 'LOADING' }) => (
  <div style={{
    position:'relative', width:'100%', height:'100%',
    background:bg, color:ink, overflow:'hidden',
    fontFamily:tDisplay,
  }}>
    {/* corner reg marks */}
    {[
      {top:10, left:10,  bt:1, bl:1},
      {top:10, right:10, bt:1, br:1},
      {bottom:10, left:10,  bb:1, bl:1},
      {bottom:10, right:10, bb:1, br:1},
    ].map((s,i)=>(
      <div key={i} style={{
        position:'absolute', width:8, height:8,
        ...(s.top!=null ? {top:s.top}:{}), ...(s.bottom!=null?{bottom:s.bottom}:{}),
        ...(s.left!=null?{left:s.left}:{}), ...(s.right!=null?{right:s.right}:{}),
        borderTop:    s.bt ? `1px solid ${ink}`:'',
        borderBottom: s.bb ? `1px solid ${ink}`:'',
        borderLeft:   s.bl ? `1px solid ${ink}`:'',
        borderRight:  s.br ? `1px solid ${ink}`:'',
      }}/>
    ))}

    {/* top label bar */}
    <div style={{
      position:'absolute', top:16, left:30, right:30,
      display:'flex', justifyContent:'space-between', alignItems:'center',
      fontFamily:tMono, fontSize:10, letterSpacing:'.22em',
      color:ink2, textTransform:'uppercase',
    }}>
      <span>● NEUROCODE STUDIO · NCS-{String(idx).padStart(2,'0')}</span>
      <span style={{color:ink3}}>{name}</span>
    </div>

    {/* central content */}
    <div style={{
      position:'absolute', inset:'46px 30px 46px',
      display:'flex', flexDirection:'column', justifyContent:'center',
    }}>
      {children}
    </div>

    {/* bottom label bar */}
    <div style={{
      position:'absolute', bottom:16, left:30, right:30,
      display:'flex', justifyContent:'space-between', alignItems:'center',
      fontFamily:tMono, fontSize:10, letterSpacing:'.22em',
      color:ink2, textTransform:'uppercase',
    }}>
      <span>{stage} · 48 kHz / Stereo</span>
      <span style={{color:ink, fontWeight:700}}>{idx}/10</span>
    </div>
  </div>
);

/* ============================================================
   10 loader variants
   ============================================================ */

const Loaders = {};

/* 01 — Marble flow */
let _flow = 0;
Loaders.l01 = () => {
  const id = `lfl${_flow++}`;
  const lines = [];
  for (let i = 0; i < 26; i++) lines.push(<path key={i} d={`M-40 ${20 + i * 4.2} L 1100 ${20 + i * 4.2}`}/>);
  return (
    <Shell idx={1} name="LIQUID FLOW" stage="STREAMING">
      <svg viewBox="0 0 1000 120" preserveAspectRatio="none" style={{width:'100%', height:120}}>
        <defs>
          <filter id={id} x="-5%" y="-30%" width="110%" height="160%">
            <feTurbulence type="fractalNoise" baseFrequency="0.006 0.025" numOctaves="2" seed="3">
              <animate attributeName="baseFrequency" dur="22s"
                values="0.006 0.025;0.012 0.04;0.006 0.025" repeatCount="indefinite"/>
            </feTurbulence>
            <feDisplacementMap in="SourceGraphic" scale="40"/>
          </filter>
        </defs>
        <g filter={`url(#${id})`} stroke={ink} strokeWidth=".6" fill="none">{lines}</g>
      </svg>
    </Shell>
  );
};

/* 02 — Goo blob assembling */
let _goo = 0;
Loaders.l02 = () => {
  const id = `gid${_goo++}`;
  const N = 9;
  const blobs = [];
  for (let i = 0; i < N; i++) {
    const t = (i/N) * Math.PI*2;
    const r = 36 + (i%3)*8;
    const cx = 500 + Math.cos(t)*120;
    const cy = 60 + Math.sin(t)*30;
    const cx2 = 500 + Math.cos(t+1)*40;
    const cy2 = 60 + Math.sin(t+1)*10;
    const dur = 5 + (i%4);
    blobs.push(
      <circle key={i} cx={cx} cy={cy} r={r} fill={ink}>
        <animate attributeName="cx" values={`${cx};${cx2};${cx}`} dur={dur+'s'} repeatCount="indefinite"/>
        <animate attributeName="cy" values={`${cy};${cy2};${cy}`} dur={(dur+1)+'s'} repeatCount="indefinite"/>
      </circle>
    );
  }
  return (
    <Shell idx={2} name="MASS · GOO" stage="MERGING">
      <svg viewBox="0 0 1000 120" preserveAspectRatio="xMidYMid meet" style={{width:'100%', height:120}}>
        <defs>
          <filter id={id} x="-5%" y="-20%" width="110%" height="140%">
            <feGaussianBlur stdDeviation="10"/>
            <feColorMatrix values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 24 -10"/>
          </filter>
        </defs>
        <g filter={`url(#${id})`}>{blobs}</g>
      </svg>
    </Shell>
  );
};

/* 03 — Frequency analyzer bars */
Loaders.l03 = () => {
  const N = 64;
  const bars = [];
  for (let i = 0; i < N; i++) {
    const x = 30 + i * (940/N);
    const w = 940/N - 4;
    // baseline height varies; animate
    const peak = 8 + Math.abs(Math.sin(i*0.3))*60 + Math.random()*20;
    bars.push(
      <rect key={i} x={x} y={70} width={w} height={6} fill={ink}>
        <animate attributeName="height" values={`6;${peak};${peak*.5};${peak*1.1};6`}
          dur={(1.2 + (i%5)*.2) + 's'} repeatCount="indefinite"/>
        <animate attributeName="y" values={`70;${70-peak};${70-peak*.5};${70-peak*1.1};70`}
          dur={(1.2 + (i%5)*.2) + 's'} repeatCount="indefinite"/>
      </rect>
    );
  }
  return (
    <Shell idx={3} name="ANALYZER · FFT" stage="SCANNING">
      <svg viewBox="0 0 1000 100" style={{width:'100%', height:100}}>
        <line x1="20" y1="76" x2="980" y2="76" stroke={ink} strokeWidth=".5" opacity=".5"/>
        {bars}
      </svg>
    </Shell>
  );
};

/* 04 — Self-drawing wave with percent */
Loaders.l04 = () => {
  const d = "M20 60 Q40 20 80 60 T 160 60 T 240 60 T 320 60 T 400 60 T 480 60 T 560 60 T 640 60 T 720 60 T 800 60 T 880 60 T 960 60";
  return (
    <Shell idx={4} name="WAVEFORM · DRAW" stage="ENCODING">
      <svg viewBox="0 0 1000 120" style={{width:'100%', height:120}}>
        <line x1="20" y1="60" x2="980" y2="60" stroke={ink2} strokeWidth=".5" opacity=".4"/>
        <path d={d} stroke={ink} strokeWidth="1.6" fill="none" strokeLinecap="round"
          strokeDasharray="1800" strokeDashoffset="1800">
          <animate attributeName="stroke-dashoffset" values="1800;0;-1800"
            dur="6s" repeatCount="indefinite"/>
        </path>
        <path d={d} stroke={ink} strokeWidth=".7" fill="none" opacity=".5"
          strokeDasharray="1800" strokeDashoffset="-1800">
          <animate attributeName="stroke-dashoffset" values="-1800;0;1800"
            dur="6s" repeatCount="indefinite"/>
        </path>
      </svg>
    </Shell>
  );
};

/* 05 — Dot grid pulse sweep */
Loaders.l05 = () => {
  const cols = 60, rows = 5;
  const dots = [];
  const w = 940/cols;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const x = 30 + c*w;
      const y = 30 + r*16;
      const delay = c * 0.05;
      dots.push(
        <circle key={`${r}-${c}`} cx={x} cy={y} r="1.5" fill={ink}>
          <animate attributeName="r" values="1.2;3.5;1.2" dur="2.4s"
            begin={delay + 's'} repeatCount="indefinite"/>
          <animate attributeName="opacity" values=".3;1;.3" dur="2.4s"
            begin={delay + 's'} repeatCount="indefinite"/>
        </circle>
      );
    }
  }
  return (
    <Shell idx={5} name="GRID · SWEEP" stage="MAPPING">
      <svg viewBox="0 0 1000 100" style={{width:'100%', height:100}}>{dots}</svg>
    </Shell>
  );
};

/* 06 — Radial spinner with tick scale */
Loaders.l06 = () => {
  const ticks = [];
  for (let i = 0; i < 24; i++) {
    const major = i % 6 === 0;
    ticks.push(
      <line key={i} x1="60" y1={major?16:22} x2="60" y2="28"
        stroke={ink} strokeWidth={major?1.4:.6}
        transform={`rotate(${i*15} 60 60)`}/>
    );
  }
  return (
    <Shell idx={6} name="ROTOR · 24" stage="ALIGNING">
      <div style={{display:'flex', alignItems:'center', gap:32}}>
        <svg viewBox="0 0 120 120" width="100" height="100">
          <circle cx="60" cy="60" r="50" fill="none" stroke={ink} strokeWidth=".5" opacity=".3"/>
          <g>{ticks}<animateTransform attributeName="transform" type="rotate"
            from="0 60 60" to="360 60 60" dur="48s" repeatCount="indefinite"/></g>
          <line x1="60" y1="60" x2="60" y2="20" stroke={ink} strokeWidth="1.6">
            <animateTransform attributeName="transform" type="rotate"
              from="0 60 60" to="360 60 60" dur="2.6s" repeatCount="indefinite"/>
          </line>
          <circle cx="60" cy="60" r="3" fill={ink}/>
        </svg>
        <div>
          <div style={{fontFamily:tDisplay, fontWeight:900, fontSize:42,
            letterSpacing:'-.04em', color:ink, lineHeight:.9, textTransform:'uppercase'}}>Loading</div>
          <div style={{fontFamily:tMono, fontSize:10, letterSpacing:'.28em',
            color:ink2, textTransform:'uppercase', marginTop:6}}>·· encoder · standby ··</div>
        </div>
      </div>
    </Shell>
  );
};

/* 07 — Typewriter NEUROCODE STUDIO appearing */
Loaders.l07 = () => {
  const text = 'NEUROCODE \u00B7 STUDIO \u00B7 ENGINE \u00B7 2026';
  return (
    <Shell idx={7} name="STREAM · TYPE" stage="TRANSMITTING">
      <div style={{display:'flex', flexDirection:'column', gap:14}}>
        <div style={{fontFamily:tMono, fontSize:10, letterSpacing:'.28em', color:ink3, textTransform:'uppercase'}}>
          <span>$ ncs --init --48k --stereo</span>
        </div>
        <div style={{
          fontFamily:tDisplay, fontWeight:800, fontSize:54, letterSpacing:'-.025em',
          color:ink, textTransform:'uppercase', lineHeight:1,
          whiteSpace:'nowrap', overflow:'hidden', borderRight:`3px solid ${ink}`,
          width:'fit-content', maxWidth:'100%',
          animation: 'typing 7s steps(40, end) infinite, caret .6s step-end infinite',
        }}>
          {text}
        </div>
        <style>{`
          @keyframes typing { 0%{width:0} 60%{width:100%} 100%{width:100%} }
          @keyframes caret { 50%{border-color:transparent} }
        `}</style>
      </div>
    </Shell>
  );
};

/* 08 — Swiss progress bar with stage timeline */
Loaders.l08 = () => (
  <Shell idx={8} name="PROGRESS · TIMELINE" stage="PROCESSING">
    <div style={{display:'flex', flexDirection:'column', gap:14}}>
      <div style={{display:'flex', justifyContent:'space-between', fontFamily:tMono,
        fontSize:9, letterSpacing:'.2em', color:ink2, textTransform:'uppercase'}}>
        <span>tts</span><span>am encoding</span><span>binaural</span><span>music bed</span><span>normalize</span>
      </div>
      <div style={{position:'relative', height:2, background:ink4}}>
        <div style={{position:'absolute', top:0, left:0, height:2, background:ink, width:'0%',
          animation:'sweep 4s linear infinite'}}/>
        <style>{`@keyframes sweep{from{width:0}to{width:100%}}`}</style>
        {[0,25,50,75,100].map((p,i)=>(
          <span key={i} style={{position:'absolute', left:`${p}%`, top:-3, width:1, height:8,
            background:ink, transform:'translateX(-.5px)'}}/>
        ))}
      </div>
      <div style={{display:'flex', justifyContent:'space-between', fontFamily:tMono,
        fontSize:9, letterSpacing:'.2em', color:ink3, textTransform:'uppercase'}}>
        <span>00</span><span>25</span><span>50</span><span>75</span><span>100</span>
      </div>
      <div style={{fontFamily:tDisplay, fontWeight:800, fontSize:34, color:ink,
        letterSpacing:'-.02em', textTransform:'uppercase', marginTop:4}}>
        Building affirmation chain<span style={{color:ink3}}>...</span>
      </div>
    </div>
  </Shell>
);

/* 09 — Expanding concentric rings + percent number */
Loaders.l09 = () => (
  <Shell idx={9} name="RINGS · EXPAND" stage="TUNING">
    <div style={{display:'flex', alignItems:'center', gap:36}}>
      <svg viewBox="0 0 140 140" width="120" height="120">
        {[10, 20, 30, 40, 50, 60].map((r,i)=>(
          <circle key={i} cx="70" cy="70" r={r} fill="none" stroke={ink} strokeWidth="1">
            <animate attributeName="r" values={`${r-6};${r+10};${r-6}`}
              dur={(3+i*.4)+'s'} repeatCount="indefinite"/>
            <animate attributeName="opacity" values=".9;.1;.9"
              dur={(3+i*.4)+'s'} repeatCount="indefinite"/>
          </circle>
        ))}
        <circle cx="70" cy="70" r="3" fill={ink}/>
      </svg>
      <div>
        <div style={{fontFamily:tMono, fontSize:10, letterSpacing:'.3em', color:ink3, textTransform:'uppercase'}}>frequency · alpha</div>
        <div style={{fontFamily:tDisplay, fontWeight:900, fontSize:48,
          letterSpacing:'-.04em', color:ink, lineHeight:.9}}>
          10.000<span style={{color:ink3, fontWeight:300}}>Hz</span>
        </div>
        <div style={{fontFamily:tMono, fontSize:10, letterSpacing:'.22em', color:ink2,
          textTransform:'uppercase', marginTop:6}}>·· binaural carrier active ··</div>
      </div>
    </div>
  </Shell>
);

/* 10 — Compass needle + horizontal fill bar */
Loaders.l10 = () => (
  <Shell idx={10} name="COMPASS · SYNC" stage="LOCKING">
    <div style={{display:'flex', alignItems:'center', gap:36}}>
      <svg viewBox="0 0 120 120" width="100" height="100">
        <circle cx="60" cy="60" r="52" fill="none" stroke={ink} strokeWidth=".5" opacity=".4"/>
        {['N','E','S','W'].map((d,i)=>{
          const a = (i*90 - 90) * Math.PI / 180;
          return <text key={i} x={60+Math.cos(a)*60} y={60+Math.sin(a)*60+3}
            fontFamily={tMono} fontSize="8" fill={ink} textAnchor="middle" letterSpacing="1">{d}</text>;
        })}
        <g>
          <polygon points="60,18 64,60 56,60" fill={ink}/>
          <polygon points="60,102 64,60 56,60" fill="none" stroke={ink} strokeWidth=".7"/>
          <animateTransform attributeName="transform" type="rotate"
            from="0 60 60" to="360 60 60" dur="8s" repeatCount="indefinite"/>
        </g>
        <circle cx="60" cy="60" r="3" fill={bg} stroke={ink} strokeWidth=".7"/>
      </svg>
      <div style={{flex:1}}>
        <div style={{display:'flex', justifyContent:'space-between', fontFamily:tMono,
          fontSize:10, letterSpacing:'.2em', color:ink2, textTransform:'uppercase', marginBottom:8}}>
          <span>aligning · channel L/R</span>
          <span>tracking</span>
        </div>
        <div style={{position:'relative', height:2, background:ink4}}>
          <div style={{position:'absolute', height:2, background:ink, width:'30%',
            animation:'roam 3.6s ease-in-out infinite'}}/>
          <style>{`@keyframes roam{0%{left:0;width:8%}50%{left:30%;width:46%}100%{left:92%;width:8%}}`}</style>
        </div>
        <div style={{fontFamily:tDisplay, fontWeight:800, fontSize:30, color:ink,
          letterSpacing:'-.02em', textTransform:'uppercase', marginTop:10, lineHeight:1}}>
          Locking phase · L↔R
        </div>
      </div>
    </div>
  </Shell>
);

/* ===== Compose variants ===== */
const VARIANTS = [
  {n:1,  key:'l01', name:'Liquid · flow'},
  {n:2,  key:'l02', name:'Mass · goo'},
  {n:3,  key:'l03', name:'Analyzer · FFT'},
  {n:4,  key:'l04', name:'Waveform · draw'},
  {n:5,  key:'l05', name:'Grid · sweep'},
  {n:6,  key:'l06', name:'Rotor · 24'},
  {n:7,  key:'l07', name:'Stream · type'},
  {n:8,  key:'l08', name:'Progress · timeline'},
  {n:9,  key:'l09', name:'Rings · expand'},
  {n:10, key:'l10', name:'Compass · sync'},
];

window.LoaderVariants = VARIANTS;
window.LoaderComponents = Loaders;
