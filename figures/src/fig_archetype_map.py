"""Archetype map: every archetype drawn from its code.

Generates figures/fig_archetype_map.svg (Chapter 7, "Where the archetypes sit").
Edit here and rerun with `python3 figures/src/fig_archetype_map.py` rather than
editing the SVG. x = zone range on the scale transect, row = farming-axis
position, color = the lever that leads the restorative work.
"""
import os

MODE = {  # lever colors (scale-led takes the transect's green); the three physical ones at the
          # spaced values of fig_siting_latitude.svg, so structure and management can be told
          # apart where their bars sit side by side
 'scale':('#5e7d3a','#ffffff'), 'siting':('#b8934a','#2c2c2a'), 'structure':('#836836','#ffffff'), 'management':('#4f3d1c','#ffffff'),
 'ownership':('#4a6d8c','#ffffff'), 'contract':('#33506b','#ffffff')}
ROWS = [  # code, name, band tint (the position-table ramp), code color (the positions plate)
 ('S0','Created agriculture','#6ba6d1','#0d3452'), ('S1','Primary agriculture','#7fb3d9','#1c4c73'),
 ('S2','Secondary agriculture','#bfdaec','#2f6b96'), ('S3','Ordinary-land siting','#efeeea','#5f5e5a'),
 ('S4','Low-productivity siting','#d9cbe6','#6a4a91'), ('S5','Impaired-land siting','#b69ed4','#46295f')]
# row -> lanes -> bars: (first zone, last zone, label lines, mode, kind) kind: F featured, K sketched, D only in some cases
L = {
 'S0':[[(3,5,['Brightfield, where the ground layer is grazed'],'siting','D')]],
 'S1':[[(1,1,['Barnyard','Shelter Solar'],'ownership','F'),(2,5,['Regenerative Solar Grazing'],'management','F')],
       [(2,4,['Perennial Crop Canopy'],'structure','F')],
       [(2,4,['Solar Fencerows'],'structure','K')],
       [(2,3,['Vegetable Agrivoltaics'],'structure','K')],
       [(1,3,['Marginal Land Solar, where stock stays on'],'siting','D')]],
 'S2':[[(2,5,['Regenerative Solar Grazing'],'management','F')],
       [(3,3,['Pollinator Meadow,','where hives are kept'],'scale','D')]],
 'S3':[[(3,3,['Pollinator','Meadow Solar'],'scale','K'),(4,5,['Restored-Grassland Solar'],'management','K')],
       [(3,4,['Farm-Load Microgrid'],'siting','K')]],
 'S4':[[(2,3,['Marginal Land Solar'],'siting','F')],
       [(2,3,['Pivot-Corner Recharge'],'siting','K')],
       [(3,4,['Farm-Load Microgrid'],'siting','K')],
       [(3,5,['Brightfield'],'siting','K')]],
 'S5':[[(3,3,['Solar Prairie','Strips'],'siting','F'),(4,5,['Retired-Irrigation Solar'],'contract','F')]],
}
RARE={('S4',1),('S5',1),('S5',2),('S4',5)}
ZONES=[('A1','Farmstead','#EAF3DE'),('A2','Commercial','#DCEBC8'),('A3','Community','#C0DD97'),('A4','Utility','#AED483'),('A5','Complex','#97C459')]
X0,CW,LW=166,150,0; W=X0+5*CW+6
PITCH,BH,PAD=42,34,8
y=62; o=[]; rows_y=[]
for code,name,tint,cc in ROWS:
    n=len(L[code]); h=n*PITCH+2*PAD; rows_y.append((code,name,tint,cc,y,h)); y+=h
H_grid_end=y; H=y+96
def zx(z): return X0+(z-1)*CW
out=[]
out.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img">')
out.append('<title>Where the archetypes sit, and which lever does their work</title>')
out.append('<desc>A grid with the five ground-taking zones of the scale transect across the top, A1 Farmstead to A5 Complex, and the six farming-axis positions down the side, S0 Created agriculture at the top through S5 Impaired-land siting at the bottom. Each of the thirteen archetypes is drawn as a bar spanning the zones it recurs at, in the row of its farming-axis position, colored by the lever that leads its restorative work. Filled bars are the six featured archetypes, outlined bars the seven sketched ones, and dashed bars a position a form takes only in some cases. The primary-agriculture row runs from A1 to A5, carried at A1 by barnyard shelter and from A2 to A5 by grazing. Hatched cells mark combinations that rarely get built: sparing at A1, and impaired-land siting at A2, where the acreage spares almost nothing, and low-productivity siting at A5, where scattered remnants will not assemble and only brightfields reach. Every clear cell is possible, including created agriculture at any size. Ten of the thirteen forms reach A3. Read left to right, the colors tend to shift from ownership and structure at the small end, through siting and scale in the middle, to management and contracts at the large end.</desc>')
out.append('''<style>
text{font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.zc{font-size:13px;font-weight:700;fill:#2c2c2a}.zn{font-size:12px;fill:#3d3d3a}
.rc{font-size:15px;font-weight:700}.rn{font-size:11.5px;fill:#5f5e5a}
.bl{font-size:12px;font-weight:600}.bd{font-size:12px;font-style:italic;fill:#4a4944}
.lg{font-size:12px;fill:#3d3d3a}.lk{font-size:11.5px;fill:#5f5e5a}
</style>''')
# zone header chips
for i,(c,n,g) in enumerate(ZONES):
    x=zx(i+1)
    out.append(f'<rect x="{x+4}" y="16" width="{CW-8}" height="30" rx="5" fill="{g}" stroke="#c9c6bc" stroke-width="0.5"/>')
    out.append(f'<text x="{x+CW/2}" y="36" text-anchor="middle"><tspan class="zc">{c}</tspan><tspan class="zn" dx="6">{n}</tspan></text>')
out.append(f'<text class="rn" x="10" y="36">scale transect →</text>')
# row bands and labels
for code,name,tint,cc,ry,rh in rows_y:
    out.append(f'<rect x="0" y="{ry}" width="{W}" height="{rh}" fill="{tint}" fill-opacity="0.22"/>')
    cy=ry+rh/2
    out.append(f'<text class="rc" x="10" y="{cy-2:.0f}" fill="{cc}">{code}</text>')
    out.append(f'<text class="rn" x="10" y="{cy+14:.0f}">{name}</text>')
out.append('<defs><pattern id="rare" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="7" stroke="#8f8d84" stroke-width="1"/></pattern></defs>')
out.append('<!-- hatched: combinations that rarely get built. Every clear cell is possible, with or without a recurring form. -->')
for code,name,tint,cc,ry,rh in rows_y:
    for z in range(1,6):
        if (code,z) in RARE:
            out.append(f'<rect x="{zx(z)}" y="{ry}" width="{CW}" height="{rh}" fill="url(#rare)" opacity="0.55"/>')
out.append(f'<g stroke="#ffffff" stroke-width="2">'+''.join(f'<path d="M0,{ry} H{W}"/>' for *_,ry,rh in rows_y[1:])+'</g>')
out.append(f'<g stroke="#ffffff" stroke-width="2">'+''.join(f'<path d="M{zx(i)},{rows_y[0][4]} V{H_grid_end}"/>' for i in range(1,6))+'</g>')
# bars
for code,name,tint,cc,ry,rh in rows_y:
    for li,lane in enumerate(L[code]):
        by=ry+PAD+li*PITCH+(PITCH-BH)/2
        for z1,z2,lines,mode,kind in lane:
            x=zx(z1)+5; w=(z2-z1+1)*CW-10; col,tc=MODE[mode]
            if kind=='F':
                out.append(f'<rect x="{x}" y="{by}" width="{w}" height="{BH}" rx="4" fill="{col}"/>'); fill=tc; cls='bl'
            elif kind=='K':
                out.append(f'<rect x="{x}" y="{by}" width="{w}" height="{BH}" rx="4" fill="#ffffff"/>')
                out.append(f'<rect x="{x+1}" y="{by+1}" width="{w-2}" height="{BH-2}" rx="3.5" fill="{col}" fill-opacity="0.14" stroke="{col}" stroke-width="2"/>'); fill='#2c2c2a'; cls='bl'
            else:
                out.append(f'<rect x="{x+1}" y="{by+1}" width="{w-2}" height="{BH-2}" rx="3.5" fill="#ffffff" fill-opacity="0.6" stroke="{col}" stroke-width="1.6" stroke-dasharray="5 3"/>'); fill='#4a4944'; cls='bd'
            if len(lines)==1:
                out.append(f'<text class="{cls}" x="{x+w/2}" y="{by+BH/2+4.2:.1f}" text-anchor="middle" fill="{fill}">{lines[0]}</text>')
            else:
                out.append(f'<text class="{cls}" x="{x+w/2}" y="{by+BH/2-2.6:.1f}" text-anchor="middle" fill="{fill}" style="font-size:11.5px"><tspan x="{x+w/2}">{lines[0]}</tspan><tspan x="{x+w/2}" dy="13">{lines[1]}</tspan></text>')
# legend
ly=H_grid_end+30
x=10
out.append(f'<text class="lk" x="{x}" y="{ly+4}">restorative work</text>')
x=128
for m in ['scale','siting','structure','management','ownership','contract']:
    col,_=MODE[m]
    out.append(f'<rect x="{x}" y="{ly-8}" width="22" height="14" rx="3" fill="{col}"/><text class="lg" x="{x+28}" y="{ly+4}">{m}-led</text>')
    x+= 28+ {'scale':56,'siting':62,'structure':80,'management':98,'ownership':90,'contract':76}[m] + 18
ly2=ly+26
out.append(f'<text class="lk" x="10" y="{ly2+4}">filled: featured archetype · outlined: sketched · dashed: a position the form takes only in some cases</text>')
ly3=ly2+24
out.append(f'<rect x="10" y="{ly3-8}" width="22" height="14" fill="url(#rare)" opacity="0.8" stroke="#c9c6bc" stroke-width="0.5"/>')
out.append(f'<text class="lk" x="38" y="{ly3+4}">hatched: rarely built. A clear cell with no bar is possible, with no recurring form yet.</text>')
out.append('</svg>')
dest=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','fig_archetype_map.svg')
open(dest,'w').write('\n'.join(out)+'\n')
print(W,H)
