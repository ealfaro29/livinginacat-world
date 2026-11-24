"""Fijaciones de la revisión compacta. Las cantidades salen de los puntos de montaje."""
from collections import Counter, defaultdict
from math import cos, pi, sin, sqrt
from build123d import Align, Color, Cone, Plane, Polygon, Pos, extrude

FLAT, BUTTON, NUT = '7213', '7219', 'M3-cuadrada'
D_HEAD = 5.70
NUT_SIZE, NUT_HEIGHT = 5.4, 2.4
DRILL, POCKET, SLOT_H = 3.4, 5.8, 2.7

def estandarizar(m):
    box, cyl, pad, add = (m[k] for k in ('box','cylinder','rounded','add'))
    parts, find, cx, cy = (m[k] for k in ('parts','lookup','CX','CY'))
    slots, fittings, checks = [], [], []
    body, void = defaultdict(list), defaultdict(list)
    screw_groups={'fijo':'herrajesFijos','puente':'herrajesY','carro':'herrajesX','camara':'herrajesOptica'}

    def change(name,solid):
        index=next(i for i,a in enumerate(parts) if a[0]==name)
        _,grp,col,_,printed=parts[index]
        solid=solid.clean()
        assert solid.is_valid and (not printed or len(solid.solids())==1), (name,len(solid.solids()))
        solid.label=name
        solid.color=Color(m['PALETTE'][col])
        parts[index]=(name,grp,col,solid,printed)

    def merge(target,names,other=()):
        combined=find(target).fuse(*[find(n) for n in names],*other)
        change(target,combined)
        parts[:]=[p for p in parts if p[0] not in names]

    def socket(d,depth,z):
        r=d/sqrt(3)
        poly=Polygon(*[(r*cos(i*pi/3),r*sin(i*pi/3)) for i in range(6)], align=None)
        return Pos(0,0,z)*extrude(poly,amount=depth)

    align=(Align.CENTER,Align.CENTER,Align.MIN)
    def cone(z,high,low,h):
        return Pos(0,0,z)*Cone(high/2,low/2,h,align=align)

    nominal_flat=cone(0,6.50,3,1.75).fuse(cyl(0,0,1.75,3,6.25)).cut(socket(2,1.12,-.02))
    # Maximum head envelope, including its hex socket. Threads shown at the major diameter.
    button=cyl(0,0,-1.65,D_HEAD,1.65).fuse(cyl(0,0,0,3,8)).cut(socket(2,1.10,-1.67))
    sq=box(-2.7,2.7,-2.7,2.7,0,2.4).cut(cyl(0,0,-.1,2.55,2.6))
    csink=cone(-.01,7.02,DRILL,1.81)
    def loc(point,axis,side):
        # Local X is the insertion direction for the square nut.
        return Plane(origin=point,x_dir=side,z_dir=axis).location
    def joint(name,sku,point,axis,side,move='fijo',through=(),receiver=None,
              nut_z=None,exit_len=0,engagement=None,depth=None,head_part=None):
        uid=f'{name}_{1+sum(r["union"]==name for r in fittings):02d}'
        L=loc(point,axis,side)
        pos=.25 if sku==FLAT else 0.0
        head=nominal_flat if sku==FLAT else button
        add('T_'+sku+'_'+uid,screw_groups[move],'amber' if sku==FLAT else 'blue',L*Pos(0,0,pos)*head)
        for part in through:
            void[part].append(L*cyl(0,0,-.01,DRILL,9.1))
        if head_part is not None:
            assert sku==FLAT
            void[head_part].append(L*csink)
        if receiver:
            assert nut_z is not None and exit_len>POCKET/2
            # Pocket opens to the outside of the individual boss/rail, without an end cap.
            void[receiver]+=[L*box(-POCKET/2,exit_len,-POCKET/2,POCKET/2,nut_z,nut_z+SLOT_H),
                             L*cyl(0,0,-.01,DRILL,9.2)]
            nut_start=nut_z+.15
            add('Q_M3_'+uid,screw_groups[move],'warm',L*Pos(0,0,nut_start)*sq)
            assert 8+pos >= nut_start+NUT_HEIGHT-.01,uid
            slots.append(dict(union=name,centro=list(point),hacia=list(side),desde=nut_z,hasta=nut_z+SLOT_H,alcance=exit_len))
            checks.append((receiver,L*box(-2.7,exit_len-.06,-2.7,2.7,nut_start,nut_start+2.4),uid))
        if engagement is not None:
            assert 2.0<=engagement<=depth-.30+1e-8,(uid,engagement,depth)
        fittings.append(dict(union=name,codigo=sku,origen_mm=list(point),eje=list(axis),grupo=move,
            tuerca=NUT if receiver else None,mordida_mm=engagement,fondo_min_mm=depth))

    up=(0,0,1); down=(0,0,-1); right=(1,0,0); back=(0,1,0)
    # The two sidewalls meet their floor, bezel and switch cup as one serviceable half.
    # The original shell/bezel meet on their perimeter. The buried collar adds positive overlap.
    ring=m['frontpad'](m['LCD_X'],1.4,m['LCD_Z'],87,57,1.6,3).cut(
        m['frontpad'](m['LCD_X'],1.3,m['LCD_Z'],80,51,1.9,2))
    merge('Carcasa_delante',['Piso_delante','Bisel_pantalla_TS24'],[m['mount'],ring])
    merge('Carcasa_detras',['Piso_detras'])
    # Holes in the LCD support are retained, including through the optional buried collar.
    for x in (-82.5,-9.5):
        for z in (9.75,54.25):
            void['Carcasa_delante'].append(cyl(x,-.2,z,3.5,5,(0,1,0)))

    # The transverse bridge, its idler ledges and both saddles co-print on one bed.
    merge('Puente_transversal_nuevo',['Silla_Y_I','Silla_Y_D','Oreja_idler_A','Oreja_idler_B'])
    # Rail mounts. The solid of the steel rail already has an unmodified diameter-6 counterbore.
    for tag,sgn in [('I',-1),('D',1)]:
        x=cx+sgn*m['RAIL']
        support='Asiento_Y_'+tag
        merge(support,[f'Pie_asiento_{tag}_{i}' for i in range(3)])
        for y in range(18,264,20):
            joint('Guias_Y',BUTTON,(x,y,93.3),down,(sgn,0,0),receiver=support,nut_z=5.05,exit_len=8.9)
        for y in (65,133,237):
            xf=x+sgn*5.5
            base='Carcasa_delante' if y<145 else 'Carcasa_detras'
            joint('Asientos_al_piso',FLAT,(xf,y,0),up,back,through=(base,),receiver=support,
                  nut_z=4.6,exit_len=7.6,head_part=base)
        for a in (-7.5,7.5):
            for b in (-8,8):
                # Clearance above the seated head extends to the top of the integrated bridge.
                void['Puente_transversal_nuevo'].append(cyl(x+a,cy+b,105.4,6.35,27))
                joint('Patines_Y',BUTTON,(x+a,cy+b,105.4),down,right,'puente',
                      through=('Puente_transversal_nuevo',),engagement=2.6,depth=3.0)
    for x in range(-75,66,20):
        joint('Guia_X',BUTTON,(x,cy+14,133.8),down,back,'puente',receiver='Puente_transversal_nuevo',
              nut_z=5.05,exit_len=7.2)
    for a in (-8,8):
        for b in (-7.5,7.5):
            joint('Patin_X',BUTTON,(cx+a,cy+14+b,145.9),down,right,'carro',
                  through=('Carro_portapunta',),engagement=2.6,depth=3.0)
    for tag,sgn,face in [('A',-1,87),('B',1,94)]:
        motor='NEMA17_'+tag; cradle='Cuna_motor_'+tag; x=cx+sgn*26
        for a in (-15.5,15.5):
            for b in (-15.5,15.5):
                void[motor].append(cyl(x+a,275+b,face-2.7-4,2.5,4.1))
                joint('Motores',BUTTON,(x+a,275+b,face+2.3),down,right,
                      through=(cradle,),engagement=3,depth=4)
        # Printed feet transfer the loads straight to the rear half of the shell.
        merge('Carcasa_detras',[cradle,'Poste_retorno_'+tag])
        # The interfaces names in these queues refer to the same merged part.
        void['Carcasa_detras'].extend(void.pop(cradle,[]))

    # Two tabs make a lapped joint. The vertical side skirts also interlock along the seam.
    for x in (-89,89):
        tongue=pad(x,148.6,3,11,16.8,6.4,1.5)
        body['Carcasa_delante'].append(tongue.fuse(box(x-3,x+3,141.0,144.8,2.6,4)))
        joint('Costura_del_chasis',FLAT,(x,151,0),up,(-1 if x>0 else 1,0,0),through=('Carcasa_detras',),
              receiver='Carcasa_delante',nut_z=4.7,exit_len=6.0,head_part='Carcasa_detras')
    for side in (-1,1):
        for y in (186,206):
            # Replace the short cylindrical counterbore with a matched cone in solid plastic.
            x=side*98; ctr=(x,y,50); inward=(-side,0,0)
            L=loc(ctr,inward,back)
            body['Carcasa_detras'].append(L*cyl(0,0,0,6.8,3.0))
            body['Portico_camara_una_pieza'].append(L*box(-5,5,-4.7,4.7,3.2,8.85))
            joint('Portico_a_carcasa',FLAT,ctr,inward,back,through=('Carcasa_detras',),
                  receiver='Portico_camara_una_pieza',nut_z=4.65,exit_len=5.35,head_part='Carcasa_detras')
    # The lid has two accessible screws at the front and two integral releases at the rear.
    for x in (-62,52):
        y=88
        xmin,xmax=sorted((x-4.8 if x<0 else x+4.8, -96.5 if x<0 else 96.5))
        boss=box(x-4.8,x+4.8,y-5,y+5,37.2,44)
        body['Carcasa_delante'].append(boss.fuse(box(xmin-.2,xmax+.2,y-4.6,y+4.6,38.2,43.5)))
        joint('Panel_de_servicio',FLAT,(x,y,46.8),down,back,through=('Tabique_sobre_electronica',),
              receiver='Carcasa_delante',nut_z=4.6,exit_len=5.35,head_part='Tabique_sobre_electronica')
    for x in (-59,52):
        # Rest pads and snap tongues have independent sections to free the 12 mm flexing length.
        support=box(x-4,x+4,246.8,249.8,2.7,44)
        anchor=box(x-4,x+4,249.4,253.35,2.7,34.5)
        spring=m['yz']([(251.35,33.5),(252.72,33.5),(252.72,46.8),(251.7,49.2),
                         (250.1,48.0),(250.1,47.05),(251.35,47.05)],x-3.4,x+3.4)
        body['Carcasa_detras'].append(support.fuse(anchor,spring))
    # The control board bears on four printed, flat-topped mounting posts with side-fed nuts.
    for x in (-73,9):
        for y in (159,221):
            void['Carcasa_detras'].append(cyl(x,y,1.75,3.55,1.45))
            footprint=box(x-4.2,x+4.2,y-4.2,y+4.2,4.,9.)
            body['Bandeja_MKS'].append(footprint)
            void['MKS_DLC32_V22'].append(cyl(x,y,8.9,3.4,2))
            joint('Placa_MKS',BUTTON,(x,y,10.6),down,(-1 if x<0 else 1,0,0),receiver='Bandeja_MKS',
                  nut_z=4.05,exit_len=7.3)
    for x in (14.5,63.5):
        for y in (79,137):
            void['Raspberry_Pi_5'].append(cyl(x,y,8.9,2.7,2))
    # Both optical slots need flat bearing faces. An integral outer bearing shoulder
    # bridges each slot; the square nuts drop in the pod from the service side.
    for y in (136,151):
        # The head bears on the X+ face of the stationary slotted leaf. Each screw travels with the pod.
        ctr=(24.6,y,183); axis=(-1,0,0); insertion=(0.,0.,-1.)
        # Pod inner rail at x=16.5..20 contiguous with shoe. Reinforced ear extends away from the lens.
        loc_p=loc(ctr,axis,insertion)
        body['Capota_y_soporte_C922'].append(cyl(19.75,y,183,7.2,.85,(1,0,0)))
        body['Capota_y_soporte_C922'].append(loc_p*box(-4.3,4.3,-4,4,4.65,8.2))
        joint('Altura_camara',BUTTON,ctr,axis,insertion,'camara',receiver='Capota_y_soporte_C922',
              nut_z=4.85,exit_len=29.8)
    # Pi 5 on four reference lands. Two loose-tolerance pilot pins take in-plane
    # shear. Two edge hooks and two releasable spring cheeks hold the board down.
    pi_tray='Bandeja_Pi'
    for x in (14.5,63.5):
        body[pi_tray].append(cyl(x,79,6.2,3.4,2.8).fuse(cyl(x,79,8.85,2.15,.79)).fuse(Pos(x,79,0)*cone(9.64,2.15,1.65,.25)))
    for x in (19.,58.):
        body[pi_tray].append(box(x-2.3,x+2.3,73.65,75.05,3.4,11.7).fuse(
            box(x-2.3,x+2.3,74.6,76.55,10.85,12.05)))
    for sign in (-1,1):
        edge=39+sign*28
        section=[(edge+sign*u,z) for u,z in
                 [(.35,3.8),(1.7,3.8),(1.7,11.8),(.35,12.8),(-.75,11.5),(-.75,10.85),(.35,10.85)]]
        body[pi_tray].append(m['xz'](section,119.5,125.5))
    # The display keeps the owner's low-head M2.5 x 8. The screw bears on
    # the printed front. A washer on the flat PCB distributes the nut load.
    small_parts=[]
    def hex_outline(width):
        r=width/sqrt(3)
        return Polygon(*[(r*cos(i*pi/3),r*sin(i*pi/3)) for i in range(6)],align=None)
    nut25=extrude(hex_outline(5),amount=2).cut(cyl(0,0,-.1,2.16,2.2))
    screw25=cyl(0,0,-1.7,4.7,1.7).fuse(cyl(0,0,0,2.5,8))
    washer25=cyl(0,0,0,6,.5).cut(cyl(0,0,-.05,2.7,.6))
    for x in (-82.5,-9.5):
        for z in (9.75,54.25):
            uid=f'LCD_{1+len(small_parts):02d}'; origin=(x,1.95,z)
            L=loc(origin,back,right)
            panel='Carcasa_delante'
            body[panel].append(cyl(x,1.45,z,7.3,3.55,back))
            void[panel]+=[cyl(x,-.1,z,5.3,2.05,back), cyl(x,1.9,z,2.85,3.25,back)]
            void['PCB_pantalla_TS24'].append(cyl(x,4.85,z,2.8,2,back))
            add('T_M25_'+uid,'herrajesFijos','steel',L*screw25)
            add('Arandela_M25_'+uid,'herrajesFijos','steel',L*Pos(0,0,4.65)*washer25)
            add('Tuerca_M25_'+uid,'herrajesFijos','warm',L*Pos(0,0,5.15)*nut25)
            small_parts.append(dict(centro=list(origin),codigo='M2.5x8',componente='TS24-R'))
    # Known outer box and end collars of the existing Adafruit enclosure.
    # Two long-side hooks grasp the lid. Locating corners stop axial slip clear of both cable ports.
    rr='Carcasa_detras'
    for y,sign in [(m['ADA_Y']-12.2,-1),(m['ADA_Y']+12.2,1)]:
        cross=[(y+sign*u,z) for u,z in [(.35,2.75),(1.8,2.75),(1.8,15.6),(.55,17.8),
               (-.9,17.15),(-.9,16.5),(.35,16.5)]]
        body[rr].append(m['yz'](cross,m['ADA_X']-4.5,m['ADA_X']+4.5))
    for x,sign in [(m['ADA_X']-18.2,-1),(m['ADA_X']+18.2,1)]:
        xa,xb=sorted((x+sign*.35,x+sign*2.05))
        for y in (216.,232.):
            body[rr].append(box(xa,xb,y-1.5,y+1.5,2.7,7))
    # Machine bores after uniting positive features, including through any earlier structure.
    for name in dict.fromkeys([*body,*void]):
        sh=find(name)
        if body[name]: sh=sh.fuse(*body[name])
        if void[name]: sh=sh.cut(*void[name])
        change(name,sh)
    # Do not offset the deck, boards or camera datums when consolidating their carriers.
    merge('Carcasa_detras',['Bandeja_MKS'])
    # The Pi carrier crosses the seam. Integrate its four posts into the front half only;
    # clip its unsupported tail along the split. USB and Pi mounting hole positions are unchanged.
    front_pi=find('Bandeja_Pi') & box(-100,100,0,144.8,2,11)
    change('Bandeja_Pi',front_pi)
    merge('Carcasa_delante',['Bandeja_Pi'])
    # Side trim is integral with each shell half and split at the same seam.
    for tag in ('I','D'):
        for i in range(2):
            n=f'Borde_lateral_{tag}{i}'
            sh=find(n)
            for name,lo,hi in [('Carcasa_delante',0,144.9),('Carcasa_detras',145.1,302.01)]:
                chunk=sh & box(-110,110,lo,hi,50,91)
                if chunk is not None and len(chunk.solids()):
                    change(name,find(name).fuse(chunk))
            parts[:]=[p for p in parts if p[0]!=n]
    # Evaluate a full nut, including its insertion path, against the printed receiver.
    for name,probe,uid in checks:
        name={'Bandeja_MKS':'Carcasa_detras'}.get(name,name)
        clash=probe & find(name)
        v=sum(s.volume for s in clash.solids()) if clash is not None else 0
        assert v<.001,(uid,'boca de la tuerca',v)
    counts=Counter(r['codigo'] for r in fittings)
    bins={k:dict(Counter(r['union'] for r in fittings if r['codigo']==k)) for k in counts}
    assert counts[BUTTON]==34+12+8+4+2 and counts[FLAT]==2+6+4+2
    assert len(slots)==34+14+4+2
    return {'resumen':{'tornillos':dict(counts),'tuercas':{NUT:len(slots)},'por_union':bins,'posiciones':fittings,
        'ranuras_de_carga':slots,'fijaciones_pantalla':{'tornillo_M2.5x8_bajo':4,'arandela_M2.5':4,'tuerca_hex_M2.5':4,'posiciones':small_parts},
        'retenciones_impresas':{'Raspberry_Pi_5':'dos guías, dos ganchos y dos lengüetas; cero tornillos','caja_Adafruit':'dos lengüetas más topes; cero tornillos externos'},
        'llave_Allen_mm':2,'se_eliminan':{'cuna_del_telefono':4,'corredera_fija_al_portico':2,'cazoleta_del_interruptor':2},
        'balance_de_inventario':{'7213_comprados':10,'7219_comprados':50,'tuercas_cuadradas_M3_compradas':50,
        'libres_hoy':None},'ancho_ranura_mm':POCKET,'alto_ranura_mm':SLOT_H,
        'diametro_y_angulo_avellanado':[7,90],'tornillo_cabeza_boton_altura_max':1.65,
        'recorrido_de_ajuste_funda_camara_mm':[95,110],
        'fuera_de_este_conteo':['sujeción propia del ventilador y del disipador','ejes y separadores de poleas','acople, solenoide y mordaza de correas','tuerca S301T','tornillo de trípode','retención de cables y portafusible','fijación del canal y del convertidor definitivo']},
        'techo_cabezal':145.9+1.65}
