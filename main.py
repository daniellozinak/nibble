def open_file(_filename):
    data = []
    output = []
    with open(_filename) as f:
        for line in f:
            data.append(line.replace("\n", "").split(";"))
        del data[0]
    for row in data:
        temp = []
        for item in row:
            temp.append(int(item))
        output.append(temp)
    return output


def find_max(rows):
    max = 0
    for row in rows:
        for item in row:
            if item > max:
                max = item
    return max


def as_matrix(rows):
    max = find_max(rows)
    matrix = []
    for i in range(1, max + 1):
        row = []
        for j in range(1, max + 1):
            if [i, j] in rows or [j, i] in rows:
                row.append(1)
            else:
                row.append(0)
        matrix.append(row)
    return matrix


def min(a, b):
    return a if a < b else b


def as_adjencylist(rows):
    dict = {}
    for i in range(1, find_max(rows) + 1):
        dict[i] = []
    for row in rows:
        dict[row[0]].append(row[1])
        dict[row[1]].append(row[0])
    for key in dict.copy():
        if len(dict[key]) == 0:
            del dict[key]
    return dict


# sum of n nodes' degrees
def volume(_nodes):
    return len(_nodes)


# probability that one way step makes the node leave its community
def conductance(S, V):
    s_nodes = S.keys()

    count = 0
    for i in s_nodes:
        for key in V:
            if key not in s_nodes:
                count += V[key].count(i)

    volume_S = 0
    volume_S_V = 0
    for key in S:
        volume_S += volume(S[key])
    for key in V:
        if key not in s_nodes:
            volume_S_V += volume(V[key])
    return count / (min(volume_S_V, volume_S))


if __name__ == '__main__':
    graph = open_file("data/KarateClub.csv")
    cut = [[1, 2], [1, 3], [1, 4], [2, 1], [2, 4], [3, 1], [3, 4], [3, 8], [4, 2], [4, 3], [4, 1], [4, 5]]
    c = conductance(as_adjencylist(cut), as_adjencylist(graph))
    print(c)
