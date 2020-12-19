import matplotlib.pyplot as plt

graph_file = 'pathfinding_graph.txt'

with open(graph_file, 'r') as file:
    text = file.read()

cut_index = text.find('connections')
text = text[:cut_index]
lines = text.split('\n')[:-1]
data = [list(map(int, line.split(' '))) for line in lines]

indices, xs, ys = zip(*data)

plt.scatter(xs, ys)

for i, x, y in zip(indices, xs, ys):
    plt.annotate(i, (x, y))

plt.gca().invert_yaxis()
plt.show()