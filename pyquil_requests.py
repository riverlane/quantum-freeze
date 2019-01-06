import threading
from queue import Queue
from pyquil.api import get_qc
from pyquil.quil import Program, address_qubits
from pyquil.gates import RESET

from bitarray import bitarray

sim=True
import subprocess as sp



class QThread(threading.Thread):

    def __init__(self, group=None, target=None, name=None,
             args=(), kwargs=None):
        threading.Thread.__init__(self, group=group, target=target, name=name)
        self.setDaemon(True)
        self.args = args
        self.kwargs = kwargs
        self.queue = Queue()
        # record sim or not here!
        self.simulator = sim
        self.qc = get_qc("9q-square-qvm")
        self.qubits = None
        # self.compprocess = sp.Popen(["quilc", "-S"], close_fds=True)
        # self.servprocess = sp.Popen(["qvm", "-S"], close_fds=True)


    def run(self):
        """Pops circuits from a work queue and runs them. Async calls the
        callback when done.
        """
        while True:
            req, callback = self.queue.get(block=True)
            try:
                nq_program = self.qc.compiler.quil_to_native_quil(self.program)
            except KeyError:
                print("pyquil was not able to compile the program.")
                print(self.program)
                raise

            binary = self.qc.compiler.native_quil_to_executable(nq_program)
            self.qc.qam.load(binary)
            self.qc.qam.run()
            self.qc.qam.wait()
            bitstrings = self.qc.qam.read_memory(region_name="ro")

            print("QVM finished, calling callback")
            # need to unwrap the list of strings to a list of lists of ints.
            states = bitstrings
            callback(states)


    def build_circuit(self, qubit_ops):
        program = Program()
        self.qubits = [program.alloc() for _ in range(len(qubit_ops))]

        program_readout_reg = program.declare("ro",
                                              memory_type="BIT",
                                              memory_size=len(self.qubits))

        for qb, gatestr in zip(self.qubits, qubit_ops):
            if gatestr=="I":
                pass
            elif gatestr=="X":
                program.gate("X", qubits=[qb], params=[])
            elif gatestr=="H":
                program.gate("H", qubits=[qb], params=[])
            elif gatestr=="K": # our one char CX label
                program.gate("CNOT", qubits=[self.qubits[self.qubits.index(qb)-1], qb], params=[])

        program.measure_all(*zip(self.qubits, program_readout_reg))
        program = address_qubits(program)
        program.wrap_in_numshots_loop(shots=10)

        self.program = program

    def execute(self, callback):
        # args={"quil_program":self.program, "trials":10}
        "enqueues a QVM request and a callback to execute once finished."
        self.queue.put((None, callback))

    def quit(self):
        self.compprocess.terminate()
        self.servprocess.terminate()
