import random

import networkx
import networkx as nx
from operator import itemgetter


def pick_node(neighbours):
    random_index = random.randrange(0, len(neighbours))
    while neighbours[random_index] == 0:
        random_index = random.randrange(0, len(neighbours))
    return random_index


def random_walk(g, start=4, max_iterations=50, epsilon=10e-8):
    walk_mat = []
    node_list = list(g.nodes)

    # init random walk matrix
    for i in range(len(node_list) + 1):
        temp = []
        for j in range(len(node_list) + 1):
            temp.append(0)
        walk_mat.append(temp)

    current_node = start
    current_degree = g.degree(current_node) + 1
    # walks = [current_node]
    result = {}
    for _ in range(max_iterations):
        changed = False
        for node in (list(g.neighbors(current_node)) + [current_node]):
            if walk_mat[current_node][node] == 0:
                changed = True
                walk_mat[current_node][node] = 1 / current_degree
                result[current_node] = 1 / current_degree
        current_node = pick_node(walk_mat[current_node])
        current_degree *= (g.degree(current_node) + 1) * 0.4 if changed else 1
        # walks.append(current_node)
    # print("vannila walk")
    # print(walks)

    return result


def ppr(g, seed, alpha=0.85, epsilon=10e-8, iters=100):
    pref = {}
    T = [seed]
    for node in g.neighbors(seed):
        T.append(node)
    for node in g:
        if node in T:
            pref.update({node: (1.0 / len(T))})
        else:
            pref.update({node: 0.0})

    return nx.pagerank(g, alpha=alpha, personalization=pref, max_iter=iters,
                       tol=epsilon)


def nibble_sorted(g, node_dict):
    spprv = {}
    for item in node_dict.items():
        k, v = item
        spprv.update({k: (v / g.degree(k))})
        pass
    return sorted(spprv.items(), key=itemgetter(1), reverse=True)


def min_cond_cut(g, dspprv, max_cutsize=0):
    def conductance(nbunch):
        sigma = 0.0
        vol1 = vol2 = 0
        for node in nbunch:
            for n in g.neighbors(node):
                if n not in nbunch:
                    sigma += 1.0

        for degseq in dict(g.degree()).items():
            node, degree = degseq
            if node not in nbunch:
                vol2 += degree
            else:
                vol1 += degree

        result = 0
        min_volume = min(vol1, vol2)

        if min_volume > 0:
            result = sigma / min_volume

        return result

    k = 1
    conductance_list = []

    if max_cutsize < 1 or max_cutsize > len(dspprv):
        # cutsize could be as big as the graph itself
        limit = (len(dspprv))
    else:
        # maximum size of the cut with minimum conductance
        limit = max_cutsize

    while k < limit:
        nbunch = []
        for i in range(0, k):
            nbunch.append(dspprv[i][0])

        c = (k, conductance(nbunch))
        # conductane of current cut size
        # print (c)
        conductance_list.append(c)
        k += 1

    return min(conductance_list, key=itemgetter(1))


## running the code ..
def loadGraph(gfile, delim="   "):
    return nx.read_edgelist(path=gfile, comments='#',
                            delimiter=delim, nodetype=int)


def vanilla_nibble(g, seed, max_cutsize=10, max_iterations=100, epsilon=10e-8):
    random_walk_result = random_walk(g, seed, max_iterations, epsilon)
    random_walk_sorted = nibble_sorted(g, node_dict=random_walk_result)
    best_community = min_cond_cut(g, dspprv=random_walk_sorted, max_cutsize=max_cutsize)
    return best_community, random_walk_sorted


def pagerank_nibble(g, seed, max_cutsize=10, iters=100, epsilon=10e-8, alpha=0.85):
    pagerank = ppr(g, seed, alpha, epsilon, iters)
    sorted_pagerank = nibble_sorted(g, node_dict=pagerank)
    best_community = min_cond_cut(g, sorted_pagerank, max_cutsize)
    return best_community, sorted_pagerank


def mark_commmunity_nodes(graph, community, community_size, seed, epsilon, cutsize, iteration, variant):
    values = {}
    for node in graph.nodes():
        values[node] = "not-community"

    for i in range(community_size):
        node = community[i][0]
        rank = community[i][1]
        if rank < epsilon:
            break
        values[node] = "community"
    values[seed] = "seed"
    print(f"currently v={variant}_cs={cutsize}_e={epsilon}_i={iteration}")
    networkx.set_node_attributes(graph, values, name=f"v={variant}_s={seed}_cs={cutsize}_e={epsilon}_i={iteration}")


g = loadGraph("data/KarateClub.csv", ";")
seed = 4
cutsizes = [10, 15]
epsilons = [10e-5, 10e-8, 10e-11]
iterations = [100, 200]

for cutsize in cutsizes:
    for epsilon in epsilons:
        for iteration in iterations:
            vanilla_community, vanilla_result = vanilla_nibble(g, seed, cutsize, iteration, epsilon)
            pagerank_community, pagerank_result = pagerank_nibble(g, seed, cutsize, iteration, epsilon)

            mark_commmunity_nodes(g, pagerank_result, pagerank_community[0], seed, epsilon, cutsize, iteration, "pr")
            mark_commmunity_nodes(g, vanilla_result, vanilla_community[0], seed, epsilon, cutsize, iteration, "v")

networkx.write_gexf(g, f"data/allinone.gexf")
