"""One playbook executing — the walk's core and its helpers. Imports
`micro` and `spec`; `program.py` dispatches to the executors in `steps`
through the table it is handed (`surface.py` says the shape) and
`speak.py` types against their contract, so nothing here imports
`steps`, `drive` or `bench`. The map is in `physiclaw.conductor`."""
