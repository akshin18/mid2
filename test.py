



a = {"a":1,"b":2}

for i  in a.copy():
    if "a" in i:
        del a[i]
print(a)