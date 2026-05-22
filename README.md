<h1>Circuit Simulator</h1>

<h2>Video Demo URL</h2>
(OneDrive URL) https://1drv.ms/v/c/5a912cfc994114e9/IQDp6Yg-UpDYSID7_zTMMC2BAQKpQXpDCa5V0dI6FuK0Agc?e=FvA2Qm
<h2>Description:</h2>
<h3>Project phases</h3>
<h4>Phase 1</h4>
<p>Full UI implementation; ability to add various components, edit values, connect components using wires, etc.</p>
<p>Main GUI library: Tkinter</p>

<h4>Phase 2</h4>
<p>Implementation of solver/simulator; when run, solves for voltages and current values at all critical points (components)</p>
<h3>Overview</h3>
<p>  This project is a basic DC circuit simulation tool built in Python, using Tkinter for the graphical interface and a MNA (Modified Nodal Analysis) engine for the solver. The motivation was because I am highly interested in electrical engineering and I wanted to explore how software in the field handled complex circuits in logic.</p>
<h3>GUI (app.py)</h3>
<p>  The editor is built around a Tkinter canvas with a custom coordinate system. Rather than using Tkinter's built-in scrollregion and canvas scaling, all component positions are stored in world space, and a pair of transform functions (w2s - world to screen & s2w) convert between world and screen coordinates on every draw call. Zooming is implemented by updating a scale factor and pan offset, then calling a full redraw of the canvas from scratch. This turned out to be much more reliable than the initial approach of calling canvas.scale(), which physically moved canvas item coordinates while the Python-side state stayed unchanged, causing issues where the coordinates were stored incorrectly and the user's clicks were being registered improperly.</p>
<p>  Components are placed on a fixed grid. Each component stores its position, rotation angle, a list of node positions (ex. two pins/terminals of components like resistors and voltage sources), and a dictionary of parameter values (used for scalability; currently not needed but could be helpful for implementing ICs in the future). The node positions are what the wire routing system uses to make connections, so keeping them in sync with the component position and angle on every move or rotation was an important invariant to maintain.</p>
<p>  Rendering is very modular. There is a standalone draw function for each component type (draw_resistor, draw_capacitor, draw_voltage_src, etc, all contained within helpers.py, which also contains helper functions for rotation of points/nodes) that receives a ws funcntion which translates local offsets to actual positions, accounting for rotations and scaling. The render_component function creates ws, computes line width from the zoom level, then looks up the appropriate function in a DRAW_FN dictionary of all of the draw functions. Adding a new component only requires writing a draw function and adding two entries (one in DRAW_FN and one in the COMPONENTS catalogue), allowing for very high scalability.</p>
<p>Wire routing supports intermediates nodes which can be created simply by clicking, and clicking to end a wire on an existing wire splits it and inserts a junction node automatically. One bug that took some time to track down was a double-click issue where clicking a component node triggered both the tag-level <Button-1> binding and the canvas-level binding, effectively calling the canvas_click function twice. The fix was to simply comment out the wire section in comp_click, which prevented wires from being treated like components.</p>
<p>Rotation is handled in 90-degree steps. The R key rotates a selected component clockwise and E rotates it counterclockwise. The rotate_point function uses round(cos) and round(sin) on the angle to keep coordinates exact for 90-degree steps. This is apparently the typical way to do it in popular schematic software.</p>
<p>Component values are editable through a double-click dialog. Each entry in the component catalogue defines a params list of (label, default, unit) tuples, and the dialog generates an entry field for each one. Values are stored as strings in the component dict and parsed at simulation time, which keeps the solver separate and therefore makes the software more efficient</p>
<h3>Solver (solver.py)</h3>
<p>  The solver uses Modified Nodal Analysis (MNA, which I researched with the help of AI). Specifically, my implementation modifies standard nodal analysis to integrate voltage sources. The full implementation (in solver.py) is split into three classes. NetlistBuilder takes the JSON state from the editor and resolves connectivity using union-find, producing a flat element list where each element has a type, value, and two net indices. NodalSolver creates the full matrix and solves for the currents at each node. CircuitSolver chains the two and derives element currents from the solution, outputting the result in two manners - human readable and a separate dict for the GUI logic.</p>
<p>The MNA matrix has size n_nets + m where m is the number of voltage-source-like elements — voltage sources, inductors, and diodes. Resistors are stamped as conductances into the G portion of the matrix. Voltage sources extend the matrix with an additional current unknown and are stamped into separate blocks. Capacitors are not stamped as they do not affect DC circuits (after initial charging).</p>
<p>The ground node row and column are deleted before solving, which reduces the matrix to a square system. Solving is done with Gaussian elimination with partial pivoting, implemented (with help of AI). Singular matrix detection was important here as a floating net or a loop of voltage sources both produce a singular matrix which was hard to debug for a while.</p>
<h3>Other</h3>
<p>constants.py - Contains some color and component constants/defaults, as well as suffix conversion arrays.</p>

<h3>Possible ways to continue expanding</h3>
<p>Add simulation of capacitor charging/discharging; inductors; op-amps; transistors</p>
<p>Expand project to include digital logic simulation</p>
<p>New tab for digital logic circuits - all logic gates and the ability to turn logic circuits into actual circuits (using transistors)</p>
<p>Simulation of basic ICs in circuit editor tab - Arduino programming, shift registers, displays, motor control, LDOs, etc</p>
