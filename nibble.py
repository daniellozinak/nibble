import random

import networkx
import networkx as nx
from operator import itemgetter
from enum import Enum


class Method(Enum):
    CONDUCTANCE = 1
    RATIO_CUT = 2
    NORMALIZED_CUT = 3


def pick_node(neighbours):
    random_index = random.randrange(0, len(neighbours))
    while neighbours[random_index] == 0:
        random_index = random.randrange(0, len(neighbours))
    return random_index


def copy_graph(g, used):
    g_copy = g.copy()
    for node in used:
        g_copy.remove_node(node)
    return g_copy


def random_walk(g, start=4, max_iterations=50, epsilon=10e-8, init_len=0):
    walk_mat = []

    # init random walk matrix
    for i in range(init_len + 1):
        temp = []
        for j in range(init_len + 1):
            temp.append(0)
        walk_mat.append(temp)

    current_node = start
    current_degree = g.degree(current_node) + 1
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
        dgr = g.degree(k)
        if dgr != 0:
            spprv.update({k: (v / dgr)})
        else:
            spprv.update({k: 0})
        pass
    return sorted(spprv.items(), key=itemgetter(1), reverse=True)


def min_cond_cut(g, dspprv, max_cutsize=0, method=Method.CONDUCTANCE):
    def get_cut(nbunch):
        sigma = 0.0
        for node in nbunch:
            for n in g.neighbors(node):
                if n not in nbunch:
                    sigma += 1.0
        return sigma

    def get_volume(nbunch):
        vol1 = vol2 = 0
        for degseq in dict(g.degree()).items():
            node, degree = degseq
            if node not in nbunch:
                vol2 += degree
            else:
                vol1 += degree
        return vol1, vol2

    def get_size(nbunch):
        return len(nbunch), abs(len(g.nodes) - len(nbunch))

    def conductance(nbunch):
        sigma = get_cut(nbunch)
        vol1, vol2 = get_volume(nbunch)

        result = 0
        min_volume = min(vol1, vol2)

        if min_volume > 0:
            result = sigma / min_volume

        return result

    def ratio_cut(nbunch):
        sigma = get_cut(nbunch)
        size1, size2 = get_size(nbunch)
        q1 = q2 = 0

        if size1 > 0:
            q1 = sigma / size1
        if size2 > 0:
            q2 = sigma / size2

        return q1 + q2

    def normalized_cut(nbunch):
        sigma = get_cut(nbunch)
        vol1, vol2 = get_volume(nbunch)
        q1 = q2 = 0

        if vol1 > 0:
            q1 = sigma / vol1
        if vol2 > 0:
            q2 = sigma / vol2

        return q1 + q2

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

        cndct = 0
        if method == Method.CONDUCTANCE:
            cndct = conductance(nbunch)
        elif method == Method.RATIO_CUT:
            cndct = ratio_cut(nbunch)
        elif method == Method.NORMALIZED_CUT:
            cndct = normalized_cut(nbunch)

        c = (k, cndct)
        # conductane of current cut size
        conductance_list.append(c)
        k += 1

    if len(conductance_list) == 0:
        return dspprv[0]

    return min(conductance_list, key=itemgetter(1))


## running the code ..
def loadGraph(gfile, delim="   "):
    return nx.read_edgelist(path=gfile, comments='#',
                            delimiter=delim, nodetype=int)


def vanilla_nibble(g, seed, max_cutsize=10, max_iterations=100, epsilon=10e-8, method=Method.CONDUCTANCE, used=None):
    g_copy = copy_graph(g, used)
    random_walk_result = random_walk(g_copy, seed, max_iterations, epsilon, len(g.nodes))
    random_walk_sorted = nibble_sorted(g_copy, node_dict=random_walk_result)
    best_community = min_cond_cut(g_copy, dspprv=random_walk_sorted, max_cutsize=max_cutsize, method=method)
    return best_community, random_walk_sorted


def pagerank_nibble(g, seed, max_cutsize=10, iters=100, epsilon=10e-8, method=Method.CONDUCTANCE, used=None,
                    alpha=0.85):
    g_copy = copy_graph(g, used)
    pagerank = ppr(g_copy, seed, alpha, epsilon, iters)
    sorted_pagerank = nibble_sorted(g_copy, node_dict=pagerank)
    best_community = min_cond_cut(g_copy, sorted_pagerank, max_cutsize, method=method)
    return best_community, sorted_pagerank


def get_graph_attribute(variant, seed, method, tries):
    return f"v={variant}_s={seed}_m={method}_part={tries}"


def mark_commmunity_nodes(graph, community, community_size, seed, epsilon, cutsize, iteration, variant, method,
                          used=None,
                          tries=0,
                          current_seed = -1):
    if used is None:
        used = set()
    values = {}
    for node in graph.nodes():
        if node in used:
            values[node] = "used"
        else:
            values[node] = "not-community"

    for i in range(community_size):
        node = community[i][0]
        rank = community[i][1]
        if rank < epsilon:
            break
        values[node] = "community"
    values[current_seed] = "seed"
    print(f"currently v={variant}_s={seed}_m={method}_part={tries}")
    networkx.set_node_attributes(graph, values, name=get_graph_attribute(variant, seed, method, tries))


g = loadGraph("data/KarateClub.csv", ";")


def pick_seed(g, used):
    copied = copy_graph(g, used)
    if len(copied.nodes) == 0:
        return -1
    max = list(copied.nodes)[0]
    for node in copied.nodes:
        if copied.degree(node) > copied.degree(max):
            max = node
    return max


cutsize = 15
iteration = 200
epsilon = 10e-8
seeds = [1, 34, 12]
methods = [Method.CONDUCTANCE, Method.RATIO_CUT, Method.NORMALIZED_CUT]

for seed in seeds:
    for method in methods:
        current_seed = seed

        # reset used after while loop
        current_iteration = 0
        used = set()
        while len(used) != len(g.nodes):
            vanilla_community, vanilla_result = vanilla_nibble(g, current_seed, cutsize, iteration, epsilon, method,
                                                               used)
            # pagerank_community, pagerank_result = pagerank_nibble(g, current_seed, cutsize, iteration, epsilon, method,
            #                                                       used)
            if vanilla_result[0][1] == 0:
                break

            mark_commmunity_nodes(g, vanilla_result, vanilla_community[0], seed, epsilon, cutsize, iteration, "v",
                                  method, used, current_iteration, current_seed)
            # mark_commmunity_nodes(g, pagerank_result, pagerank_community[0], seed, epsilon, cutsize, iteration, "pr",
            #                       method, used, current_iteration, current_seed)

            res = nx.get_node_attributes(g, get_graph_attribute("v", seed, method, current_iteration))
            for i in res:
                if res[i] == "seed" or res[i] == "community":
                    used.add(i)
            current_iteration += 1
            current_seed = pick_seed(g, used)

networkx.write_gexf(g, f"data/removeing_result_1.gexf")
