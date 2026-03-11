# Contributing

High-signal contributions improve the physiological protocol itself, not only the metaphor.

Good contribution targets:

- stronger signal channels and organ interactions
- richer cell adapters
- recovery pool and rehabilitation flows
- better workflow demos
- clearer protocol docs

Before opening a pull request:

```powershell
pip install -e .
python -m unittest discover -s .\tests -v
python .\examples\research_assistant_demo.py
```

Pull requests should explain:

- what protocol behavior changed
- why the change improves the organism model
- what tests prove it
