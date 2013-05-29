from random import randint

fn = input("What's the input filename? ")
ls = open(fn).read().split("\n")
n  = int(ls[0]) #total no. of pieces
ns = [(max(0, float(ls[k])), k) for k in range(1, 8)] #ratios
t  = sum([x for (x, k) in ns]) #total of ratios
ps = [k for (x, k) in ns for i in range(int(x / t * n))] #the pieces 
ps += [max(ns)[1] for k in range(n - len(ps))] #top up for rounding
qs  = [] 
for k in range(len(ps)): 
    x = randint(k, len(ps) - 1) #randomise
    qs.append(ps[x]) 
    ps[x] = ps[k]
fx = open("z" + fn, 'w')
while qs != []:
    s = str(qs[:50]).replace(", ", "")[1:-1]
    fx.write(s)
    fx.write("\n")
    qs = qs[50:]
input("Hit Enter to finish")
