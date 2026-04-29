# Pyodide String Corruption Bug Reproduction
This repo contains code that reproduces a bug in pyodide v0.29.3 that causes Python strings copied to JavaScript to get corrupted when the WebAssembly heap size is very high (>2GB) and the string is allocated in a high memory location.

## How to Use
You can use the nix flake to get a devshell with the necessary runtime dependencies if you need (`nix develop`, or activate the `direnv` `.envrc`), or install NodeJS yourself.

Then you can simply:

```
npm install
npm start
```

You'll see this output (or similar):

```
=== Phase 0: sanity baseline ===
  [ok] at startup: heap=20MB py_len=1024 py_nul_count=0 py_first=U+0100 js_len=1024 js_nul_count=0 js_first=U+0100
=== Phase 1: large bytes ballast ===
  [ok] after 2.050 GB bytes ballast: heap=2114MB py_len=1024 py_nul_count=0 py_first=U+0100 js_len=1024 js_nul_count=0 js_first=U+0100
=== Phase 2: many small varied allocations ===
  [ok] small allocs i=5000: heap=2114MB py_len=1024 py_nul_count=0 py_first=U+0100 js_len=1024 js_nul_count=0 js_first=U+0100
  [ok] small allocs i=10000: heap=2114MB py_len=1024 py_nul_count=0 py_first=U+0100 js_len=1024 js_nul_count=0 js_first=U+0100
  [*** BUG TRIGGERED ***] small allocs i=15000: heap=2114MB py_len=1024 py_nul_count=0 py_first=U+0100 js_len=1024 js_nul_count=1024 js_first=U+0000
>>> Phase 2 triggered.
```

What this is demonstrating is that once the string is transferred to JavaScript, all its characters become null.