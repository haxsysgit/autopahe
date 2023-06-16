arg = "13-17"

# parsing the arg to get individial eps
epr = list(x for x in arg.split('-'))

# list of the range of eps
episodes_list = list(range(int(epr[0]),int(epr[1]) + 1))

print(episodes_list)

print(epr)