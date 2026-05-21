import json
import math

# for changing solver values back to human-readable
SUFFIXES = {
    1e-15: "f",
    1e-12: "p",
    1e-9: "n",
    1e-6: "µ",
    1e-3: "m",
    1e3: "K",
    1e6: "M",
    1e9: "G",
    1e12: "T",
}

# for parse_value
_SUFFIXES = {
    "f": 1e-15,
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
    "µ": 1e-6,
    "m": 1e-3,
    "k": 1e3,
    "K": 1e3,
    "M": 1e6,
    "G": 1e9,
    "T": 1e12,
}


# converts string to value
def parse_value(s):
    s = str(s).strip()
    if s.lower() == "inf":  # op-amp
        return math.inf
    if not s:
        raise ValueError("empty value string")
    if s[-1] in _SUFFIXES:
        return float(s[:-1]) * _SUFFIXES[s[-1]]
    return float(s)


class NetlistBuilder:
    """
    Converts state dict into nets of connected element nodes
    """

    def __init__(self, state):
        self._comps = state["components"]
        self._conns = state["connections"]
        self.warnings = []

    def build(self):
        nets = self.get_nets()
        elements = self.get_elems(nets)
        n_nets = max(nets.values()) + 1 if nets else 0

        gnd_net = self._find_ground_net(elements, n_nets)

        return elements, n_nets, gnd_net

    def get_nets(self):
        parent = {}

        def find(key):
            while parent.get(key, key) != key:
                parent[key] = parent.get(parent.get(key, key), parent.get(key, key))
                key = parent.get(key, key)
            return key

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        # initialise every component node as its own net
        for cid, comp in self._comps.items():
            for i in range(len(comp["nodes"])):
                k = (cid, i)
                parent[k] = k

        # merge nodes connected by wires
        for conn in self._conns:
            a = (conn["from_id"], conn["from_node"])
            b = (conn["to_id"], conn["to_node"])
            if conn["from_id"] in self._comps and conn["to_id"] in self._comps:
                union(a, b)

        root_to_net = {}
        result = {}
        counter = 0
        for key in sorted(parent.keys()):
            root = find(key)
            if root not in root_to_net:
                root_to_net[root] = counter
                counter += 1
            result[key] = root_to_net[root]

        return result

    def get_elems(self, nets):
        elements = []
        for cid, comp in self._comps.items():
            name = comp["type"]
            etype = name
            if etype == "Wire Node":
                continue  # skip wire nodes
            elif etype in ("NPN BJT", "Op-Amp"):
                self.warnings.append(
                    f"{name} [{cid}] skipped"
                )
                continue

            vals = comp.get("values", {})
            node_count = len(comp["nodes"])

            try:
                if etype == "Ground":
                    n0 = nets.get((cid, 0))
                    if n0 is None:
                        continue
                    elements.append(
                        {
                            "id": cid,
                            "type": "Ground",
                            "value": 0.0,
                            "n_pos": n0,
                            "n_neg": n0,
                        }
                    )

                elif etype == "Resistor":
                    r = parse_value(vals.get("R", "1k"))
                    if r <= 0:
                        raise ValueError("resistance must be > 0")
                    n0 = nets[(cid, 0)]
                    n1 = nets[(cid, 1)]
                    elements.append(
                        {
                            "id": cid,
                            "type": "Resistor",
                            "value": r,
                            "n_pos": n0,
                            "n_neg": n1,
                        }
                    )

                elif etype == "Capacitor":
                    c = parse_value(vals.get("C", "100n"))
                    n0 = nets[(cid, 0)]
                    n1 = nets[(cid, 1)]
                    elements.append(
                        {
                            "id": cid,
                            "type": "Capacitor",
                            "value": c,
                            "n_pos": n0,
                            "n_neg": n1,
                        }
                    )

                elif etype == "Inductor":
                    l = parse_value(vals.get("L", "10m"))
                    n0 = nets[(cid, 0)]
                    n1 = nets[(cid, 1)]
                    elements.append(
                        {
                            "id": cid,
                            "type": "Inductor",
                            "value": l,
                            "n_pos": n0,
                            "n_neg": n1,
                        }
                    )
                elif etype == "Voltage Src":
                    v = parse_value(vals.get("V", "5"))
                    n_pos = nets[(cid, 0)]
                    n_neg = nets[(cid, 1)]
                    elements.append(
                        {
                            "id": cid,
                            "type": "Voltage Src",
                            "value": v,
                            "n_pos": n_pos,
                            "n_neg": n_neg,
                        }
                    )
                elif etype == "Diode":
                    vf = parse_value(vals.get("Vf", "0.7"))
                    n0 = nets[(cid, 0)]
                    n1 = nets[(cid, 1)]
                    elements.append(
                        {
                            "id": cid,
                            "type": "Diode",
                            "value": vf,
                            "n_pos": n0,
                            "n_neg": n1,
                        }
                    )
            except (KeyError, ValueError) as exc:
                self.warnings.append(f"{name} [{cid}]: {exc} - error")

        return elements

    def _find_ground_net(self, elements, n_nets):
        for el in elements:
            if el["type"] == "Ground":
                return el["n_pos"]
        return 0


class NodalSolver:

    def __init__(self, elements, n_nets, gnd_net):
        self.elements = elements
        self.n_nets = n_nets
        self.gnd_net = gnd_net

        self.vs_elems = [el for el in elements if el["type"] in ("Voltage Src", "Inductor", "Diode")]
        self.m = len(self.vs_elems)  # number of extra unknowns
        self.n = n_nets  # number of nodes

    def solve(self):
        if self.n == 0:
            raise Exception("No nets found")

        size = self.n + self.m

        # AI was used here to help implement the allocation of the matrices
        G = [[0.0] * size for _ in range(size)]  # conductance
        rhs = [0.0] * size

        vs_index = {}
        for k, element in enumerate(self.vs_elems):
            vs_index[element["id"]] = self.n + k

        for element in self.elements:
            etype = element["type"]
            p, q = element["n_pos"], element["n_neg"]

            if etype == "Resistor":
                # conductance
                g = 1.0 / element["value"]
                self._stamp_conductance(G, p, q, g)
            elif etype in ("Voltage Src", "Inductor", "Diode"):
                # voltage source/inductor/diode has to be treated differently
                v_imposed = (
                    element["value"]
                    if etype == "Voltage Src"
                    else (0.0 if etype == "Inductor" else element["value"])
                )
                vs_row = vs_index[element["id"]]
                if p < self.n:
                    G[p][vs_row] += 1.0
                    G[vs_row][p] += 1.0
                if q < self.n:
                    G[q][vs_row] -= 1.0
                    G[vs_row][q] -= 1.0
                rhs[vs_row] = v_imposed

        gnd = self.gnd_net
        # remove ground row and column
        rows_to_keep = [i for i in range(size) if i != gnd]
        G2 = [[G[r][c] for c in rows_to_keep] for r in rows_to_keep]
        rhs2 = [rhs[r] for r in rows_to_keep]

        if not G2:
            raise Exception("Everything is ground")

        # solve matrix
        solution = self._gauss(G2, rhs2)

        node_voltages = {}
        branch_currents = {}

        sol_idx = 0
        for orig_idx in rows_to_keep:
            if orig_idx < self.n:
                node_voltages[orig_idx] = solution[sol_idx]
            else:
                # find which VS element this current belongs to
                for eid, vidx in vs_index.items():
                    if vidx == orig_idx:
                        branch_currents[eid] = solution[sol_idx]
                        break
            sol_idx += 1

        node_voltages[gnd] = 0.0

        return node_voltages, branch_currents

    # used AI to understand how the nodal analysis method works and how to implement using matrices
    def _stamp_conductance(self, G, p, q, g):
        n = self.n
        if p < n:
            G[p][p] += g
        if q < n:
            G[q][q] += g
        if p < n and q < n:
            G[p][q] -= g
            G[q][p] -= g

    # use of AI to help with implementing linear algebra solving
    # could have used numpy but I was getting errors with singular matrices
    @staticmethod
    def _gauss(A, b):
        """
        Solve Ax = b via Gaussian elimination with partial pivoting.
        """
        n = len(b)
        M = [A[i][:] + [b[i]] for i in range(n)]

        for col in range(n):
            # find pivot
            max_row = max(range(col, n), key=lambda r: abs(M[r][col]))
            if abs(M[max_row][col]) < 1e-12:
                raise Exception("Singular matrix")
            M[col], M[max_row] = M[max_row], M[col]

            for row in range(col + 1, n):
                if abs(M[col][col]) < 1e-15:
                    continue
                factor = M[row][col] / M[col][col]
                for j in range(col, n + 1):
                    M[row][j] -= factor * M[col][j]

        x = [0.0] * n
        for i in range(n - 1, -1, -1):
            x[i] = M[i][n]
            for j in range(i + 1, n):
                x[i] -= M[i][j] * x[j]
            if abs(M[i][i]) < 1e-15:
                raise Exception("Singular matrix")
            x[i] /= M[i][i]

        return x


class CircuitSolver:

    def __init__(self, state):
        self._state = state

    def solve(self):
        results = {
            "node_voltages": {},
            "branch_currents": {},
            "element_currents": {},
            "warnings": [],
            "error": None,
        }

        try:
            # net list
            builder = NetlistBuilder(self._state)
            elements, n_nets, gnd_net = builder.build()
            results["warnings"].extend(builder.warnings)

            if n_nets == 0 or not elements:
                raise Exception("No solvable elements found in circuit")

            # solve
            solver = NodalSolver(elements, n_nets, gnd_net)
            node_voltages, branch_currents = solver.solve()

            results["node_voltages"] = node_voltages
            results["branch_currents"] = branch_currents

            # currents through elements
            for elem in elements:
                etype = elem["type"]
                p, q = elem["n_pos"], elem["n_neg"]
                vp = node_voltages.get(p, 0.0)
                vq = node_voltages.get(q, 0.0)

                if etype == "Resistor":
                    i = (vp - vq) / elem["value"]
                    results["element_currents"][elem["id"]] = i
                elif etype in ("Voltage Src", "Inductor", "Diode"):
                    # already in branch_currents from MNA
                    results["element_currents"][elem["id"]] = branch_currents.get(
                        elem["id"], 0.0
                    )
        except Exception as e:
            results["error"] = f"Solver error: {e}"

        return results

    def solve_and_format(self):
        # returns human readable for debugging
        results = self.solve()
        lines = []

        if results["error"]:
            lines.append(f"ERROR: {results['error']}")
            return "\n".join(lines), results
        if results["warnings"]:
            for w in results["warnings"]:
                lines.append(f"WARN: {w}")
            lines.append("")
        lines.append("Node voltages:")
        for net in sorted(results["node_voltages"]):
            v = results["node_voltages"][net]
            lines.append(f"  net {net:>3d}:  {v:>12.6f} V")

        if results["branch_currents"]:
            lines.append("\nBranch currents (V/L/D):")
            for eid, i in results["branch_currents"].items():
                lines.append(f"  [{eid}]:  {i*1e3:>12.6f} mA")

        if results["element_currents"]:
            lines.append("\nElement currents:")
            for eid, i in results["element_currents"].items():
                lines.append(f"  [{eid}]:  {i*1e3:>12.6f} mA")

        return "\n".join(lines), results