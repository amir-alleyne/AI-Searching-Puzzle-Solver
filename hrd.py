from copy import deepcopy
from heapq import heappush, heappop
import time
import argparse
import sys

# ====================================================================================

char_goal = '1'
char_single = '2'


class Piece:
    """
    This represents a piece on the Hua Rong Dao puzzle.
    """

    def __init__(self, is_goal, is_single, coord_x, coord_y, orientation):
        """
        :param is_goal: True if the piece is the goal piece and False otherwise.
        :type is_goal: bool
        :param is_single: True if this piece is a 1x1 piece and False otherwise.
        :type is_single: bool
        :param coord_x: The x coordinate of the top left corner of the piece.
        :type coord_x: int
        :param coord_y: The y coordinate of the top left corner of the piece.
        :type coord_y: int
        :param orientation: The orientation of the piece (one of 'h' or 'v')
            if the piece is a 1x2 piece. Otherwise, this is None
        :type orientation: str
        """

        self.is_goal = is_goal
        self.is_single = is_single
        self.coord_x = coord_x
        self.coord_y = coord_y
        self.orientation = orientation

    def __repr__(self):
        return '{} {} {} {} {}'.format(self.is_goal, self.is_single, \
                                       self.coord_x, self.coord_y, self.orientation)


class Board:
    """
    Board class for setting up the playing board.
    """

    def __init__(self, pieces):
        """
        :param pieces: The list of Pieces
        :type pieces: List[Piece]
        """

        self.width = 4
        self.height = 5

        self.pieces = pieces

        # self.grid is a 2-d (size * size) array automatically generated
        # using the information on the pieces when a board is being created.
        # A grid contains the symbol for representing the pieces on the board.
        self.grid = []
        self.__construct_grid()

    def __construct_grid(self):
        """
        Called in __init__ to set up a 2-d grid based on the piece location information.

        """

        for i in range(self.height):
            line = []
            for j in range(self.width):
                line.append('.')
            self.grid.append(line)

        for piece in self.pieces:
            if piece.is_goal:
                self.grid[piece.coord_y][piece.coord_x] = char_goal
                self.grid[piece.coord_y][piece.coord_x + 1] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x] = char_goal
                self.grid[piece.coord_y + 1][piece.coord_x + 1] = char_goal
            elif piece.is_single:
                self.grid[piece.coord_y][piece.coord_x] = char_single
            else:
                if piece.orientation == 'h':
                    self.grid[piece.coord_y][piece.coord_x] = '<'
                    self.grid[piece.coord_y][piece.coord_x + 1] = '>'
                elif piece.orientation == 'v':
                    self.grid[piece.coord_y][piece.coord_x] = '^'
                    self.grid[piece.coord_y + 1][piece.coord_x] = 'v'

    def display(self):
        """
        Print out the current board.
        """
        for i, line in enumerate(self.grid):
            for ch in line:
                print(ch, end='')
            print()


class State:
    """
    State class wrapping a Board with some extra current state information.
    Note that State and Board are different. Board has the locations of the pieces.
    State has a Board and some extra information that is relevant to the search:
    heuristic function, f value, current depth and parent.
    """

    def __init__(self, board, f,depth, parent=None):
        """
        :param board: The board of the state.
        :type board: Board
        :param f: The f value of current state.
        :type f: int
        :param depth: The depth of current state in the search tree.
        :type depth: int
        :param parent: The parent of current state.
        :type parent: Optional[State]
        """
        self.board = board
        self.f = f
        self.depth = depth
        self.parent = parent
        self.id = hash(board)  # The id for breaking ties.

    def __lt__(self, other):
        return self.f < other.f


def read_from_file(filename):
    """
    Load initial board from a given file.

    :param filename: The name of the given file.
    :type filename: str
    :return: A loaded board
    :rtype: Board
    """

    puzzle_file = open(filename, "r")

    line_index = 0
    pieces = []
    g_found = False

    for line in puzzle_file:

        for x, ch in enumerate(line):

            if ch == '^':  # found vertical piece
                pieces.append(Piece(False, False, x, line_index, 'v'))
            elif ch == '<':  # found horizontal piece
                pieces.append(Piece(False, False, x, line_index, 'h'))
            elif ch == char_single:
                pieces.append(Piece(False, True, x, line_index, None))
            elif ch == char_goal:
                if g_found == False:
                    pieces.append(Piece(True, False, x, line_index, None))
                    g_found = True
        line_index += 1

    puzzle_file.close()

    board = Board(pieces)

    return board


def goal_test(state):
    """
    Returns whether given state is at the goal state
    TODO: get the board and iterate through the pieces. Check if the goal piece is
    at coord (goalx,goaly)

    Assumptions: the board is 0 based and the origin is the top left hand corner
    """
    for piece in state.board.pieces:
        if piece.is_goal and piece.coord_x == 1 and piece.coord_y == 3:
            return True
    return False


def calculate_man(piece):
    """
    Given a state, calculate the manhattan distance of the goal piece
    :param state:
    :return:
    """
    return abs(1 - piece[0]) + abs(3 - piece[1])


def get_goal_piece(pieces):
    for piece in pieces:
        if piece.is_goal:
            return piece


def move_piece(stated, piece, new_loc):
    """
    Takes in a state and a single piece and moves it to the specified location
    """
    pieces = deepcopy(stated.board.pieces)

    for p in pieces:
        if piece.coord_x == p.coord_x and p.coord_y == piece.coord_y:
            p.coord_x = new_loc[0]
            p.coord_y = new_loc[1]
            break

    goalp = get_goal_piece(pieces)
    # assert goalp.is_goal
    new_f = stated.depth + 1 + calculate_man((goalp.coord_x, goalp.coord_y))
    new_s = State(Board(pieces), new_f, stated.depth + 1, stated)
    return new_s


def possible_goal_move(state, piece, empty):
    """
    Takes in the current state of a board and returns the new board after moving the goal piece

    Logistics of move:
    for goal piece to move, it has to to be adjacent to both empty space : either empty spaces at
    LEFT - (xcoord-1,ycoord) and (xcoord-1,ycoord+1) OR
     UP - (xcoord,ycoord-1) and (xcoord+1,ycoord-1) OR
     DOWN - (xcoord,ycoord+2) and (xcoord+1,ycoord+2) OR
     RIGHT - (xcoord+2,ycoord) and (xcoord+2,ycoord+1)
    """
    e1 = empty[0]
    e2 = empty[1]
    new_boards = []
    # move up
    if (e1[0] == piece.coord_x and e1[1] == piece.coord_y - 1) and \
            (e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y - 1):
        new_boards.append(move_piece(state, piece, e1))
    if (e2[0] == piece.coord_x and e2[1] == piece.coord_y - 1) and \
            (e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y - 1):
        new_boards.append(move_piece(state, piece, e2))
    # move down
    if (e1[0] == piece.coord_x and e1[1] == piece.coord_y + 2) and \
            (e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y + 2):
        new_boards.append(move_piece(state, piece, (e1[0], e1[1] - 1)))
    if (e2[0] == piece.coord_x and e2[1] == piece.coord_y + 2) and \
            (e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y + 2):
        new_boards.append(move_piece(state, piece, (e2[0], e2[1] - 1)))

    # move right
    if (e1[0] == piece.coord_x + 2 and e1[1] == piece.coord_y) and \
            (e2[0] == piece.coord_x + 2 and e2[1] == piece.coord_y + 1):
        new_boards.append(move_piece(state, piece, (e1[0] - 1, e1[1])))
    if (e2[0] == piece.coord_x + 2 and e2[1] == piece.coord_y) and \
            (e1[0] == piece.coord_x + 2 and e1[1] == piece.coord_y + 1):
        new_boards.append(move_piece(state, piece, (e2[0] - 1, e2[1])))

    # move left
    if (e1[0] == piece.coord_x - 1 and e1[1] == piece.coord_y) and \
            (e2[0] == piece.coord_x - 1 and e2[1] == piece.coord_y + 1):
        new_boards.append(move_piece(state, piece, e1))
    if (e2[0] == piece.coord_x - 1 and e2[1] == piece.coord_y) and \
            (e1[0] == piece.coord_x + - 1 and e1[1] == piece.coord_y + 1):
        new_boards.append(move_piece(state, piece, e2))

    return new_boards


def possible_single_move(state, piece, empty):
    """
    Return a list of possible boards that 1 single piece can take
    """

    e1 = empty[0]
    e2 = empty[1]
    new_boards = []
    # move up
    if e1[0] == piece.coord_x and e1[1] == piece.coord_y - 1:
        new_boards.append(move_piece(state, piece, e1))
    if e2[0] == piece.coord_x and e2[1] == piece.coord_y - 1:
        new_boards.append(move_piece(state, piece, e2))
    # move left
    if e1[0] == piece.coord_x - 1 and e1[1] == piece.coord_y:
        new_boards.append(move_piece(state, piece, e1))
    if e2[0] == piece.coord_x - 1 and e2[1] == piece.coord_y:
        new_boards.append(move_piece(state, piece, e2))
        # move right
    if e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y:
        new_boards.append(move_piece(state, piece, e1))
    if e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y:
        new_boards.append(move_piece(state, piece, e2))
        # move down
    if e1[0] == piece.coord_x and e1[1] - 1 == piece.coord_y:
        new_boards.append(move_piece(state, piece, e1))
    if e2[0] == piece.coord_x and e2[1] - 1 == piece.coord_y:
        new_boards.append(move_piece(state, piece, e2))

    return new_boards


def possible_1x2_move(state, piece, empty):
    """
    Returns a list of possible moves for the 1x2 pieces

    1X2 pieces can move if:

    Horizontal orientation:
    if empty spaces are to its left - e1[0] at x - 1, e1[1] at y, e2[0] at x - 2, e2[1] at y or vice versa
    if empty spaces are to its right - e1[0] at x+2, e1[1] at y, e2[0] at x + 3, e2[1] at y or vice versa
    if empty spaces are above it - e1[0] at x, e1[1] at y - 1, e2[0] at x + 1, e2[1] at y- 1 or vice versa
    if empty spaces are below it - e1[0] at x, e1[1] at y+ 1, e2[0] at x + 1, e2[1] at y+ 1 or vice versa

    Vertical orientation:
    if empty spaces are to its left - e1[0] at x - 1, e1[1] at y, e2[0] at x - 1, e2[1] at y + 1 or vice versa
    if empty spaces are to its right - e1[0] at x+1, e1[1] at y, e2[0] at x + 1, e2[1] at y + 1 or vice versa
    if empty spaces are above it - e1[0] at x, e1[1] at y - 1, e2[0] at x , e2[1] at y- 2 or vice versa
    if empty spaces are below it - e1[0] at x, e1[1] at y+ 2, e2[0] at x , e2[1] at y+ 3 or vice versa
    """

    e1 = empty[0]
    e2 = empty[1]
    new_boards = []
    # move up
    if piece.orientation == 'v':
        if e2[0] == piece.coord_x and e2[1] == piece.coord_y - 1:
            new_boards.append(move_piece(state, piece, e2))
        if e1[0] == piece.coord_x and e1[1] == piece.coord_y - 1:
            new_boards.append(move_piece(state, piece, e1))

        # move left
        if ((e2[0] == piece.coord_x - 1 and e2[1] == piece.coord_y) and \
                (e1[0] == piece.coord_x - 1 and e1[1] == piece.coord_y + 1)):
            new_boards.append(move_piece(state, piece, e2))
        if ((e1[0] == piece.coord_x - 1 and e1[1] == piece.coord_y) and \
                (e2[0] == piece.coord_x - 1 and e2[1] == piece.coord_y + 1)):
            new_boards.append(move_piece(state, piece, e1))

        # move right
        if ((e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y) and \
                (e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y + 1)):
            new_boards.append(move_piece(state, piece, e2))
        if ((e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y) and \
                (e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y + 1)):
            new_boards.append(move_piece(state, piece, e1))

        # move down
        if e2[0] == piece.coord_x and e2[1] == piece.coord_y + 2:
            new_boards.append(move_piece(state, piece, (e2[0], e2[1] - 1)))
        if e1[0] == piece.coord_x and e1[1] == piece.coord_y + 2:
            new_boards.append(move_piece(state, piece, (e1[0], e1[1] - 1)))
    else:
        # move left
        if e2[0] == piece.coord_x - 1 and e2[1] == piece.coord_y:
            new_boards.append(move_piece(state, piece, e2))
        elif e1[0] == piece.coord_x - 1 and e1[1] == piece.coord_y:
            new_boards.append(move_piece(state, piece, e1))

        # move up
        if ((e2[0] == piece.coord_x and e2[1] == piece.coord_y - 1) and \
                (e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y - 1)):
            new_boards.append(move_piece(state, piece, e2))
        if ((e1[0] == piece.coord_x and e1[1] == piece.coord_y - 1) and \
                (e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y - 1)):
            new_boards.append(move_piece(state, piece, e1))

        # move down
        if ((e2[0] == piece.coord_x and e2[1] == piece.coord_y + 1) and \
                (e1[0] == piece.coord_x + 1 and e1[1] == piece.coord_y + 1)):
            new_boards.append(move_piece(state, piece, e2))
        if ((e1[0] == piece.coord_x and e1[1] == piece.coord_y + 1) and \
                (e2[0] == piece.coord_x + 1 and e2[1] == piece.coord_y + 1)):
            new_boards.append(move_piece(state, piece, e1))

        # move right
        if e2[0] == piece.coord_x + 2 and e2[1] == piece.coord_y:
            new_boards.append(move_piece(state, piece, (e2[0] - 1, e2[1])))
        elif e1[0] == piece.coord_x + 2 and e1[1] == piece.coord_y:
            new_boards.append(move_piece(state, piece, (e1[0] - 1, e1[1])))
    return new_boards


def get_empty_slots(board):
    """
    Return the positions of the empty slots in a list of lists of length 2 each containing [x,y] of each
    empty slot

    """
    possible = {(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (1, 1), (1, 0), (1, 2), (1, 3), (1, 4),
                (2, 0), (2, 1), (2, 2), (2, 3), (2, 4),
                (3, 1), (3, 2), (3, 3), (3, 0), (3, 4)}
    actual = set()
    for piece in board.pieces:
        actual.add((piece.coord_x, piece.coord_y))
        if piece.is_goal:
            actual.add((piece.coord_x + 1, piece.coord_y))
            actual.add((piece.coord_x, piece.coord_y + 1))
            actual.add((piece.coord_x + 1, piece.coord_y + 1))
        if piece.orientation == 'h':
            actual.add((piece.coord_x + 1, piece.coord_y))
        if piece.orientation == 'v':
            actual.add((piece.coord_x, piece.coord_y + 1))
    slots = list(possible.difference(actual))
    # assert len(slots) == 2
    return slots


def gen_successors(state):
    """
    Generate the successors for the given state
    TODO:  for each piece generate all the possible next moves
    # return an array of possible boards resulting from a specific move
    """
    empty = get_empty_slots(state.board)  # list of two coords
    successors = []

    # iterate through the pieces on the current board
    for piece in state.board.pieces:
        # for each piece, check whether they are adjacent to '.' based on their side
        if piece.is_goal:
            successors.extend(possible_goal_move(state, piece, empty))
        elif piece.is_single:
            successors.extend(possible_single_move(state, piece, empty))
        elif piece.orientation is not None:
            successors.extend(possible_1x2_move(state, piece, empty))
    return successors


def get_soln(goal_state):
    """
    Function that when given a goal state, returns the path taken to reach this state
    """
    path = []

    while goal_state:
        path.append(goal_state)
        goal_state = goal_state.parent
    return path[::-1]


def get_rep(board):
    """
    Takes in a board and returns the string representation for it
    :param board:
    :return: a string representation of the board
    """
    str_rep = ''
    for i, line in enumerate(board.grid):
        for ch in line:
            str_rep += ch
    return str_rep


def dfs(state):
    frontier = [state]
    explored = set()

    while len(frontier) != 0:
        curr = frontier.pop()
        str_rep = get_rep(curr.board)
        if str_rep not in explored:
            explored.add(str_rep)
            if goal_test(curr):
                return get_soln(curr)
            frontier.extend(gen_successors(curr))

    print("No solution")


def a_star(state):
    frontier = [state]
    # heappush heappop
    explored = set()

    while len(frontier) != 0:
        curr = heappop(frontier)
        str_rep = get_rep(curr.board)
        if not str_rep in explored:
            explored.add(str_rep)
            if goal_test(curr):
                return get_soln(curr)
            successors = gen_successors(curr)
            for x in successors:
                heappush(frontier, x)

    print("No solution")


def write_board(board, file):
    f = open(file, 'a')
    for i, line in enumerate(board.grid):
        for ch in line:
            f.write(ch)
        f.write('\n')
    f.write('\n')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inputfile",
        type=str,
        required=True,
        help="The input file that contains the puzzle."
    )
    parser.add_argument(
        "--outputfile",
        type=str,
        required=True,
        help="The output file that contains the solution."
    )
    parser.add_argument(
        "--algo",
        type=str,
        required=True,
        choices=['astar', 'dfs'],
        help="The searching algorithm."
    )

    args = parser.parse_args()
    print(args.outputfile)
    # read the board from the file
    board = read_from_file(args.inputfile)
    # board.display()
    # print(get_rep(board))
    state = State(board, 0, 0, 0)
    print(args.algo)
    if args.algo == 'dfs':
        soln = dfs(state)
        dfs_file = open(args.outputfile, 'w')
        for s in soln:
            write_board(s.board, args.outputfile)
        dfs_file.close()
    else:
        soln2 = a_star(state)
        print(len(soln2)-1)
        astar_file = open(args.outputfile, 'w')
        for s in soln2:
            # s.board.display()
            write_board(s.board, args.outputfile)
        astar_file.close()


