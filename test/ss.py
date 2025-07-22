import random
names = ["Harry","Ben","Harvey","Joe","Maddie","Tiegan"]

maddie = ["Harry","Harvey"]
harry = ["Maddie"]
harvey = ["Maddie"]

random.shuffle(names)
opener = names.copy()
random.shuffle(opener)

for name in names:
    index = names.index(name)
    print(f'{name} - {opener[0]}')
    del opener[0]
    
def restrictions(name):
    if name == "Maddie":
        pass