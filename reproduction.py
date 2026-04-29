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
    """Construct a fresh UCS2 str, verify it is intact in Python, then convert
    it to JS via inspectStr (which reads back via charCodeAt). Returns True if
    the JS-side string is all-NUL despite the Python str being intact."""
    # any codepoint > U+00FF forces 2-byte-per-char internal storage (UCS2 kind)
    s = chr(0x0100) + "x" * 1023

    # Python-side sanity check: confirm the str's data is genuinely intact
    # before we hand it to JS. If py_nul_count > 0, the corruption is not at
    # the JS boundary — investigate elsewhere.
    py_len = len(s)
    py_first = ord(s[0])
    py_nul_count = s.count("\x00")

    # JS-side view via inspectStr (reads each char via charCodeAt)
    info = js.inspectStr(s).to_py()
    triggered = info["nulCount"] == info["length"]

    tag = "*** BUG TRIGGERED ***" if triggered else "ok"
    print(
        f"  [{tag}] {label}: heap={heap_mb():.0f}MB "
        f"py_len={py_len} py_nul_count={py_nul_count} "
        f"py_first=U+{py_first:04X} "
        f"js_len={info['length']} js_nul_count={info['nulCount']} "
        f"js_first=U+{info['firstCode']:04X}"
    )
    return triggered


def main():
    # Phase 0: sanity baseline at startup, before any allocation pressure.
    # Confirms the conversion works in an unstressed Pyodide.
    print("=== Phase 0: sanity baseline ===")
    trigger_check("at startup")

    # Phase 1: large bytes ballast. Forces several memory.grow events to take
    # the WASM heap up to ~2 GB. By itself this is NOT enough to trigger the
    # bug.
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

    # Phase 2: many small varied allocations on top of the ballast.
    #
    # Note: heap_mb() does NOT change during Phase 2. No further memory.grow
    # events occur. The trigger is the allocation/fragmentation pattern itself,
    # not a memory.grow event.
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