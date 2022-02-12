# Python-Tank-Game
![alt text](https://github.com/mspardinas/Python-Tank-Game/blob/master/readme-images/tank-game.png)

A PyGame-based tank game similar to the old game Battle City (NES) created using Python for CS 150, Programming Languages, in UPD. This project was developed by Timothy Magno and I, Miguel Pardiñas, as our final project for CS 150.

The pair was provided a template code (original template code is in the folder *unchanged files from template*) and was instructed to modify it to add: (1) four additional tank types using inheritance and (2) the functionality of each tank to drop/place bombs in the field. For this project, the pair used Python and PyGame was used as it is a Python library used to create graphical games.

## Dependencies
Make sure to have the latest version of Python installed, and install PyGame afterwards.
```
pip install pygame
```
To verify installation of PyGame:
```
python -m pygame.examples.aliens
```

## Tank Game
- The provided code is a two-player game based on Battle City (NES) or general tank games on a 1000x800 pixel map.
- Each player controls a tank which can move in four (4) directions, fire its own bullets, and drop or place bombs.
- Each tank has 10 hit/health points or HP.
- A bullet deals 1 damage and a bomb deals 3 damage.
- Walls (red blocks) have a health of 3 and block a tank's movement.
- Trees (green blocks) cannot be damaged, hide or conceal a tank's location, and do not block a tank's movement.
- Note that terrain elements (walls and trees) are generated randomly.

## Game Instructions / Controls
- Player 1: *Arrow Up* (move up), *Arrow Left* (move left), *Arrow Down* (move down), *Arrow Right* (move right), *.* or *period* (fire bullets), and *,* or *comma* (drop/place bomb).
- Player 2: *W* (move up), *A* (move left), *S* (move down), *D* (move right), *space* (fire bullets), and *C* (drop/place bomb).

## Installation / Running
Download necessary Python files and while in the respective directory, run by typing:
```
python game.py
```
*Note that the game runs indefinitely, it can only be stopped by terminating it in the CMD*

![alt text](https://github.com/mspardinas/Python-Tank-Game/blob/master/readme-images/python-tanks-demo.gif)

