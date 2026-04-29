"""
Synthetic reproducer search for Pyodide's silent Python-str -> JS-string
conversion bug.

Bug signature: pyodide.ffi.to_js() (or implicit conversion via a JS function
call) on a Python str whose data lives at a high WASM address yields a JS
string of correct .length but every charCodeAt is 0. Source Python str is
intact.
"""

import gc
import js
import pyodide_js


def heap_mb():
    return pyodide_js._module.HEAPU8.buffer.byteLength / (1024 * 1024)


def trigger_check(label):
    """Construct a fresh UCS2 str post-allocation, convert it to JS, see if the
    JS string is all-NUL. Returns True if the bug has fired."""
    # en-dash forces UCS2; length large enough that the alloc lands somewhere
    # post-growth
    s = chr(0x0100) + "x" * 1023
    info = js.inspectStr(s).to_py()
    triggered = info['nulCount'] == info['length']
    tag = "*** BUG TRIGGERED ***" if triggered else "ok"
    print(f"  [{tag}] {label}: heap={heap_mb():.0f}MB")
    return triggered

def main():
    # Phase 1: large bytes ballast (we already know this doesn't trigger; included
    # as a baseline to confirm growth alone isn't enough)
    print("=== Phase 1: large bytes ballast ===")
    ballast = []
    while heap_mb() < 2050:
        try:
            ballast.append(bytes(100 * 1024 * 1024))
        except MemoryError:
            break
    if trigger_check("after 2.050 GB bytes ballast"):
        print(">>> Phase 1 triggered. Memory growth alone is enough.")
        return

    # Phase 2: many small varied allocations
    print("=== Phase 2: many small varied allocations ===")
    small = []
    for i in range(50000):
        small.append(bytes(1000 + (i % 4000)))
        if i and i % 5000 == 0 and trigger_check(f"small allocs i={i}"):
            print(">>> Phase 2 triggered.")
            return
    del small
    gc.collect()

if __name__ == "__main__":
    main()