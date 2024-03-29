import os
import re

import matplotlib.patches
import matplotlib.pyplot as plt
import networkx as nx

a = "across"
d = "down"
directions = {'a' : 'across', 'd' : 'down'}


class findClue :
	def __init__(self, Clue: str, word_length: int, isSolved = False) :
		"""
		:rtype: findClue
		:type word_length: int
		:type Clue: str
		"""
		self.Clue = Clue
		self.Length = word_length
		self.isSolved = isSolved

	def solved(self, boolean) :
		self.isSolved = boolean

	def __str__(self) :
		return f"{self.Clue}, {self.Length}"


class Tile :
	def __init__(self, row, column, aclue = None, dclue = None, block = False) :
		"""
		:rtype: Tile
		:type block: bool
		:type dclue: findClue
		:type aclue: findClue
		:type column: int
		:type row: int
		"""
		self.value = (row, column)  # Position of the tile in the grid
		self.isBlock = block  # Is not a black tile at first
		self.char = ' '  # Initialises as empty
		self.AClue = aclue  # Clue going right from this tile : Is None if not the beginning of a
		# word across
		self.DClue = dclue  # Same as with across but with down instead
		boolean = self.isBlock
		temp_bool = not self.char == ' '
		if self.AClue is not None :
			temp_bool = temp_bool and self.AClue.isSolved
		if self.DClue is not None :
			temp_bool = temp_bool and self.DClue.isSolved
		boolean = boolean or temp_bool
		self.isSolved = boolean

	def modify(self, char = ' ', block = False, aclue = None, dclue = None) :
		"""
		:param dclue: optional : clue going down from the tile. Default is None
		:type dclue: findClue
		:param aclue: optional : clue going right from the tile. Default is None
		:type aclue: findClue
		:param char: optional : specifies the letter that is placed in the tile. Default is ''. If block is True
		should be false.
		:type char: str
		:param block: optional : specifies if a letter can be placed in the tile. Default is False.
		:type block: bool
		"""
		self.isBlock = self.isBlock or block or char == '#'
		if not self.isBlock :
			if not char == ' ' :
				self.char = char
			if aclue is not None :
				self.AClue = aclue
			if dclue is not None :
				self.DClue = dclue

	def solve(self, direction) :
		self.isSolved = True
		if direction == a :
			self.AClue.solved(True)
		else :
			self.DClue.solved(True)

	def __str__(self) :
		if self.isBlock :
			return "#"
		else :
			return self.char

	def __eq__(self, other) :
		# The implementation is partial as not all attributes will need to be checked here, and only grids
		# representing the same crossword will be compared
		if not isinstance(other, type(self)) : return NotImplemented
		return (self.char == other.char) and self.isBlock == other.isBlock

	def __ne__(self, other) :
		if not isinstance(other, type(self)) : return NotImplemented
		return not (self.char == other.char) or not (self.isBlock == other.isBlock)

	def __hash__(self) :
		return hash((self.char, self.isBlock, self.DClue.Clue, self.AClue.Clue))


class Grid :  # Representation of a grid
	def __init__(self,
			p,
			q,
			aclues_list,
			dclues_list,
			grid = None,
			weight = 1,
			name = None,
			words = None,
			QWeight = 0) :
		"""
		:param p: height of the grid
		:type p: int
		:param q: width of the grid
		:type q: int
		:param aclues_list: list of the across clues of the grid and the tile they start from, starting with the clue
		:type aclues_list: list[tuple[findClue, tuple[int, int]]]
		:param dclues_list: list of the down clues of the grid
		:type dclues_list: list[tuple[findClue, tuple[int, int]]]
		"""
		if words is None :
			words = []
		self.Size = (p, q)
		self.Grid = [[Tile(i, j) for j in range(q)] for i in range(p)] if grid is None else grid  # Initialises as empty
		self.AClues = {}
		self.DClues = {}
		self.Weight = weight
		self.Name = name
		self.Words = words if words is not None else []
		self.QWeight = QWeight

		for c in aclues_list :
			self.AClues[c[0]] = c[1]

		for c in dclues_list :
			self.DClues[c[0]] = c[1]

		for c in self.AClues :
			(i, j) = self.AClues[c]
			self.Grid[i][j].modify(aclue = c)

		for c in self.DClues :
			(i, j) = self.DClues[c]
			self.Grid[i][j].modify(dclue = c)

	def copy(self) :
		p, q = self.Size
		aclues_list = [(findClue(c.Clue, c.Length, c.isSolved), self.AClues[c]) for c in self.AClues]
		dclues_list = [((findClue(c.Clue, c.Length, c.isSolved)), self.DClues[c]) for c in self.DClues]
		g = Grid(p, q, aclues_list, dclues_list, weight = self.Weight, name = self.Name, words = self.Words.copy(),
				 QWeight = self.QWeight)
		for i in range(p) :
			for j in range(q) :
				tile = self.Grid[i][j]
				if tile.isBlock :
					g.Grid[i][j].modify(block = True)
				else :
					g.Grid[i][j].modify(char = tile.char)
		return g

	def isSolved(self) :
		p, q = self.Size
		for i in range(p) :
			for j in range(q) :
				if not self.Grid[i][j].isSolved :
					return False
		return True

	def __str__(self, clues: bool = True) :
		"""
		:param clues: specifies if the method should add the clues to the returned str
		:type clues: bool
		"""
		grid_string = f"{self.Size} \n"

		p, q = self.Size
		across_str = []
		down_str = []
		for i in range(p) :
			grid_string += "|"
			for j in range(q) :
				tile = self.Grid[i][j]
				grid_string += tile.__str__()
				if tile.AClue is not None :
					across_str.append((tile.AClue, i, j))
				if tile.DClue is not None :
					down_str.append((tile.DClue, i, j))
				if j != q - 1 :
					grid_string += "|"
				else :
					grid_string += "| \n"

		if clues :
			grid_string += f"Across Clues : \n"
			for c in across_str :
				grid_string += (c[0].__str__() + f", {c[1]}, {c[2]}\n")

			grid_string += f"Down Clues : \n"
			for c in down_str :
				grid_string += (c[0].__str__() + f", {c[1]}, {c[2]}\n")

		grid_string += f"{self.Weight}"
		return grid_string

	def is_complete(self) :
		r = True
		p, q = self.Size
		for row in range(p) :
			for column in range(q) :
				r = r and self.Grid[i][j].char != " "
		return r

	def fill_word(self, word: str, weight: float, direction: str, row: int, column: int) :
		"""
		:param weight: weight of the word to be added to the grid
		:type weight: float
		:param column: column number of the tile, starting from 0
		:type column: int
		:param row: row number of the tile, starting from 0.
		:type row: int
		:param word: word to be added
		:type word: str
		:param direction: specifies if the word should go right from the tile, or down
		:type direction: str
		"""
		wordLength = len(word)
		p, q = self.Size
		if direction == a :
			if wordLength != self.Grid[row][column].AClue.Length :
				return False
		else :
			if wordLength != self.Grid[row][column].DClue.Length :
				return False

		if self.is_complete() :
			if direction == a :
				for k in range(wordLength) :
					tile = self.Grid[row][column + k]
					if tile.isBlock :
						return False
					if not tile.char == ' ' :
						if tile.char != word[k] :
							return False
			for k in range(wordLength) :
				tile = self.Grid[row + k][column]
				if tile.isBlock :
					return False
				if not tile.char == ' ' :
					if tile.char != word[k] :
						return False
			return self.copy()

		if direction == a :
			for k in range(wordLength) :
				if column + k >= q :
					return False
				tile = self.Grid[row][column + k]
				if tile.isBlock :
					return False
				if not tile.char == ' ' :
					if tile.char != word[k] :
						return False

			grid_copy = self.copy()
			for k in range(wordLength) :
				tile = grid_copy.Grid[row][column + k]
				tile.modify(char = word[k])

		else :
			for k in range(wordLength) :
				if row + k >= p :
					return False
				tile = self.Grid[row + k][column]
				if tile.isBlock :
					return False
				if tile.char != ' ' :
					if tile.char != word[k] :
						return False

			grid_copy = self.copy()
			for k in range(wordLength) :
				tile = grid_copy.Grid[row + k][column]
				tile.modify(char = word[k])

		grid_copy.Weight *= weight
		c = grid_copy.Grid[row][column]
		c.solve(direction)
		grid_copy.Words.append(word)
		return grid_copy

	def __eq__(self, other) :
		if not isinstance(other, type(self)) : return NotImplemented
		return self.Grid == other.Grid

	def __ne__(self, other) :
		if not isinstance(other, type(self)) : return NotImplemented
		return self.Grid != other.Grid

	def __hash__(self) :
		return hash((tuple(self.Grid)))

	def __le__(self, other) :
		return self.Weight <= other.Weight

	def __ge__(self, other) :
		return self.Weight >= other.Weight

	def __lt__(self, other) :
		return self.Weight < other.Weight

	def __gt__(self, other) :
		return self.Weight > other.Weight

	def display(self, save_string) :
		p, q = self.Size
		fig = plt.figure()
		ax = fig.add_subplot()
		plt.xticks([_ for _ in range(q + 1)])
		plt.yticks([_ for _ in range(p + 1)])
		ax.invert_yaxis()
		clue_counter = 1

		for row in range(p) :
			for column in range(q) :
				tile = self.Grid[row][column]
				if tile.isBlock :
					ax.add_patch(matplotlib.patches.Rectangle((column, row), 1, 1, fill = False, hatch = '///',
															  facecolor = 'black'))
				else :
					char = tile.char
					if char != " " :
						ax.text(column + 4 / 11, row + 8 / 12, char.upper(), size = 30)

				if tile.AClue is not None or tile.DClue is not None :
					ax.text(column + 1 / 11, row + 9 / 40, f"{clue_counter}", size = 10)
					clue_counter += 1

		plt.grid(True, linewidth = 3.7, color = 'black')
		plt.savefig(save_string)

	def to_networkx_constraint_network(self) :
		p, q = self.Size
		clue_counter = 1
		G = nx.Graph()
		prev_clue_dict = {}

		for row in range(p) :
			for column in range(q) :
				tile = self.Grid[row][column]
				if tile.AClue is not None or tile.DClue is not None :

					if tile.AClue is not None :
						G.add_node(f"{clue_counter}D")

						tile_list = set([(row, column + k) for k in range(tile.AClue.Length)])
						k = len(tile_list)

						for node in [node for node in G.nodes if node != f"{clue_counter}A"] :
							node_tiles = prev_clue_dict[node]
							k2 = len(node_tiles)

							if len(tile_list.union(node_tiles)) < k + k2 :
								G.add_edge(node, f"{clue_counter}A")

						prev_clue_dict[f"{clue_counter}A"] = tile_list

					if tile.DClue is not None :
						G.add_node(f"{clue_counter}D")

						tile_list = set([(row + k, column) for k in range(tile.DClue.Length)])
						k = len(tile_list)

						for node in [node for node in G.nodes if node != f"{clue_counter}D"] :
							node_tiles = prev_clue_dict[node]
							k2 = len(node_tiles)

							if len(tile_list.union(node_tiles)) < k + k2 :
								G.add_edge(node, f"{clue_counter}D")

						prev_clue_dict[f"{clue_counter}D"] = tile_list

					clue_counter += 1

		return G


gridname = "grid_20_03_2023_MiniTWP"
directory = os.path.join(f"{gridname}")
grid_path = os.path.join(directory, "grid.txt")

with open(grid_path) as f :
	auqlue = f.readlines()
	l1 = auqlue[0]
	l1 = re.sub("\n", "", l1)
	l1 = l1.split("  ")
	alen = int(l1[0])
	dlen = int(l1[1])
	raw_aclues = auqlue[1 : 1 + alen]
	raw_dclues = auqlue[1 + alen : 1 + alen + dlen]

	aclues = []
	for a_clue in raw_aclues :
		a_clue = a_clue.split("  ")
		a_clue[-1] = re.sub("\n", "", a_clue[-1])
		clue, length = a_clue[0], int(a_clue[1])
		coords = (int(a_clue[2]), int(a_clue[3]))
		aclues.append((findClue(clue, length), coords))

	dclues = []
	for d_clue in raw_dclues :
		d_clue = d_clue.split("  ")
		d_clue[-1] = re.sub("\n", "", d_clue[-1])
		clue, length = d_clue[0], int(d_clue[1])
		coords = (int(d_clue[2]), int(d_clue[3]))
		dclues.append((findClue(clue, length), coords))

	lines = auqlue[1 + alen + dlen :]
	lines = [re.sub("\n", "", line) for line in lines]
	grid = Grid(len(lines), len(lines[0]), aclues_list = aclues, dclues_list = dclues, name = gridname, weight = 1,
				QWeight = 0)

	for i in range(len(lines)) :
		for j in range(len(lines[0])) :
			if lines[i][j] == '#' :
				grid.Grid[i][j].modify(block = True)
			elif lines[i][j] != '0' :
				grid.Grid[i][j].modify(char = lines[i][j])
