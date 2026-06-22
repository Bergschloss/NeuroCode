/* global React */
/* 20 abstract animated symbol marks for Neurocode Studio — editorial monochrome.
   Each variant is a pure SVG symbol (no wordmark) with SMIL or CSS animation. */

const ink  = '#fff';
const ink2 = '#bdbdbd';
const ink3 = '#7a7a7a';
const ink4 = '#3a3a3a';
const rule = '#222';
const tMono = 'Space Mono, monospace';

/* ===== Plate wrapper ===== */
const Plate = ({ idx, label, children }) => (
  <div style={{
    width:'100%', height:'100%', background:'#000', color:'#fff',
    position:'relative', overflow:'hidden',
    display:'flex', alignItems:'center', justifyContent:'center',
    fontFamily:'Inter, sans-serif',
  }}>
    <Corners/>
    <div style={{position:'absolute', top:12, right:14,
      fontFamily:tMono, fontSize:8, letterSpacing:'.3em',
      color:ink3, textTransform:'uppercase'}}>{String(idx).padStart(2,'0')} / 20</div>
    <div style={{position:'absolute', bottom:12, left:14,
      fontFamily:tMono, fontSize:8, letterSpacing:'.28em',
      color:ink2, textTransform:'uppercase'}}>● {label}</div>
    <div style={{width:170, height:170, display:'flex',
      alignItems:'center', justifyContent:'center'}}>
      {children}
    </div>
  </div>
);

const Corners = () => {
  const base = {position:'absolute', width:9, height:9};
  return (
    <>
      <div style={{...base, top:8, left:8, borderTop:`1px solid ${ink}`, borderLeft:`1px solid ${ink}`}}/>
      <div style={{...base, top:8, right:8, borderTop:`1px solid ${ink}`, borderRight:`1px solid ${ink}`}}/>
      <div style={{...base, bottom:8, left:8, borderBottom:`1px solid ${ink}`, borderLeft:`1px solid ${ink}`}}/>
      <div style={{...base, bottom:8, right:8, borderBottom:`1px solid ${ink}`, borderRight:`1px solid ${ink}`}}/>
    </>
  );
};

/* ===== 20 abstract symbols ===== */

const Sym = {};

/* 01 — Liquid marble droplet: horizontal lines warped by turbulence */
let _lid = 0;
Sym.s01 = () => {
  const id = `lq${_lid++}`;
  const lines = [];
  for (let i = 0; i < 32; i++) lines.push(<path key={i} d={`M-20 ${10+i*5} L 180 ${10+i*5}`}/>);
  return (
    <svg viewBox="0 0 170 170">
      <defs>
        <filter id={id} x="-30%" y="-30%" width="160%" height="160%">
          <feTurbulence type="fractalNoise" baseFrequency="0.012 0.04" numOctaves="2" seed="6">
            <animate attributeName="baseFrequency" dur="14s" values="0.012 0.04;0.018 0.06;0.012 0.04" repeatCount="indefinite"/>
          </feTurbulence>
          <feDisplacementMap in="SourceGraphic" scale="40"/>
        </filter>
        <clipPath id={`${id}c`}>
          <circle cx="85" cy="85" r="78"/>
        </clipPath>
      </defs>
      <g clipPath={`url(#${id}c)`}>
        <g filter={`url(#${id})`} stroke={ink} strokeWidth=".7" fill="none">{lines}</g>
      </g>
      <circle cx="85" cy="85" r="78" fill="none" stroke={ink} strokeWidth=".5" opacity=".4"/>
    </svg>
  );
};

/* 02 — Pulsing concentric rings */
Sym.s02 = () => (
  <svg viewBox="0 0 170 170">
    {[20, 38, 56, 74].map((r, i) => (
      <circle key={i} cx="85" cy="85" r={r} fill="none" stroke={ink} strokeWidth=".8" opacity=".7">
        <animate attributeName="r" values={`${r};${r+8};${r}`} dur={`${4+i*.5}s`} repeatCount="indefinite"/>
        <animate attributeName="opacity" values=".9;.2;.9" dur={`${4+i*.5}s`} repeatCount="indefinite"/>
      </circle>
    ))}
    <circle cx="85" cy="85" r="2.5" fill={ink}/>
  </svg>
);

/* 03 — Crosshair: rotating outer ring + fixed cross */
Sym.s03 = () => (
  <svg viewBox="0 0 170 170">
    <g transform="translate(85 85)">
      <circle r="74" fill="none" stroke={ink} strokeWidth=".6" strokeDasharray="3 6">
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="36s" repeatCount="indefinite"/>
      </circle>
      <circle r="56" fill="none" stroke={ink} strokeWidth=".8"/>
      <line x1="-74" y1="0" x2="-30" y2="0" stroke={ink} strokeWidth="1"/>
      <line x1="30" y1="0" x2="74" y2="0" stroke={ink} strokeWidth="1"/>
      <line x1="0" y1="-74" x2="0" y2="-30" stroke={ink} strokeWidth="1"/>
      <line x1="0" y1="30" x2="0" y2="74" stroke={ink} strokeWidth="1"/>
      <circle r="6" fill="none" stroke={ink} strokeWidth="1.2"/>
      <circle r="1.5" fill={ink}/>
    </g>
  </svg>
);

/* 04 — Frequency response that breathes between peaks/notch */
Sym.s04 = () => (
  <svg viewBox="0 0 170 170">
    <line x1="10" y1="120" x2="160" y2="120" stroke={ink} strokeWidth=".6" opacity=".4"/>
    {[20,40,60,85,110,130,150].map((x,i)=>(
      <line key={i} x1={x} y1="120" x2={x} y2="126" stroke={ink} strokeWidth=".5" opacity=".5"/>
    ))}
    <path fill="none" stroke={ink} strokeWidth="1.4" strokeLinecap="round">
      <animate attributeName="d" dur="6s" repeatCount="indefinite"
        values="
          M10 85 Q40 65 60 65 Q80 65 85 75 L85 110 L85 75 Q90 65 110 65 Q150 65 160 85;
          M10 85 Q40 50 60 50 Q80 50 85 60 L85 115 L85 60 Q90 50 110 50 Q150 50 160 85;
          M10 85 Q40 65 60 65 Q80 65 85 75 L85 110 L85 75 Q90 65 110 65 Q150 65 160 85"/>
    </path>
    <line x1="85" y1="30" x2="85" y2="55" stroke={ink} strokeWidth=".8"/>
    <circle cx="85" cy="28" r="2.5" fill={ink}/>
  </svg>
);

/* 05 — Notch carve: sine wave with notch growing in/out */
Sym.s05 = () => (
  <svg viewBox="0 0 170 170">
    <g stroke={ink} fill="none">
      <path strokeWidth="1.2" d="M10 85 Q30 50 50 85 T 90 85 T 130 85 T 160 85"/>
      <g>
        <rect x="80" y="40" width="10" height="90" fill="#000"/>
        <line x1="85" y1="40" x2="85" y2="130" strokeWidth=".7" opacity=".7" strokeDasharray="2 3"/>
        <animateTransform attributeName="transform" type="scale" values="1 .3;1 1.2;1 .3" dur="5s" repeatCount="indefinite" additive="sum"/>
      </g>
    </g>
  </svg>
);

/* 06 — Rotating hairline arc with center dot */
Sym.s06 = () => (
  <svg viewBox="0 0 170 170">
    <g transform="translate(85 85)">
      <circle r="68" fill="none" stroke={ink} strokeWidth=".4" opacity=".4"/>
      <g>
        <path d="M 0 -68 A 68 68 0 0 1 48 -48" fill="none" stroke={ink} strokeWidth="2" strokeLinecap="round"/>
        <circle cx="0" cy="-68" r="3" fill={ink}/>
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="9s" repeatCount="indefinite"/>
      </g>
      <g opacity=".5">
        <path d="M 0 -50 A 50 50 0 0 1 35 -35" fill="none" stroke={ink} strokeWidth="1.2"/>
        <animateTransform attributeName="transform" type="rotate" from="180" to="-180" dur="13s" repeatCount="indefinite"/>
      </g>
      <circle r="3" fill={ink}/>
    </g>
  </svg>
);

/* 07 — Constellation: dots with lines fading in sequence */
Sym.s07 = () => {
  const pts = [[40,30],[120,40],[30,80],[85,70],[140,90],[50,130],[110,130]];
  const lines = [[0,3],[1,3],[2,3],[3,4],[3,5],[3,6]];
  return (
    <svg viewBox="0 0 170 170">
      <g stroke={ink} strokeWidth=".7" fill={ink}>
        {lines.map((l,i)=>{
          const [a,b]=l;
          return (
            <line key={i} x1={pts[a][0]} y1={pts[a][1]} x2={pts[b][0]} y2={pts[b][1]} opacity=".4">
              <animate attributeName="opacity" values=".15;.9;.15" dur="3s" begin={`${i*.4}s`} repeatCount="indefinite"/>
            </line>
          );
        })}
        {pts.map(([x,y],i)=>(
          <circle key={i} cx={x} cy={y} r={i===3?3:2}>
            <animate attributeName="r" values={`${i===3?3:2};${i===3?5:3.4};${i===3?3:2}`} dur="3s" begin={`${i*.3}s`} repeatCount="indefinite"/>
          </circle>
        ))}
      </g>
    </svg>
  );
};

/* 08 — Scan line over horizontal hatching */
Sym.s08 = () => (
  <svg viewBox="0 0 170 170">
    <g stroke={ink} strokeWidth=".5">
      {Array.from({length:18}, (_,i)=>(
        <line key={i} x1="15" y1={20+i*8} x2="155" y2={20+i*8} opacity=".4"/>
      ))}
    </g>
    <line x1="15" y1="20" x2="15" y2="156" stroke={ink} strokeWidth="1.4">
      <animate attributeName="x1" values="15;155;15" dur="4s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="15;155;15" dur="4s" repeatCount="indefinite"/>
    </line>
    <rect x="15" y="14" width="140" height="148" fill="none" stroke={ink} strokeWidth=".7"/>
  </svg>
);

/* 09 — Three dots rotating around center (NCS) */
Sym.s09 = () => (
  <svg viewBox="0 0 170 170">
    <g transform="translate(85 85)">
      <circle r="60" fill="none" stroke={ink} strokeWidth=".4" opacity=".3"/>
      <g>
        <circle cx="0" cy="-50" r="6" fill={ink}/>
        <circle cx="43.3" cy="25" r="6" fill={ink}/>
        <circle cx="-43.3" cy="25" r="6" fill={ink}/>
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="14s" repeatCount="indefinite"/>
      </g>
      <g opacity=".55">
        <circle cx="0" cy="-30" r="2.5" fill={ink}/>
        <circle cx="26" cy="15" r="2.5" fill={ink}/>
        <circle cx="-26" cy="15" r="2.5" fill={ink}/>
        <animateTransform attributeName="transform" type="rotate" from="360" to="0" dur="20s" repeatCount="indefinite"/>
      </g>
    </g>
  </svg>
);

/* 10 — Hexagon morphing into circle (radius pulse) */
Sym.s10 = () => (
  <svg viewBox="0 0 170 170">
    <g transform="translate(85 85)" fill="none" stroke={ink} strokeWidth="1.1">
      <polygon points="0,-60 52,-30 52,30 0,60 -52,30 -52,-30">
        <animateTransform attributeName="transform" type="rotate" from="0" to="60" dur="11s" repeatCount="indefinite"/>
        <animate attributeName="opacity" values="1;.5;1" dur="5s" repeatCount="indefinite"/>
      </polygon>
      <polygon points="0,-40 35,-20 35,20 0,40 -35,20 -35,-20" opacity=".5">
        <animateTransform attributeName="transform" type="rotate" from="60" to="0" dur="13s" repeatCount="indefinite"/>
      </polygon>
      <circle r="3" fill={ink} stroke="none"/>
    </g>
  </svg>
);

/* 11 — Pulse grid: 5x5 dots, wave amplitude */
Sym.s11 = () => {
  const grid = [];
  for (let r=0;r<5;r++) for (let c=0;c<5;c++) {
    const x = 30 + c*28, y = 30 + r*28;
    const delay = (r+c)*.15;
    grid.push(
      <circle key={`${r}-${c}`} cx={x} cy={y} r="2" fill={ink}>
        <animate attributeName="r" values="1;4;1" dur="2.5s" begin={`${delay}s`} repeatCount="indefinite"/>
        <animate attributeName="opacity" values=".3;1;.3" dur="2.5s" begin={`${delay}s`} repeatCount="indefinite"/>
      </circle>
    );
  }
  return <svg viewBox="0 0 170 170">{grid}</svg>;
};

/* 12 — Spiral, slowly rotating */
Sym.s12 = () => {
  let d = 'M 85 85';
  for (let t = 0; t < 8 * Math.PI; t += 0.08) {
    const r = 1.5 * t;
    d += ` L ${85 + r * Math.cos(t)} ${85 + r * Math.sin(t)}`;
  }
  return (
    <svg viewBox="0 0 170 170">
      <g transform="translate(85 85)">
        <g transform="translate(-85 -85)">
          <path d={d} fill="none" stroke={ink} strokeWidth=".8">
            <animateTransform attributeName="transform" type="rotate" from="0 85 85" to="360 85 85" dur="22s" repeatCount="indefinite"/>
          </path>
        </g>
      </g>
    </svg>
  );
};

/* 13 — Rotating radial tick marks (clock face) */
Sym.s13 = () => {
  const ticks = [];
  for (let i = 0; i < 36; i++) {
    const major = i % 9 === 0;
    ticks.push(
      <line key={i} x1="85" y1="20" x2="85" y2={major ? 36 : 28}
        stroke={ink} strokeWidth={major ? 1.4 : .6}
        transform={`rotate(${i*10} 85 85)`}/>
    );
  }
  return (
    <svg viewBox="0 0 170 170">
      <circle cx="85" cy="85" r="65" fill="none" stroke={ink} strokeWidth=".5" opacity=".3"/>
      <g>
        {ticks}
        <animateTransform attributeName="transform" type="rotate" from="0 85 85" to="360 85 85" dur="60s" repeatCount="indefinite"/>
      </g>
      <line x1="85" y1="85" x2="85" y2="30" stroke={ink} strokeWidth="1.4">
        <animateTransform attributeName="transform" type="rotate" from="0 85 85" to="360 85 85" dur="7s" repeatCount="indefinite"/>
      </line>
      <circle cx="85" cy="85" r="3" fill={ink}/>
    </svg>
  );
};

/* 14 — Triangle outline with internal vertical scanning */
Sym.s14 = () => (
  <svg viewBox="0 0 170 170">
    <defs>
      <clipPath id="triClip"><polygon points="85,18 152,140 18,140"/></clipPath>
    </defs>
    <polygon points="85,18 152,140 18,140" fill="none" stroke={ink} strokeWidth="1.2"/>
    <g clipPath="url(#triClip)" stroke={ink} strokeWidth=".6">
      {Array.from({length:14},(_,i)=>(
        <line key={i} x1="0" y1={32+i*8} x2="170" y2={32+i*8} opacity=".5"/>
      ))}
    </g>
    <line x1="85" y1="14" x2="85" y2="146" stroke={ink} strokeWidth=".5" opacity=".4"/>
    <line x1="85" y1="18" x2="85" y2="140" stroke={ink} strokeWidth="1.4">
      <animate attributeName="x1" values="40;130;40" dur="5s" repeatCount="indefinite"/>
      <animate attributeName="x2" values="40;130;40" dur="5s" repeatCount="indefinite"/>
    </line>
  </svg>
);

/* 15 — Two intersecting circles (Venn) with pulsing intersection */
Sym.s15 = () => (
  <svg viewBox="0 0 170 170">
    <g fill="none" stroke={ink} strokeWidth="1.1">
      <circle cx="65" cy="85" r="50">
        <animate attributeName="cx" values="65;72;65" dur="6s" repeatCount="indefinite"/>
      </circle>
      <circle cx="105" cy="85" r="50">
        <animate attributeName="cx" values="105;98;105" dur="6s" repeatCount="indefinite"/>
      </circle>
    </g>
    <ellipse cx="85" cy="85" rx="14" ry="44" fill={ink} opacity=".15">
      <animate attributeName="rx" values="6;18;6" dur="6s" repeatCount="indefinite"/>
    </ellipse>
    <line x1="85" y1="35" x2="85" y2="135" stroke={ink} strokeWidth=".4" strokeDasharray="2 3" opacity=".5"/>
  </svg>
);

/* 16 — Square with rotating diagonals */
Sym.s16 = () => (
  <svg viewBox="0 0 170 170">
    <rect x="25" y="25" width="120" height="120" fill="none" stroke={ink} strokeWidth=".7" opacity=".4"/>
    <g transform="translate(85 85)" stroke={ink} strokeWidth="1.1" fill="none">
      <g>
        <line x1="-60" y1="0" x2="60" y2="0"/>
        <line x1="0" y1="-60" x2="0" y2="60"/>
        <animateTransform attributeName="transform" type="rotate" from="0" to="45" dur="6s" repeatCount="indefinite"/>
      </g>
      <g opacity=".5">
        <line x1="-60" y1="0" x2="60" y2="0"/>
        <line x1="0" y1="-60" x2="0" y2="60"/>
        <animateTransform attributeName="transform" type="rotate" from="45" to="0" dur="9s" repeatCount="indefinite"/>
      </g>
      <rect x="-3" y="-3" width="6" height="6" fill={ink}/>
    </g>
  </svg>
);

/* 17 — Self-drawing sine wave (stroke-dashoffset) */
Sym.s17 = () => (
  <svg viewBox="0 0 170 170">
    <g stroke={ink} fill="none">
      <line x1="10" y1="85" x2="160" y2="85" strokeWidth=".4" opacity=".4"/>
      <path d="M10 85 Q25 40 40 85 T70 85 T100 85 T130 85 T160 85" strokeWidth="1.3" strokeDasharray="220" strokeDashoffset="220" strokeLinecap="round">
        <animate attributeName="stroke-dashoffset" values="220;0;-220" dur="6s" repeatCount="indefinite"/>
      </path>
      <path d="M10 85 Q25 130 40 85 T70 85 T100 85 T130 85 T160 85" strokeWidth=".8" opacity=".5" strokeDasharray="220" strokeDashoffset="-220" strokeLinecap="round">
        <animate attributeName="stroke-dashoffset" values="-220;0;220" dur="6s" repeatCount="indefinite"/>
      </path>
    </g>
  </svg>
);

/* 18 — Measurement scale with sliding pointer arrow */
Sym.s18 = () => (
  <svg viewBox="0 0 170 170">
    <g stroke={ink} fill={ink}>
      <line x1="20" y1="100" x2="150" y2="100" strokeWidth=".7"/>
      {Array.from({length:11},(_,i)=>{
        const x = 20 + i*13, big = i%5===0;
        return <line key={i} x1={x} y1="100" x2={x} y2={big?116:108} strokeWidth={big?1:.5}/>;
      })}
      <g>
        <polygon points="0,-10 6,0 -6,0" stroke="none"/>
        <line x1="0" y1="0" x2="0" y2="48" strokeWidth=".7"/>
        <animateTransform attributeName="transform" type="translate" values="33 50;137 50;33 50" dur="6s" repeatCount="indefinite"/>
      </g>
      <text x="20" y="138" fontFamily={tMono} fontSize="8" fill={ink3} letterSpacing="2">00 ── 100</text>
    </g>
  </svg>
);

/* 19 — Compass needle slow rotation */
Sym.s19 = () => (
  <svg viewBox="0 0 170 170">
    <g transform="translate(85 85)">
      <circle r="68" fill="none" stroke={ink} strokeWidth=".5" opacity=".4"/>
      <circle r="58" fill="none" stroke={ink} strokeWidth=".4" opacity=".25"/>
      {['N','E','S','W'].map((d,i)=>{
        const a = (i*90 - 90) * Math.PI / 180;
        return <text key={i} x={Math.cos(a)*76} y={Math.sin(a)*76+3}
          fontFamily={tMono} fontSize="8" fill={ink} textAnchor="middle" letterSpacing="1">{d}</text>;
      })}
      <g>
        <polygon points="0,-60 4,0 -4,0" fill={ink}/>
        <polygon points="0,60 4,0 -4,0" fill="none" stroke={ink} strokeWidth=".7"/>
        <animateTransform attributeName="transform" type="rotate" from="0" to="360" dur="42s" repeatCount="indefinite"/>
      </g>
      <circle r="3" fill="#000" stroke={ink} strokeWidth=".7"/>
    </g>
  </svg>
);

/* 20 — Quadrant pulse: 4 cells alternating fill */
Sym.s20 = () => (
  <svg viewBox="0 0 170 170">
    <rect x="25" y="25" width="120" height="120" fill="none" stroke={ink} strokeWidth=".7"/>
    <line x1="85" y1="25" x2="85" y2="145" stroke={ink} strokeWidth=".7"/>
    <line x1="25" y1="85" x2="145" y2="85" stroke={ink} strokeWidth=".7"/>
    {[[25,25],[85,25],[25,85],[85,85]].map(([x,y],i)=>(
      <rect key={i} x={x+1} y={y+1} width="58" height="58" fill={ink} opacity="0">
        <animate attributeName="opacity" values="0;.9;0" dur="4s" begin={`${i*1}s`} repeatCount="indefinite"/>
      </rect>
    ))}
    <circle cx="85" cy="85" r="3" fill={ink}/>
  </svg>
);

/* ===== Compose variants ===== */
const VARIANTS = [
  {n:1, key:'s01', name:'Liquid · marble'},
  {n:2, key:'s02', name:'Ring · pulse'},
  {n:3, key:'s03', name:'Crosshair · target'},
  {n:4, key:'s04', name:'Response · breath'},
  {n:5, key:'s05', name:'Notch · carve'},
  {n:6, key:'s06', name:'Arc · orbit'},
  {n:7, key:'s07', name:'Constellation'},
  {n:8, key:'s08', name:'Scan · field'},
  {n:9, key:'s09', name:'Trio · orbit'},
  {n:10,key:'s10', name:'Hex · rotate'},
  {n:11,key:'s11', name:'Grid · pulse'},
  {n:12,key:'s12', name:'Spiral · slow'},
  {n:13,key:'s13', name:'Radial · clock'},
  {n:14,key:'s14', name:'Triangle · scan'},
  {n:15,key:'s15', name:'Venn · breath'},
  {n:16,key:'s16', name:'Diagonals'},
  {n:17,key:'s17', name:'Wave · draw'},
  {n:18,key:'s18', name:'Scale · pointer'},
  {n:19,key:'s19', name:'Compass'},
  {n:20,key:'s20', name:'Quadrant · pulse'},
];

const Comps = {};
VARIANTS.forEach(v => {
  Comps[v.key] = () => (
    <Plate idx={v.n} label={v.name}>
      {React.createElement(Sym[v.key])}
    </Plate>
  );
});

window.LogoVariants = VARIANTS;
window.LogoComponents = Comps;
