"""Expand/dress five existing shop shells without rebuilding the surrounding lane.
Called by the game exporter; standalone: blender -b --python environment/upgrade_shops.py
"""
from pathlib import Path
import bpy,math,random,json
from mathutils import Vector
ROOT=Path(__file__).resolve().parent


def upgrade_shops():
    scene=bpy.context.scene
    if scene.get('expanded_shops'):
        return json.loads(scene['expanded_shops'])
    rng=random.Random(927)
    col=bpy.data.collections.new('Expanded shop interiors');scene.collection.children.link(col)
    collision=bpy.data.collections['Collision'];collision.hide_viewport=False
    bpy.context.view_layer.update()
    def material(name,color,noise=False):
        m=bpy.data.materials.new(name);m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1)
        p.inputs['Roughness'].default_value=.78
        if noise:
            n=m.node_tree.nodes.new('ShaderNodeTexNoise');n.inputs['Scale'].default_value=17
            ramp=m.node_tree.nodes.new('ShaderNodeValToRGB')
            ramp.color_ramp.elements[0].color=(*[c*.72 for c in color],1)
            ramp.color_ramp.elements[1].color=(*color,1)
            m.node_tree.links.new(n.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
        return m
    wood=bpy.data.materials['Worn timber'];steel=bpy.data.materials['Old painted black metal']
    silver=bpy.data.materials['Brushed steel utensils'];paper=material('Shop paper and cotton',(.72,.68,.55))
    wall=material('Shop limewash with wear',(.68,.63,.48),True)
    tile=material('Shop worn terrazzo',(.43,.40,.32),True)
    tile_dark=material('Shop replacement floor tile',(.36,.35,.30))
    grout=material('Shop dark grout',(.16,.15,.12))
    brass=material('Shop brass hardware',(.46,.31,.10));red=bpy.data.materials['Painted red cylinder']
    cloth=[material('Shop fabric '+str(i),c,True) for i,c in enumerate([(.18,.31,.40),(.38,.13,.10),(.23,.34,.21)])]
    pack=[material('Shop package '+str(i),c) for i,c in enumerate([(.42,.09,.045),(.08,.26,.15),(.57,.36,.06),(.10,.22,.36)])]
    atlas=material('Shop printed labels',(1,1,1));n=atlas.node_tree.nodes.new('ShaderNodeTexImage')
    n.image=bpy.data.images.load(str(ROOT/'assets/shop_labels.png'),check_existing=True);n.image.pack()
    atlas.node_tree.links.new(n.outputs['Color'],atlas.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    unit=bpy.data.meshes.new('Shop box');unit.from_pydata([(-.5,-.5,-.5),(.5,-.5,-.5),(.5,.5,-.5),(-.5,.5,-.5),(-.5,-.5,.5),(.5,-.5,.5),(.5,.5,.5),(-.5,.5,.5)],[],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
    meshes={}
    cylinders={}
    specs=[(-1,1.6,'GANESH KIRANA','grocer'),(-1,9.5,'RAHIM TAILORS','tailor'),(-1,18.1,'SHANTI ELECTRICAL','electrical'),(1,5.5,'SHANKAR CHAI','tea'),(1,9.5,'SAI CYCLE WORKS','cycle')]
    report=[]
    for side,cy,title,kind in specs:
        old=next(o for o in list(collision.objects) if o.name.startswith('COL_building') and abs(o.location.y-cy)<.01 and o.location.x*side>0)
        depth,width=old.dimensions.x,old.dimensions.y
        front=old.location.x-side*depth/2
        def point(u,v,z):return (front+side*u,cy+v,z)
        def box(name,u,v,z,d,w,h,mat=wood,solid=False):
            if mat.name not in meshes:
                mesh=unit.copy();mesh.materials.append(mat);meshes[mat.name]=mesh
            ob=bpy.data.objects.new(title+' | '+name,meshes[mat.name]);col.objects.link(ob)
            ob.location=point(u,v,z);ob.scale=(d,w,h)
            if solid:
                c=bpy.data.objects.new('COL_shop '+title+' '+name,unit);collision.objects.link(c)
                c.location=ob.location;c.scale=ob.scale;c.hide_render=True;c.display_type='WIRE'
            return ob
        def rod(name,a,b,r,mat=steel):
            a,b=Vector(point(*a)),Vector(point(*b))
            if mat.name not in cylinders:
                vertices=[(math.cos(i*math.tau/12),math.sin(i*math.tau/12),z) for z in (-.5,.5) for i in range(12)]
                faces=[tuple(reversed(range(12))),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)]
                mesh=bpy.data.meshes.new('Shop cylinder '+mat.name);mesh.from_pydata(vertices,[],faces);mesh.materials.append(mat)
                for f in mesh.polygons:f.use_smooth=len(f.vertices)==4
                cylinders[mat.name]=mesh
            o=bpy.data.objects.new(title+' | '+name,cylinders[mat.name]);col.objects.link(o)
            o.location=(a+b)/2;o.scale=(r,r,(b-a).length);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
            return o
        def label(name,u,v,z,w,h,index):
            verts=[point(u,v-w/2,z-h/2),point(u,v+w/2,z-h/2),point(u,v+w/2,z+h/2),point(u,v-w/2,z+h/2)]
            mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],[(0,1,2,3)] if side<0 else [(3,2,1,0)])
            mesh.materials.append(atlas);uv=mesh.uv_layers.new()
            # Same reading direction when looking into either side of the street.
            a,b=(index%4)/4,1-(index//4+1)/4
            coords=[(a+.003,b+.003),(a+.247,b+.003),(a+.247,b+.247),(a+.003,b+.247)]
            if side>0:coords=[coords[1],coords[0],coords[3],coords[2]]
            for face in mesh.polygons:
                for loop_id,vertex_id in zip(face.loop_indices,face.vertices):uv.data[loop_id].uv=coords[vertex_id]
            o=bpy.data.objects.new(title+' | '+name,mesh);col.objects.link(o)
        def table(name,u,v,d,w,height=.85):
            box(name+' top',u,v,height,d,w,.065,wood)
            for du in (-d*.4,d*.4):
                for dv in (-w*.4,w*.4):box(name+' leg',u+du,v+dv,height/2,.045,.045,height,steel)
            box(name+' collision',u,v,height/2,d,w,height,wood,solid=True).hide_render=True
        # Remove the shallow false rear wall and generic contents, not the outer shell.
        for o in list(scene.objects):
            if o==old:continue
            if o.type not in {'MESH','CURVE'}:continue
            pts=[o.matrix_world@Vector(v) for v in o.bound_box]
            center=sum(pts,Vector())/8
            inside=abs(center.y-cy)<width/2-.1 and -.65<(center.x-front)*side<depth+.1
            prefixes=('Shop back wall','Shop shelving','Shop stock','Worn shop step')
            tea_names=('Tea counter','Tea glass','Tea kettle','Kettle ','Tea stove','LPG cylinder','Cylinder valve','Gas hose','Hanging snack packets')
            if inside and (o.name.startswith(prefixes) or (kind=='tea' and o.name.startswith(tea_names))):
                bpy.data.objects.remove(o,do_unlink=True)
            elif inside and o.name.startswith('Concrete floor slab') and abs(center.z)<.1:
                o.location.z-=.09
            elif inside and o.name.startswith('Hand-painted local shop board'):
                o.location.z+=.24
        bpy.data.objects.remove(old,do_unlink=True)
        # Side/back walls leave a genuine open entrance and central walking aisle.
        for v in (-width/2+.08,width/2-.08):
            box('plaster side lining',depth/2,v,1.28,depth,.10,2.56,wall,True)
            box('dark skirting',depth/2,v-side*.005,.10,depth,.13,.18,wood)
            box('painted lower wall',depth/2,v-math.copysign(.06,v),.62,depth-.05,.018,1.05,
                cloth[0] if kind in ('tailor','electrical') else cloth[2] if kind=='tea' else tile_dark)
        box('plaster rear lining',depth-.16,0,1.28,.10,width-.15,2.56,wall,True)
        for v in (-width/2+.16,width/2-.16):
            box('entrance pier',0,v,1.3,.28,.32,2.6,wall,True)
        box('threshold drain crossing',-.35,0,-.025,.85,width-.4,.06,tile)
        box('floor grout bed',depth/2,0,-.025,depth-.1,width-.2,.05,grout)
        for u in range(int((depth-.2)/.42)):
            for v in range(int((width-.2)/.42)):
                box('worn floor tile',.2+u*.42,-width/2+.3+v*.42,.002,.405,.405,.016,tile if (u+v)%5 else tile_dark)
        # Common services: roller-shutter drum, conduit, working light, ceiling fan.
        rod('rolled shutter',(0,-width/2+.3,2.55),(0,width/2-.3,2.55),.115,silver)
        for v in (-width/2+.30,width/2-.30):box('shutter guide',.01,v,1.2,.045,.055,2.4,steel)
        rod('fluorescent tube',(1.4,-.45,2.49),(1.4,.45,2.49),.025,paper)
        box('tube light housing',1.4,0,2.53,.14,1,.06,steel)
        rod('surface conduit',(.15,width/2-.18,1.3),(.15,width/2-.18,2.45),.012,paper)
        box('switchboard',.16,width/2-.18,1.30,.08,.16,.23,paper)
        rod('fan downrod',(depth*.55,0,2.63),(depth*.55,0,2.30),.018,steel)
        rod('fan hub',(depth*.55,0,2.27),(depth*.55,0,2.33),.10,paper)
        for angle in (0,math.tau/3,2*math.tau/3):
            blade=box('ceiling fan blade',depth*.55+.22*math.cos(angle),.22*math.sin(angle),2.29,.52,.11,.02,paper)
            blade.rotation_euler.z=side*angle
        label('wall calendar',depth-.22,width*.31,1.75,.42,.58,12)
        label('payment notice',.12,width*.30,1.6,.32,.36,13)
        if kind=='electrical':label('electrical shop fascia',-.29,0,2.43,width*.84,.46,11)
        # Rear shelves have a full clear centre aisle in front of them.
        shelf_u=depth-.46
        if kind in ('grocer','tailor','electrical'):
            for v in (-width/2+.30,width/2-.30):box('shelf upright',shelf_u,v,1.18,.045,.045,2.28,steel)
            for level in range(5):
                z=.30+level*.43
                box('rear shelf',shelf_u,0,z,.49,width-.5,.045,wood)
                for j in range(int((width-.65)/.25)):
                    v=-width/2+.46+j*.25
                    if kind=='grocer':
                        if (j+level*2)%9==0:continue
                        idx=rng.randrange(8);v+=rng.uniform(-.018,.018)
                        height=rng.uniform(.20,.34);pw=rng.uniform(.16,.21)
                        if level in (1,3):
                            rod('oil bottle' if level==3 else 'provision tin',(shelf_u-.03,v,z+.025),(shelf_u-.03,v,z+height),pw*.46,pack[idx%4])
                            rod('bottle cap',(shelf_u-.03,v,z+height),(shelf_u-.03,v,z+height+.035),pw*.34,brass)
                        else:box('labelled grocery packet',shelf_u-.03,v,z+height/2+.025,.20,pw,height,pack[idx%4])
                        label('packet label',shelf_u-.135,v,z+height/2+.025,pw*.90,height*.87,idx)
                    elif kind=='tailor':
                        for k in range(rng.randrange(2,6)):
                            o=box('folded fabric',shelf_u+rng.uniform(-.02,.02),v+rng.uniform(-.015,.015),z+.045+k*.045,.34,.21,.04,cloth[(j+k)%3])
                            o.rotation_euler.z=rng.uniform(-.06,.06)
                    else:
                        box('parts carton',shelf_u,v,z+.14,.28,.20,.24,paper);label('parts carton label',shelf_u-.145,v,z+.14,.18,.19,15)
            box('shelf collision',shelf_u,0,1.1,.52,width-.5,2.2,wood,True).hide_render=True
        if kind=='grocer':
            table('sales counter',1.05,-width*.31,1.35,.72,.93)
            box('weighing scale base',1.0,-width*.31,1.02,.29,.29,.12,steel)
            rod('scale pan',(1.0,-width*.31,1.09),(1.0,-width*.31,1.12),.19,silver)
            label('price list',depth-.22,-.7,2.10,.52,.35,0)
            for i in range(3):
                u=1.9+i*.55;v=-width*.33
                rod('grain sack',(u,v,.07),(u,v,.48),.22,paper)
                rod('visible grain',(u,v,.48),(u,v,.49),.195,brass)
                box('sack collision',u,v,.25,.45,.45,.5,wood,True).hide_render=True
            for j in range(7):label('hanging sachet strip',.10,-width*.28+j*.24,2.08,.16,.27,j%8)
        elif kind=='tailor':
            table('cutting table',1.65,-width*.29,1.65,.86,.88)
            box('fabric on cutting table',1.8,-width*.29,.929,1.0,.68,.025,cloth[0])
            box('sewing machine base',1.25,-width*.29,.95,.39,.27,.045,steel)
            box('sewing machine pillar',1.34,-width*.29,1.10,.10,.14,.30,steel)
            box('sewing machine arm',1.20,-width*.29,1.23,.34,.13,.09,steel)
            rod('needle',(1.05,-width*.29,1.19),(1.05,-width*.29,.99),.006,silver)
            rod('thread spool',(1.35,-width*.29,1.27),(1.35,-width*.29,1.37),.026,cloth[1])
            label('alteration order',1.2,-width*.29,1.43,.30,.23,14)
            for j in range(6):
                u=.6+j*.38;v=width*.36
                rod('fabric roll',(u,v,.12),(u,v,1.3+rng.random()*.25),.105,cloth[j%3])
            rod('garment rail',(.6,width*.35,1.9),(2.7,width*.35,1.9),.018,steel)
            for j in range(5):
                u=.7+j*.39;v=width*.35
                outline=[(-.13,.98),(.13,.98),(.14,1.53),(.23,1.40),(.29,1.49),(.17,1.75),(.06,1.78),(0,1.71),(-.06,1.78),(-.17,1.75),(-.29,1.49),(-.23,1.40),(-.14,1.53)]
                mesh=bpy.data.meshes.new('Shirt outline');mesh.from_pydata([point(u+du,v+.015*math.sin(i*2),zz) for i,(du,zz) in enumerate(outline)],[],[tuple(range(len(outline)))])
                mesh.materials.append(cloth[j%3]);o=bpy.data.objects.new(title+' | hanging shirt',mesh);col.objects.link(o)
                solid=o.modifiers.new('Cloth thickness','SOLIDIFY');solid.thickness=.008
                rod('hanger',(u-.14,v,1.79),(u,v,1.89),.006,silver);rod('hanger',(u,v,1.89),(u+.14,v,1.79),.006,silver)
            box('garment rack collision',1.65,width*.35,.70,2.3,.40,1.4,wood,True).hide_render=True
            label('tailoring services',depth-.22,0,2.12,.75,.32,9)
        elif kind=='tea':
            table('tea preparation counter',1.35,-width*.32,2.0,.76,.94)
            box('stove',1.0,-width*.32,1.04,.43,.43,.14,steel)
            rod('kettle body',(1.0,-width*.32,1.11),(1.0,-width*.32,1.40),.145,silver)
            rod('kettle lid',(1.0,-width*.32,1.40),(1.0,-width*.32,1.43),.15,silver)
            rod('kettle spout',(1.0,-width*.32+.1,1.26),(.82,-width*.32+.22,1.34),.025,silver)
            rod('kettle handle',(1.0,-width*.32-.18,1.23),(1.0,-width*.32-.18,1.45),.020,steel)
            for j in range(3):
                rod('biscuit jar',(2.0,-width*.32-.24+j*.21,1.0),(2.0,-width*.32-.24+j*.21,1.25),.085,brass)
                rod('jar lid',(2.0,-width*.32-.24+j*.21,1.25),(2.0,-width*.32-.24+j*.21,1.28),.09,silver)
            for j in range(6):rod('chai glass',(1.7,-width*.32-.25+j*.10,1.0),(1.7,-width*.32-.25+j*.10,1.12),.033,paper)
            for j in range(3):
                u=1.0+j*.85;v=width*.32
                table('customer bench',u,v,.60,.65,.46)
            box('tiled backsplash',depth-.25,0,1.20,.04,width-.4,1.2,paper)
            label('chai menu',depth-.29,0,1.75,.9,.65,8)
            box('wash basin',depth-.55,-width*.30,.85,.50,.65,.14,silver,True)
            rod('tap riser',(depth-.60,-width*.3,.9),(depth-.60,-width*.3,1.15),.018,silver)
            rod('LPG bottle',(2.4,-width*.32,.06),(2.4,-width*.32,.65),.17,red)
        else:
            table('repair workbench',depth-.75,-width*.20,.95,width*.48,.91)
            box('pegboard',depth-.22,0,1.65,.045,width-.5,.92,wood)
            for j in range(12):
                v=-width/2+.45+j*(width-.8)/12
                rod('hanging spanner',(depth-.26,v,1.43),(depth-.26,v,1.79),.013,silver)
                rod('tool head',(depth-.26,v-.035,1.79),(depth-.26,v+.035,1.79),.018,silver)
            label('repair price board',depth-.29,0,2.16,.90,.34,10 if kind=='cycle' else 11)
            if kind=='cycle':
                # Two spoked wheels and a triangular bicycle frame along the side wall.
                v=width*.33
                for u in (1.10,2.18):
                    bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=8,location=point(u,v,.36),major_radius=.32,minor_radius=.024,rotation=(math.pi/2,0,0))
                    o=bpy.context.object;o.name=title+' | bicycle tyre';o.data.materials.append(steel)
                    for c in list(o.users_collection):c.objects.unlink(o)
                    col.objects.link(o)
                    for j in range(12):rod('wheel spoke',(u,v,.36),(u+.30*math.cos(j*math.tau/12),v,.36+.30*math.sin(j*math.tau/12)),.003,silver)
                points=[(1.1,v,.36),(1.5,v,.38),(1.4,v,.83),(1.95,v,.83),(2.18,v,.36)]
                for a,b in [(0,1),(1,2),(2,0),(2,3),(3,1),(3,4)]:rod('cycle frame',points[a],points[b],.018,pack[1])
                box('saddle',1.4,v,.87,.25,.15,.06,steel)
                rod('handlebar',(1.95,v-.20,.94),(1.95,v+.20,.94),.018,silver)
                box('bicycle collision',1.65,v,.48,1.8,.35,.96,steel,True).hide_render=True
            else:
                for j in range(3):
                    u=1.0+j*.7;v=width*.32
                    box('appliance awaiting repair',u,v,.32,.47,.48,.60,paper,True)
                    rod('fan motor',(u,v,.65),(u,v,.89),.085,steel)
                    for k in range(3):
                        a=k*math.tau/3;blade=box('desk fan blade',u+.14*math.cos(a),v,.91+.14*math.sin(a),.28,.025,.08,pack[2]);blade.rotation_euler.y=-side*a
        # Everyday working details shared by all counters, not random street clutter.
        box('account book',.8,-width*.31,1.01,.23,.17,.035,cloth[1])
        label('receipt pad',.68,-width*.31,1.10,.16,.14,14)
        for j in range(3):
            box('overhead storage carton',depth-.42,-width*.24+j*.65,2.35,.48,.53,.32,paper)
            label('carton print',depth-.665,-width*.24+j*.65,2.35,.38,.24,15)
        report.append({'name':title,'kind':kind,'side':side,'front':front,'center_y':cy,'width':width-.30,'depth':depth-.26,'clear_aisle_width':.9})
    bpy.context.view_layer.update()
    scene['expanded_shops']=json.dumps(report)
    return report


if __name__=='__main__':
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'Shanti_Nagar_Level.blend'))
    print(json.dumps(upgrade_shops(),indent=2))
    bpy.data.collections['Collision'].hide_viewport=True
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Shanti_Nagar_Shops.blend'),compress=True)
