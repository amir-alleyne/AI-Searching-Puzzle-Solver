# HuaRongDao-Puzzle-Solver
HuaRongDao puzzle solver AI that uses searching strategies (Astar search and Depth First Search) and pruning to find an optimal solution (smallest number of moves)

# INFO ABOUT GAME

The puzzle board is four spaces wide and five spaces tall.There are four kinds of pieces:

One 2x2 piece.
Five 1x2 pieces. Each 1x2 piece can be horizontal or vertical.
Four 1x1 pieces.

The goal is to move the pieces until the 2x2 piece is above the bottom opening (i.e. helping Cao Cao escape through the Hua Rong Dao/Pass). You may move each piece horizontally or vertically only into an available space. You are not allowed to rotate any piece or move it diagonally.

# HOW TO RUN PROGRAM 
Cd to directory with code and run the below in the terminal :
    python3 hrd.py --algo astar --inputfile brd.txt --outputfile solution.txt  
    python3 hrd.py --algo dfs --inputfile brd.txt --outputfile solution.txt
    
    
# OUTPUT FILE -
This shows the sequence of moves to solve the puzzle in the smallest number fo moves. 
