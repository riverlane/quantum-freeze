## The Quantum Freeze
Safely navigate your penguin across a frozen lake avoiding the hidden holes! You can make classical moves from one square to the next but you can also make a quantum move - splitting your penguin into a superposition of states. Explore how quantum superposition can help solve the levels whilst constructing a circuit to run on Rigetti’s quantum computer.

## Installation on QCS

0. (for Linux) SSH into your QCS box using `ssh -X -p 22 forest@YOUR_QCS`. `-X` is needed to activate X forwarding and display the game on your local computer.
1. Activate the base conda environment with `conda activate`
2. Install the game with `conda install -c riverlane quantumfreeze`
5. Run `quantumfreeze`!

If you are using OSX or Windows, you will need a X server. On OSX you may want to use [XQuartz](https://www.xquartz.org/). Windows users can switch to using Windows Subsystem for Linux (WSL) or the Xming server, but support is not provided.

If you do not have a X server, `quantumfreeze` will report that is was unable to find a display. This can also be caused by omitting the `-X` flag.

## Playing the game

Your objective is the guide the penguin to his home in the igloo! The final bitstring that the circuit produces when measured gives them their instructions. A 0 will guide the penguin left, and 1 guides them down. Place gates onto the circuit in the bottom left to give your guidance.

Soon you will be challenged with multiple igloos! You will need to produce guidance with both 0 and 1 at the same time. By creating a superposition using a Hadamard gate you can get the penguin to all the igloos.

## Contributors
The Quantum Freeze was developed by Sam Coward and Tom Parks with numerous suggestions for levels from the rest of the Riverlane team!
