import json
import re
import copy
import collections
import sys

SHOCKHP = 3
MOVEHP = 1
MAXHP = 20
FOODHP = 4

with open('../game/eelectric.js', 'r') as f:
    a = f.read()
    a = re.search(re.compile(r'// SOLVERSTART(.*)// SOLVEREND', re.S), a).group(0)
    a = re.sub(re.compile(r'//(.*)$', re.M), '', a)
    LEVELS = json.loads('['+a+']')

class Game:
    def __init__(self, l):
        self.name = l['name']
        self.map = ''.join(l['map'])
        self.eel = l['eel']
        self.hp = l['hp']
        self.charge = True
        self.stars = 0
        self.food = 0
        self.foodhp = dict()
        self.blocked = 0
        i = 0
        for y in range(13):
            for x in range(13):
                p = self.map[i]
                if p == '0':
                    self.stars += 1
                    self.foodhp[i] = 0
                elif p == '1' or p == '2' or p == '3' or p == '4':
                    self.food += 1
                    self.foodhp[i] = int(p)
                elif p == '*' or p == 'p':
                    self.blocked += 1
                i += 1
    def clone(self):
        result = copy.copy(self)
        result.eel = self.eel[:]
        result.foodhp = result.foodhp.copy()
        return result
    def canshock(self):
        return self.charge
    def shock(self):
        self.charge = False
        self.hp -= SHOCKHP
        harm = False
        def sh(x, y):
            nonlocal harm
            i = (y + 6) * 13 + x + 6
            #print(' ~ %d,%d' % (x, y))
            if i in self.foodhp:
                if self.foodhp[i] > 0:
                    self.foodhp[i] -= 1
                    harm = True
        eel = self.eel
        for i in range(0,len(eel),2):
            x = eel[i]
            y = eel[i+1]
            px = eel[i-2] - x if i > 0 else None
            py = eel[i-1] - y if i > 0 else None
            nx = eel[i+2] - x if i < len(eel) - 2 else None
            ny = eel[i+3] - y if i < len(eel) - 2 else None
            nw = px == -1 or nx == -1
            ne = py == -1 or ny == -1
            se = px == 1 or nx == 1
            sw = py == 1 or ny == 1
            #print(' ~~ %s,%s %s,%s' % (px, py, nx, ny))
            #print(' ~~ %s %s %s %s' % (nw, ne, sw, se))
            if i == 0 or i == len(eel) - 2:
                if not nw and not se:
                    sh(x - 1, y)
                    sh(x + 1, y)
                else:
                    sh(x, y - 1)
                    sh(x, y + 1)
            else:
                if not nw:
                    sh(x - 1, y)
                if not ne:
                    sh(x, y - 1)
                if not se:
                    sh(x + 1, y)
                if not sw:
                    sh(x, y + 1)
        return harm
    def canmove(self, dx, dy):
        eel = self.eel
        nx = eel[0] + dx
        ny = eel[1] + dy
        for i in range(2,len(eel),4):
            if eel[i] == nx and eel[i+1] == ny:
                #if dx == 0 and dy == -1:
                #    print(' eel')
                return False
        i = (ny + 6)*13 + nx + 6
        what = self.map[i]
        if what == '*' or what == 'p':
            #if dx == 0 and dy == -1:
            #    print(' thing %s' % what)
            return False
        if i in self.foodhp:
            if self.foodhp[i] > 0:
                #if dx == 0 and dy == -1:
                #    print(' food %d' % self.foodhp[i])
                return False
        return True
    def move(self, dx, dy):
        eel = self.eel
        nx = eel[0] + dx
        ny = eel[1] + dy
        self.hp -= MOVEHP
        i = (ny + 6)*13 + nx + 6
        if i in self.foodhp:
            what = self.map[i]
            if what == '0':
                self.stars -= 1
            else:
                del self.foodhp[i]
                self.food -= 1
                self.hp = min(MAXHP, self.hp + FOODHP)
        self.eel = [nx, ny] + eel[:-2]
        self.charge = True
    def over(self):
        if self.hp <= 0:
            return True
        return self.food == 0
    def d_length(self):
        return len(self.eel)/2
    def d_emptyc(self):
        return 13*13 - self.blocked - self.d_length()

def solve(game):
    game = game.clone()
    hp = 1
    todo = collections.deque()
    hp0 = None
    steps0 = None
    solutions0 = []
    solutions2 = []
    failures = collections.deque()
    steps = 0
    def step():
        nonlocal steps
        steps += 1
        l = todo.popleft()
        sofar = l[0]
        game = l[1]
        if game.hp <= 0:
            failures.append(l)
            return
        #print('sofar %s %s' % (sofar, game.eel))
        if game.canshock():
            game2 = game.clone()
            if game2.shock():
                n = (sofar + '_', game2)
                if not game2.over():
                    todo.append(n)
                elif game2.hp <= 0 and hp - game2.hp < MAXHP:
                    failures.append(n)
        if game.canmove(-1, 0):
            game2 = game.clone()
            game2.move(-1, 0)
            n = (sofar + 'q', game2)
            if game2.food == 0 and game2.stars == 0:
                solutions2.append(n[0])
            elif game2.food == 0 and not hp0:
                solutions0.append(n[0])
            elif not game2.over():
                todo.append(n)
            elif game2.hp <= 0 and hp - game2.hp < MAXHP:
                failures.append(n)
        if game.canmove(0, -1):
            game2 = game.clone()
            game2.move(0, -1)
            n = (sofar + 'w', game2)
            if game2.food == 0 and game2.stars == 0:
                solutions2.append(n[0])
            elif game2.food == 0 and not hp0:
                solutions0.append(n[0])
            elif not game2.over():
                todo.append(n)
            elif game2.hp <= 0 and hp - game2.hp < MAXHP:
                failures.append(n)
        if game.canmove(1, 0):
            game2 = game.clone()
            game2.move(1, 0)
            n = (sofar + 's', game2)
            if game2.food == 0 and game2.stars == 0:
                solutions2.append(n[0])
            elif game2.food == 0 and not hp0:
                solutions0.append(n[0])
            elif not game2.over():
                todo.append(n)
            elif game2.hp <= 0 and hp - game2.hp < MAXHP:
                failures.append(n)
        if game.canmove(0, 1):
            game2 = game.clone()
            game2.move(0, 1)
            n = (sofar + 'a', game2)
            if game2.food == 0 and game2.stars == 0:
                solutions2.append(n[0])
            elif game2.food == 0 and not hp0:
                solutions0.append(n[0])
            elif not game2.over():
                todo.append(n)
            elif game2.hp <= 0 and hp - game2.hp < MAXHP:
                failures.append(n)
    todo.append(('', game))
    for hp in range(1, 1 + MAXHP):
        game.hp = hp
        print('  trying hp %d' % hp)
        while todo:
            step()
        if not hp0 and solutions0:
            hp0 = hp
            steps0 = steps
        if solutions2:
            return (hp0, solutions0, steps0, hp, solutions2, steps)
        todo = failures
        failures = collections.deque()
        for t in todo:
            t[1].hp += 1
        if not todo:
            break
    print('  no solutions')
    return None

with open('data.txt', 'w') as o:
    print('Level\tEel Length\tFood Count\tSpaces\tHP Given\tHP Needed (0)\tSteps (0)\tSolution Count (0)\tHP Needed (2)\tSteps (2)\tSolution Count (2)', file=o)
    for l in LEVELS:
        g = Game(l)
        print(g.name)
        print('  eel length: %d' % g.d_length())
        print('  food count: %d' % g.food)
        print('  spaces    : %d' % g.d_emptyc())
        print('  hp given  : %d' % g.hp)
        sol = solve(g)
        print('  hp needed (0) : %d' % sol[0])
        print('  steps     (0) : %d' % sol[2])
        print('  solutions (0) : %d' % len(sol[1]))
        for s in sol[1]:
            print('    ... ' + s)
        print('  hp needed (2) : %d' % sol[3])
        print('  steps     (2) : %d' % sol[5])
        print('  solutions (2) : %d' % len(sol[4]))
        for s in sol[4]:
            print('    ... ' + s)
        print('%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d' % (g.name, g.d_length(), g.food, g.d_emptyc(), g.hp, sol[0], sol[2], len(sol[1]), sol[3], sol[5], len(sol[4])), file=o)
        o.flush()
