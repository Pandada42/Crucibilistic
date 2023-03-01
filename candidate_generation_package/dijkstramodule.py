import heapq
import re
import dill
import os
import numpy as np


class Vertex :
    def __init__(self, key) :
        """
        :type key: depends on your mood UwU
        """
        self.key = key
        self.neighbours = {}

    def oriented_add_neighbour(self, neighbour, weight = None) :
        self.neighbours[neighbour] = weight

    def unoriented_add_neighbour(self, neighbour, weight = None) :
        """
        :param neighbour: Another vertex that is connected to this one in the graph.
        :type neighbour: Vertex
        :type weight: Technically anything that can be compared
        """
        self.oriented_add_neighbour(neighbour, weight)
        neighbour.oriented_add_neighbour(self, weight)

    def get_connections(self) :
        return self.neighbours.keys()

    def degree(self) :
        return len(self.neighbours.keys())

    def get_weight(self, neighbour) :
        """
        :type neighbour: Vertex
        """
        return self.neighbours.get(neighbour, None)

    def oriented_modify_weight(self, neighbour, new_weight) :
        self.neighbours[neighbour] = new_weight

    def unoriented_modify_weight(self, neighbour, new_weight) :
        self.neighbours[neighbour] = new_weight
        neighbour.neighbours[self] = new_weight

    def __str__(self) :
        return '{} neighbours : {}'.format(self.key, [x.key for x in self.neighbours])


class Graph :
    def __init__(self) :
        self.vertices = {}

    def add_vertex(self, vertex) :
        if vertex.key in self.vertices :
            return
        self.vertices[vertex.key] = vertex

    def get_vertex(self, key) :
        return self.vertices.get(key, None)

    def __contains__(self, key) :
        return key in self.vertices

    def oriented_add_edge(self, from_key, to_key, weight = None) :
        if not self.__contains__(from_key) :
            self.add_vertex(Vertex(from_key))
        if not self.__contains__(to_key) :
            self.add_vertex(Vertex(to_key))
        self.vertices[from_key].oriented_add_neighbour(self.vertices[to_key], weight)

    def unoriented_add_edge(self, from_key, to_key, weight = None) :
        if not self.__contains__(from_key) :
            self.add_vertex(Vertex(from_key))
        if not self.__contains__(to_key) :
            self.add_vertex(Vertex(to_key))
        self.vertices[from_key].unoriented_add_neighbour(self.vertices[to_key], weight)

    def get_edge(self, from_key, to_key) :
        return self.vertices.get(from_key, None).get_weight(self.vertices.get(to_key, None))

    def oriented_modify_edge(self, from_key, to_key, new_weight) :
        return self.vertices.get(from_key, None).oriented_modify_weight(self.vertices.get(to_key, None), new_weight)

    def unoriented_modify_edge(self, from_key, to_key, new_weight) :
        return self.vertices.get(from_key, None).unoriented_modify_weight(self.vertices.get(to_key, None), new_weight)

    def get_vertices(self) :
        return [self.vertices[k] for k in self.vertices.keys()]

    def __iter__(self) :
        return iter(self.vertices.values())

    def __str__(self) :
        for u in self :
            for v in u.get_connections() :
                print("{} -> {} : {}".format(u.key, v.key, self.get_edge(u.key, v.key)))


def words(db) :
    """
    :param db: Database containing documents
    :type db: list[str]
    :return: Dictionary containing the number of occurences of a word and the documents it appears in.
    :rtype: dict[tuple[int, list[list[str]]]
    """
    w = {}
    for i in db :
        c = i.split(" ")
        c[-1] = re.sub(r"\n", "", c[-1])  # If the string still has its newline operator, deletes it.
        for j in c :
            j_ = j.lower()
            if j_ in w :
                w[j_][0] += 1
                w[j_][1].append(c)
            else :
                w[j_] = [1, [c]]
    return w


def graph_creator(db: list[str], db_name: str) :
    """
    :param db_name: name of the file to save in
    :type db_name: str
    :param db: Database containing all documents
    :type db: list[str]
    :return: Graph linking a document to its terms
    with weight number of occurrences and a graph linking two words with weight tf idf
    :rtype: Graph, Graph
    """

    Omega = Graph()
    # Creation of a not oriented graph linking a document d in db to all the words w in it with
    # weight |{occurrences of w in d}|
    Words = Graph()
    # Creation of a not oriented graph linking two words u and v with weight |documents containing both u and v|
    for i in db :
        i = i.lower()
        i = re.sub("[^\w\s:À-ÿ:&]", "", i)
        Omega.add_vertex(Vertex(i))
        words_i = i.split(" ")
        words_i[-1] = re.sub(r"\n", "", words_i[-1])

        for word in words_i :
            word = re.sub("[^\w\s:À-ÿ:&]", "", word)
            x_w = Omega.get_edge(i, word)
            if x_w is None :
                Omega.unoriented_add_edge(i, word, 1)
            else :
                Omega.unoriented_modify_edge(i, word, x_w + 1)
            Words.add_vertex(Vertex(word))
            for j in words_i :
                if j != word :
                    x_w_j = Words.get_edge(word, j)
                    if x_w_j is None :
                        Words.unoriented_add_edge(word, j, 1)
                    else :
                        Words.unoriented_modify_edge(word, j, x_w_j + 1)
    # Words.__str__()

    Final = Graph()
    # Creation of an oriented graph creating the edge (u,v)
    # with weight log(|documents containing u|)-log(|documents in d containing u and v|)
    for vertex in Words.get_vertices() :
        for neighbour in vertex.neighbours :
            vertex_key, neighbour_key = re.sub("[^\w\s:À-ÿ:&]", "", vertex.key), re.sub("[^\w\s:À-ÿ:&]", "", neighbour.key)
            number_of_common_documents_vertex_neighbour = Words.get_edge(vertex_key, neighbour_key) / 2
            number_of_documents_vertex = len(Omega.get_vertex(vertex_key).get_connections())
            weight_vertex_neighbour = -np.log(number_of_common_documents_vertex_neighbour / number_of_documents_vertex)
            Final.oriented_add_edge(vertex_key, neighbour_key, weight_vertex_neighbour)
    # |documents containing u| is the degree of u in Omega, which is not oriented
    # |documents containing t and u| is the weight of (t,u) in Words, which is not oriented

    """with open(f"{db_name}_omega_graph.txt", "wb") as f :
        dill.dump(Omega, file = f)

    with open(f"{db_name}_DB_graph.txt", "wb") as f :
        dill.dump(Final, file = f)"""

    # Need to find a better way to make these graphs persistent.

    return Omega, Final


def dijkstra(graph: Graph, vertex) :
    if graph.get_vertex(vertex) is None :
        return f"{vertex} is not in G"

    priority_queue = []
    distance = {}
    for v in graph.vertices.keys() :
        distance[v] = float("inf")

    heapq.heappush(priority_queue, (0, vertex))

    while priority_queue :
        dist, current_vertex = heapq.heappop(priority_queue)
        if distance[current_vertex] == float("inf") :
            distance[current_vertex] = dist
            for neighbour in graph.get_vertex(current_vertex).neighbours :
                next_vertex = neighbour.key
                heapq.heappush(priority_queue, (dist + graph.get_edge(current_vertex, next_vertex), next_vertex))

    return distance


"""def weight(db : list[str], clue : str, word : str):
    Omega, DB = graph_creator(db)
    terms = clue.split(" ")
    r = 0
    for i in terms :
        distance = dijkstra(DB, i)
        r += -np.log(Omega.get_vertex(i).degree) - distance[word]
    return r"""

# Added a list of undesirable_words since they don't come often in a grid and they flood the answers of this module.
undesirable_words = ["and", "or", "for", "to", "than", "on", "at", "of", "from", "into"]


def dijkstra_gen(database: list[str], clue: str, length: int, db_name: str) :
    """if os.path.isfile(f"{db_name}_DB_graph.txt") and os.path.isfile(f"{db_name}_omega_graph.txt") :
        with open(f"{db_name}_DB_graph.txt", "rb") as f :
            DB = dill.load(f)
        with open(f"{db_name}_omega_graph.txt", "rb") as f :
            Omega = dill.load(f)
    else :"""
    Omega, DB = graph_creator(database, db_name)

    clue_terms = clue.lower().split(" ")
    distance_to_neighbours = {}
    for term in clue_terms :
        term = re.sub("[^\w\s:À-ÿ:&]", "", term)
        distance_to_neighbours[term] = dijkstra(DB, term)

    distances = {}
    for w in DB.get_vertices() :
        w_key = re.sub("[^\w\s:À-ÿ:&]", "", w.key)
        if w_key not in undesirable_words and len(w_key) == length :
            d = 0
            for term in clue_terms :
                d += distance_to_neighbours[term].get(w_key, 0)
            distances[w_key] = d

    def sorting_function(t) :
        return t[1]

    res = sorted([(u, 1 / (distances[u] + 1)) for u in distances.keys() if distances[u] != float("inf")],
                 key = sorting_function, reverse = False)
    # The sorted list needs to be in ascending order, as we want the words that are closest to the clue

    return res

# Change the way distances between documents are calculated so that two similar documents produce the same
# list of candidates ? Calculate the distance between two documents answers included and calculate the distance
# between the clue without answer and the rest ? Calculate the distance between two clues ?

# Nothing worrying tho, results to be expected according to Keim, Littman, Shazeer
