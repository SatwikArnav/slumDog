"""Collision-aware, deterministic street-dog roaming without rendering dependencies."""
import heapq
import math
import random
from collections import deque


def blocked(x,z,obstacles,radius=.24):
    return any((x-max(a,min(x,c)))**2+(z-max(b,min(z,d)))**2 < radius**2
               for a,b,c,d in obstacles)


class Navigation:
    step = .25

    def __init__(self,obstacles):
        self.obstacles = obstacles
        self.cells = set()
        for i in range(44):
            for j in range(111):
                x,z = self.point((i,j))
                region = (-1<=x<=1 and -25<=z<=2.5) or (.75<=x<=8.5 and -22.5<=z<=-18.25)
                if region and not blocked(x,z,obstacles,.28):
                    self.cells.add((i,j))
        if not self.cells:
            raise ValueError('No navigable street cells')

    def point(self,cell):
        return (-1.25+cell[0]*self.step,-25+cell[1]*self.step)

    def nearest(self,point):
        return min(self.cells,key=lambda c:math.dist(self.point(c),point))

    def neighbors(self,cell):
        i,j = cell
        for dx,dz in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            nxt = i+dx,j+dz
            if nxt in self.cells and (not dx or not dz or ((i+dx,j) in self.cells and (i,j+dz) in self.cells)):
                yield nxt

    def connected(self,start):
        todo,seen = deque([start]),{start}
        while todo:
            for nxt in self.neighbors(todo.popleft()):
                if nxt not in seen:
                    seen.add(nxt)
                    todo.append(nxt)
        return seen

    def path(self,start,goal,player=None):
        queue,previous,cost = [(0,start)],{}, {start:0.}
        while queue:
            _,cell = heapq.heappop(queue)
            if cell == goal:
                route = [cell]
                while cell in previous:
                    cell = previous[cell]
                    route.append(cell)
                return [self.point(c) for c in reversed(route)]
            for nxt in self.neighbors(cell):
                if player and math.dist(self.point(nxt),player) < .7:
                    continue
                distance = cost[cell]+math.dist(self.point(cell),self.point(nxt))
                if distance < cost.get(nxt,float('inf')):
                    cost[nxt],previous[nxt] = distance,cell
                    heapq.heappush(queue,(distance+math.dist(self.point(nxt),self.point(goal)),nxt))
        return []


class StreetDog:
    def __init__(self,obstacles,seed=12):
        self.nav = Navigation(obstacles)
        self.rng = random.Random(seed)
        self.x,self.z = self.nav.point(self.nav.nearest((.5,1.25)))
        self.reachable = sorted(self.nav.connected(self.nav.nearest((self.x,self.z))))
        self.yaw = math.pi
        self.mode,self.age,self.wait = 'roam',0.,0.
        self.path = []
        self.phase,self.walk_weight,self.speed = 0.,0.,0.
        self.cooldown,self.ambient = 4.,9.
        self.bark_events = 0

    def can_stand(self,x,z,yaw,player):
        for offset in (-.28,0,.48):
            px,pz = x+math.sin(yaw)*offset,z+math.cos(yaw)*offset
            if blocked(px,pz,self.nav.obstacles,.16) or math.dist((px,pz),player) < .55:
                return False
        return True

    def plan(self,player):
        here = self.nav.nearest((self.x,self.z))
        candidates = [c for c in self.reachable if 1.2 < math.dist(self.nav.point(c),(self.x,self.z)) < 4.5
                      and math.dist(self.nav.point(c),player) > 1.4
                      and math.dist(self.nav.point(c),player) < 8]
        self.rng.shuffle(candidates)
        for goal in candidates[:24]:
            path = self.nav.path(here,goal,player)
            if path:
                self.path = path[1:]
                return
        self.mode,self.age,self.wait = 'idle',0.,1.

    def update(self,dt,player):
        dt = max(0,min(.05,dt))
        self.age += dt
        self.cooldown -= dt
        self.ambient -= dt
        event = False
        near = math.dist((self.x,self.z),player) < 2.7
        if self.mode!='bark' and self.cooldown<=0 and (near or self.ambient<=0):
            self.mode,self.age = 'bark',0.
            self.cooldown,self.ambient = self.rng.uniform(9,15),self.rng.uniform(14,24)
            self.bark_events += 1
            event = True
        moved = 0.
        if self.mode == 'bark':
            self.speed = 0
            if self.age >= .75:
                self.mode,self.age,self.wait = 'idle',0.,self.rng.uniform(.7,1.6)
        elif self.mode in ('idle','sniff'):
            self.speed = 0
            if self.age >= self.wait:
                self.mode,self.age,self.path = 'roam',0.,[]
        else:
            if not self.path:
                self.plan(player)
            if self.path:
                tx,tz = self.path[0]
                dx,dz = tx-self.x,tz-self.z
                distance = math.hypot(dx,dz)
                if distance < .055:
                    self.path.pop(0)
                    if not self.path:
                        self.mode,self.age,self.wait = self.rng.choice(['sniff','idle']),0.,self.rng.uniform(2,4)
                else:
                    desired = math.atan2(dx,dz)
                    turn = (desired-self.yaw+math.pi)%math.tau-math.pi
                    self.yaw += max(-4*dt,min(4*dt,turn))
                    self.speed = min(.65,self.speed+1.5*dt)*max(0,math.cos(turn))
                    step = min(distance,self.speed*dt)
                    nx,nz = self.x+dx/distance*step,self.z+dz/distance*step
                    if self.can_stand(nx,nz,self.yaw,player):
                        self.x,self.z,moved = nx,nz,step
                    else:
                        self.mode,self.age,self.wait,self.path = 'idle',0.,.6,[]
                        self.speed = 0
        self.phase = (self.phase+moved/.38)%1
        weight = min(1,moved/(.65*dt)) if dt else 0
        self.walk_weight += (weight-self.walk_weight)*(1-math.exp(-12*dt))
        return event
